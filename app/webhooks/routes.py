"""Routes Webhook — Point d'entrée des messages WhatsApp et anti-rejeu."""
import hmac
import hashlib
import logging
import threading
import uuid
from flask import Blueprint, request, make_response, current_app
from app.repositories import business_repo, conversation_repo
from app.services import bot_core

webhooks_bp = Blueprint('webhooks', __name__)
logger = logging.getLogger(__name__)


def _verify_meta_signature(req) -> bool:
    """Vérifie la signature HMAC-SHA256 de Meta.

    Retourne True si la signature est valide.
    BLOQUANT si META_APP_SECRET n'est pas configuré en production.
    """
    app_secret = current_app.config.get('META_APP_SECRET', '')
    if not app_secret:
        # En développement (DEBUG=True) on avertit sans bloquer
        # En production (DEBUG=False) on bloque impérativement
        if current_app.debug:
            logger.warning(
                "META_APP_SECRET non configuré — vérification HMAC désactivée (mode dev uniquement)."
            )
            return True
        else:
            logger.error(
                "META_APP_SECRET manquant en production — requête webhook rejetée."
            )
            return False

    signature_header = req.headers.get('X-Hub-Signature-256', '')
    if not signature_header.startswith('sha256='):
        return False

    expected = hmac.new(
        app_secret.encode(),
        req.data,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(f"sha256={expected}", signature_header)


def _is_already_seen(wam_id: str) -> bool:
    """Retourne True si ce wam_id a déjà été traité dans les 24 dernières heures (anti-rejeu)."""
    import sqlite3
    from app.models.schema import get_db_path
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        # Chercher dans la fenêtre de 24h
        cursor.execute(
            "SELECT 1 FROM webhook_seen_ids WHERE wam_id = ? AND seen_at > datetime('now', '-24 hours')",
            (wam_id,)
        )
        found = cursor.fetchone() is not None
        if not found:
            # Enregistrer pour les prochaines 24h
            cursor.execute(
                "INSERT OR IGNORE INTO webhook_seen_ids (wam_id) VALUES (?)",
                (wam_id,)
            )
            conn.commit()
        conn.close()
        return found
    except Exception as e:
        logger.error("Erreur anti-rejeu webhook: %s", e)
        return False


@webhooks_bp.route('/webhook', methods=['GET'])
def verify():
    """Vérification du webhook par Meta."""
    if request.args.get("hub.verify_token") == current_app.config['VERIFY_TOKEN']:
        return request.args.get("hub.challenge"), 200
    return "Erreur", 403


@webhooks_bp.route('/webhook', methods=['POST'])
def handle_messages():
    """Réception et traitement des messages entrants."""
    # Vérification de la signature HMAC Meta
    if not _verify_meta_signature(request):
        logger.warning("Signature Meta invalide ou absente — requête rejetée.")
        return make_response("Signature invalide", 403)

    data = request.get_json()

    try:
        value = data.get('entry', [{}])[0].get('changes', [{}])[0].get('value', {})

        if 'messages' in value:
            message_info = value['messages'][0]

            # Protection anti-rejeu : vérifier le wam_id unique du message
            wam_id = message_info.get('id', '')
            if wam_id and _is_already_seen(wam_id):
                logger.info("Message dupliqué ignoré (anti-rejeu): %s", wam_id)
                return make_response("OK", 200)

            if message_info.get('type') in ['text', 'image', 'audio']:
                phone_id = value['metadata']['phone_number_id']
                wa_id = message_info['from']
                
                msg_type = message_info['type']
                user_text = ""
                media_url_local = None
                
                business = business_repo.get_by_phone_id(phone_id)
                if business:
                    if not dict(business).get('is_active', 1):
                        return make_response("Business inactif", 200)

                    biz_id = business['id']
                    token = business.get('token_wa')
                    
                    if msg_type == 'text':
                        user_text = message_info['text']['body']
                    elif msg_type in ['image', 'audio']:
                        media_id = message_info[msg_type]['id']
                        user_text = "📸 Image reçue" if msg_type == 'image' else "🎤 Message vocal reçu"
                        
                        # Si le message image contient une légende (caption)
                        if msg_type == 'image' and 'caption' in message_info['image']:
                            user_text = message_info['image']['caption']
                            
                        # Télécharger le média
                        from app.services.whatsapp_service import download_media, send_message
                        content, mime_type = download_media(media_id, phone_id, token)
                        if content:
                            import os, uuid
                            ext = '.jpg' if msg_type == 'image' else '.m4a'
                            if mime_type == 'image/png': ext = '.png'
                            elif mime_type == 'audio/ogg': ext = '.ogg'
                            
                            filename = f"client_{uuid.uuid4()}{ext}"
                            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'client_media')
                            os.makedirs(upload_dir, exist_ok=True)
                            file_path = os.path.join(upload_dir, filename)
                            
                            with open(file_path, 'wb') as f:
                                f.write(content)
                                
                            media_url_local = f"/static/uploads/client_media/{filename}"
                            
                            # Si c'est un audio, on le transcrit en arrière-plan et on envoie l'accusé de réception
                            if msg_type == 'audio':
                                # UX: Accusé de réception immédiat
                                send_message(wa_id, "🎤 J'écoute votre message vocal...", phone_id, token)
                                
                                # Transcription Groq
                                from app.services.ai_service import transcribe_audio
                                user_text = transcribe_audio(content)

                    # Si c'est une image, on sauvegarde manuellement car bot_core.enqueue_message ne gère pas nativement les images
                    # Si c'est un audio, on sauvegarde aussi l'entrée avec l'URL, MAIS on appelle enqueue_message pour générer une réponse
                    if msg_type in ['image', 'audio']:
                        msg_id = conversation_repo.save_message(
                            wa_id=wa_id, role='user', content=user_text, business_id=biz_id,
                            message_type=msg_type, media_url=media_url_local
                        )
                        # Récupérer le nom du client pour affichage immédiat dans la liste
                        try:
                            from app.repositories import client_repo
                            _client = client_repo.get_or_create(biz_id, wa_id)
                            _client_name = dict(_client).get('display_name') or dict(_client).get('nom') or wa_id
                        except Exception:
                            _client_name = wa_id
                        # Diffusion SocketIO pour le Dashboard/Mobile
                        try:
                            from app import socketio
                            socketio.emit('nouveau_message', {
                                'event_id': str(uuid.uuid4()),
                                'business_id': biz_id,
                                'wa_id': wa_id,
                                'client_name': _client_name,
                                'message_id': msg_id,
                                'content': user_text,
                                'role': 'user',
                                'timestamp': __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'message_type': msg_type,
                                'media_url': media_url_local
                            }, room=biz_id)
                        except Exception as e:
                            logger.error(f"Erreur SocketIO broadcast client media: {e}")
                        
                        # Si c'est un audio, on envoie le texte transcrit à l'IA pour traitement
                        if msg_type == 'audio':
                            from app import socketio as _sio
                            _sio.start_background_task(
                                bot_core.enqueue_message,
                                wa_id, user_text, business, phone_id, False
                            )
                            
                    else:
                        # Récupérer le nom du client pour affichage immédiat dans la liste
                        try:
                            from app.repositories import client_repo
                            _client = client_repo.get_or_create(biz_id, wa_id)
                            _client_name = dict(_client).get('display_name') or dict(_client).get('nom') or wa_id
                        except Exception:
                            _client_name = wa_id
                        # Diffusion du message client au Dashboard en temps réel (texte)
                        try:
                            from app import socketio
                            socketio.emit('nouveau_message', {
                                'event_id': str(uuid.uuid4()),
                                'business_id': biz_id,
                                'wa_id': wa_id,
                                'client_name': _client_name,
                                'content': user_text,
                                'role': 'user',
                                'timestamp': __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            }, room=biz_id)
                        except Exception as e:
                            pass
                        
                        # Traitement asynchrone (IA + envoi réponse) pour le texte
                        from app import socketio as _sio
                        _sio.start_background_task(
                            bot_core.enqueue_message,
                            wa_id, user_text, business, phone_id
                        )
                    
                    # Notification push Firebase — avec lien direct vers la conversation
                    try:
                        from app.services.notification_service import send_push_notification
                        from flask import request as _req
                        # Construire l'URL directe vers la conversation (ex: /admin/BIZID/chat?wa_id=WAID)
                        chat_url = f"/admin/{biz_id}/chat?wa_id={wa_id}"
                        send_push_notification(
                            business_id=biz_id,
                            title="Nouveau message WhatsApp",
                            body=user_text,
                            data={
                                "wa_id": wa_id,
                                "type": "nouveau_message",
                                "click_action": chat_url
                            }
                        )
                    except Exception as e:
                        logger.warning("Erreur Firebase emit: %s", e)


                else:
                    logger.warning("Business inconnu pour phone_id: %s", phone_id)

        elif 'statuses' in value:
            for status_item in value['statuses']:
                wam_id = status_item.get('id')
                msg_status = status_item.get('status')
                recipient_id = status_item.get('recipient_id')
                phone_id = value.get('metadata', {}).get('phone_number_id')
                
                if wam_id and msg_status:
                    updated = conversation_repo.update_message_status(wam_id, msg_status)
                    if updated and phone_id:
                        business = business_repo.get_by_phone_id(phone_id)
                        if business:
                            try:
                                from app import socketio
                                socketio.emit('statut_message', {
                                    'business_id': business['id'],
                                    'wa_id': recipient_id,
                                    'status': msg_status,
                                    'meta_message_id': wam_id
                                }, room=business['id'])
                            except Exception as e:
                                logger.error("Erreur SocketIO status update: %s", e)

    except Exception as e:
        logger.error("Erreur Webhook réception: %s", e)

    return make_response("OK", 200)
