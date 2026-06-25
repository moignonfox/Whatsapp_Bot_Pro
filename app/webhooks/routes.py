"""Routes Webhook — Point d'entree des messages WhatsApp."""
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
    """Verifie la signature HMAC-SHA256 de Meta (M-4).
    
    Retourne True si la signature est valide, ou si META_APP_SECRET n'est pas configure.
    Retourne False si la signature est invalide.
    """
    app_secret = current_app.config.get('META_APP_SECRET', '')
    if not app_secret:
        logger.warning("META_APP_SECRET non configure — verification HMAC desactivee.")
        return True  # Non bloquant si non configure (backward compat)

    signature_header = req.headers.get('X-Hub-Signature-256', '')
    if not signature_header.startswith('sha256='):
        return False

    expected = hmac.new(
        app_secret.encode(),
        req.data,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(f"sha256={expected}", signature_header)


@webhooks_bp.route('/webhook', methods=['GET'])
def verify():
    """Verification du webhook par Meta."""
    if request.args.get("hub.verify_token") == current_app.config['VERIFY_TOKEN']:
        return request.args.get("hub.challenge"), 200
    return "Erreur", 403


@webhooks_bp.route('/webhook', methods=['POST'])
def handle_messages():
    """Reception et traitement des messages entrants."""
    # M-4 : Vérification de la signature Meta
    if not _verify_meta_signature(request):
        logger.warning("Signature Meta invalide — requête rejetée.")
        return make_response("Signature invalide", 403)

    data = request.get_json()

    try:
        value = data.get('entry', [{}])[0].get('changes', [{}])[0].get('value', {})

        if 'messages' in value:
            message_info = value['messages'][0]

            if message_info.get('type') == 'text':
                phone_id = value['metadata']['phone_number_id']
                wa_id = message_info['from']
                user_text = message_info['text']['body']

                business = business_repo.get_by_phone_id(phone_id)

                if business:
                    if not dict(business).get('is_active', 1):
                        return make_response("Business inactif", 200)

                    biz_id = business['id']

                    # Diffusion du message client au Dashboard en temps reel
                    try:
                        from app import socketio
                        socketio.emit('nouveau_message', {
                            'business_id': biz_id,
                            'wa_id': wa_id,
                            'content': user_text,
                            'role': 'user',
                            'timestamp': 'now'
                        }, room=biz_id)
                    except Exception as ws_err:
                        logger.warning("Erreur SocketIO emit: %s", ws_err)

                    # Traitement asynchrone (IA + envoi reponse)
                    threading.Thread(
                        target=bot_core.enqueue_message,
                        args=(wa_id, user_text, business, phone_id)
                    ).start()
                else:
                    logger.warning("Business inconnu pour phone_id: %s", phone_id)

    except Exception as e:
        logger.error("Erreur Webhook reception: %s", e)

    return make_response("OK", 200)
