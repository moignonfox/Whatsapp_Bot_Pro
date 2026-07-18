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

def upload_media(file_path, mime_type, phone_number_id, access_token):
    """
    Upload un fichier sur l'API Meta /media et retourne le media_id.
    """
    url = f"https://graph.facebook.com/v21.0/{phone_number_id}/media"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        with open(file_path, 'rb') as f:
            files = {
                'file': (file_path, f, mime_type)
            }
            data = {
                'messaging_product': 'whatsapp'
            }
            response = requests.post(url, headers=headers, files=files, data=data, timeout=30)
            response.raise_for_status()
            res_json = response.json()
            return res_json.get('id')
    except requests.exceptions.RequestException as e:
        logger.error("❌ Erreur upload_media Meta : %s", e)
        return None

def send_media_message(to_number, media_id, media_type, phone_number_id, access_token):
    """
    Envoie un message média (image, audio, document) via l'API Cloud de WhatsApp.
    media_type: 'image', 'audio', 'document', 'video'
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
        "type": media_type,
        media_type: {
            "id": media_id
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        safe_number = f"****{to_number[-4:]}" if len(to_number) >= 4 else "****"
        logger.error("❌ Erreur API Meta media lors de l'envoi à %s: %s (response: %s)", safe_number, type(e).__name__, response.text if 'response' in locals() else '')
        return None

def download_media(media_id, phone_number_id, access_token):
    """
    Télécharge un média depuis WhatsApp en 2 étapes:
    1. Récupérer l'URL du média
    2. Télécharger le binaire depuis l'URL
    Retourne (binary_content, mime_type) ou (None, None)
    """
    url_info = f"https://graph.facebook.com/v21.0/{media_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        # 1. Obtenir l'URL
        resp_info = requests.get(url_info, headers=headers, timeout=10)
        resp_info.raise_for_status()
        info = resp_info.json()
        media_url = info.get('url')
        mime_type = info.get('mime_type')
        
        if not media_url:
            return None, None
            
        # 2. Télécharger le fichier
        resp_file = requests.get(media_url, headers=headers, timeout=30)
        resp_file.raise_for_status()
        return resp_file.content, mime_type
        
    except requests.exceptions.RequestException as e:
        logger.error("❌ Erreur download_media Meta : %s", e)
        return None, None

def send_template_message(to_number, template_name, variables, phone_number_id, access_token, language_code="fr", header_image_link=None):
    """
    Envoie un message modèle (template) approuvé via l'API Cloud de WhatsApp.
    variables est une liste de strings qui viendront remplacer {{1}}, {{2}}...
    """
    url = f"https://graph.facebook.com/v21.0/{phone_number_id}/messages"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    parameters = [{"type": "text", "text": str(var)} for var in variables]
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_number,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {
                "code": language_code
            }
        }
    }
    
    components = []
    if header_image_link:
        components.append({
            "type": "header",
            "parameters": [
                {
                    "type": "image",
                    "image": {"link": header_image_link}
                }
            ]
        })
        
    if parameters:
        components.append({
            "type": "body",
            "parameters": parameters
        })
        
    if components:
        payload["template"]["components"] = components
        
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        safe_number = f"****{to_number[-4:]}" if len(to_number) >= 4 else "****"
        error_msg = response.text if 'response' in locals() and response else str(e)
        logger.error("❌ Erreur API Meta (Template %s) à %s: %s", template_name, safe_number, error_msg)
        return None
