"""Routes Webhook — Point d'entrée des messages WhatsApp et anti-rejeu."""
import hmac
import hashlib
import logging
import threading
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

            if message_info.get('type') == 'text':
                phone_id = value['metadata']['phone_number_id']
                wa_id = message_info['from']
                user_text = message_info['text']['body']

                business = business_repo.get_by_phone_id(phone_id)

                if business:
                    if not dict(business).get('is_active', 1):
                        return make_response("Business inactif", 200)

                    biz_id = business['id']

                    # Diffusion du message client au Dashboard en temps réel
                    try:
                        from app import socketio
                        from app.services.notification_service import send_push_notification

                        logger.info("Tentative d'émission SocketIO nouveau_message pour room=%s", biz_id)
                        socketio.emit('nouveau_message', {
                            'business_id': biz_id,
                            'wa_id': wa_id,
                            'content': user_text,
                            'role': 'user',
                            'timestamp': 'now'
                        }, room=biz_id)
                        logger.info("SocketIO emit réussi !")

                        # Notification push Firebase
                        logger.info("Tentative d'envoi de notification Firebase pour business_id=%s", biz_id)
                        success_push = send_push_notification(
                            business_id=biz_id,
                            title="Nouveau message WhatsApp",
                            body=user_text,
                            data={
                                "wa_id": wa_id,
                                "type": "nouveau_message"
                            }
                        )
                        logger.info("Firebase push envoyé : %s", success_push)
                    except Exception as ws_err:
                        logger.warning("Erreur SocketIO/Firebase emit: %s", ws_err, exc_info=True)

                    # Traitement asynchrone (IA + envoi réponse)
                    threading.Thread(
                        target=bot_core.enqueue_message,
                        args=(wa_id, user_text, business, phone_id)
                    ).start()
                else:
                    logger.warning("Business inconnu pour phone_id: %s", phone_id)

    except Exception as e:
        logger.error("Erreur Webhook réception: %s", e)

    return make_response("OK", 200)
