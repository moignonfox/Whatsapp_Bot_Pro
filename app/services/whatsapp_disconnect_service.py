import requests
import logging
from app.services.crypto_service import decrypt_token

logger = logging.getLogger(__name__)

def disconnect_whatsapp_number(token_wa_encrypted: str, phone_number_id: str) -> bool:
    """
    Désabonne le numéro WhatsApp Business du webhook Vira.
    Le numéro est immédiatement disponible pour être reconnecté ailleurs.
    """
    if not token_wa_encrypted or not phone_number_id:
        logger.warning("[WhatsApp Disconnect] token_wa_encrypted ou phone_number_id manquant.")
        return False
        
    try:
        token_wa = decrypt_token(token_wa_encrypted)
        # 1. Se désabonner du webhook
        url_unsub = f"https://graph.facebook.com/v18.0/{phone_number_id}/subscribed_apps"
        response_unsub = requests.delete(
            url_unsub,
            headers={"Authorization": f"Bearer {token_wa}"}
        )
        
        # 2. Dérégistrer complètement le numéro (le libère de l'API Cloud pour qu'il puisse être utilisé sur un téléphone)
        url_deregister = f"https://graph.facebook.com/v18.0/{phone_number_id}/deregister"
        response_deregister = requests.post(
            url_deregister,
            headers={"Authorization": f"Bearer {token_wa}"}
        )
        
        if response_unsub.status_code == 200 or response_deregister.status_code == 200:
            logger.info(f"[WhatsApp Disconnect] Succès pour le numéro {phone_number_id}")
            return True
        else:
            logger.error(f"[WhatsApp Disconnect] Échec pour {phone_number_id}: {response_unsub.text} | {response_deregister.text}")
            return False
            
    except Exception as e:
        logger.error(f"[WhatsApp Disconnect] Exception lors de la déconnexion: {e}")
        return False
