"""Service d'envoi de messages WhatsApp via l'API Meta Graph."""
import logging
import requests

logger = logging.getLogger(__name__)


def send_message(to, text, phone_id, token):
    """Envoie un message texte WhatsApp via l'API Meta (v21.0)."""
    url = f"https://graph.facebook.com/v21.0/{phone_id}/messages"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code not in (200, 201):
            logger.error("Erreur API WhatsApp (%s) : %s", response.status_code, response.text)
        return response.status_code
    except requests.exceptions.RequestException as e:
        safe_number = f"****{to[-4:]}" if len(to) >= 4 else "****"
        logger.error("❌ Exception API WhatsApp lors de l'envoi à %s: %s", safe_number, type(e).__name__)
        return 500

def send_text_message(to_number, message_text, phone_number_id, access_token):
    """
    Envoie un message texte simple via l'API Cloud de WhatsApp.
    Adapté pour le multi-sociétés (utilise le token et l'ID spécifiques du business).
    """
    url = f"https://graph.facebook.com/v21.0/{phone_number_id}/messages"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_number,
        "type": "text",
        "text": {
            "body": message_text
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        # M-3 : on masque le numéro (4 derniers chiffres) et on ne loggue pas le corps de la réponse
        safe_number = f"****{to_number[-4:]}" if len(to_number) >= 4 else "****"
        logger.error("❌ Erreur API Meta lors de l'envoi à %s: %s", safe_number, type(e).__name__)
        return None
