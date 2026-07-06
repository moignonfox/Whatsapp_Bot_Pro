import time
import random
import logging
from app.repositories import marketing_repo, business_repo, conversation_repo
from app.services import whatsapp_service

logger = logging.getLogger(__name__)

def process_campaign_queue():
    """
    Fonction appelée par le scheduler (ex: toutes les 10 secondes).
    Dépile UN SEUL message, l'envoie, et met à jour son statut.
    """
    msg = marketing_repo.get_next_pending_message()
    if not msg:
        return  # Rien à faire

    # On a un message à envoyer
    msg_id = msg['id']
    biz_id = msg['business_id']
    wa_id = msg['wa_id']
    content = msg['message']

    business = business_repo.get_by_id(biz_id)
    if not business:
        marketing_repo.mark_message_status(msg_id, 'failed')
        return

    phone_id = business['whatsapp_phone_id']
    token = business['token_wa']
    plan = dict(business).get('plan_abonnement', 'BASIC')

    try:
        whatsapp_service.send_text_message(
            to_number=wa_id,
            message_text=content,
            phone_number_id=phone_id,
            access_token=token
        )
        marketing_repo.mark_message_status(msg_id, 'sent')
        
        # Log dans l'historique
        conversation_repo.save_message(wa_id, "assistant", f"[CAMPAGNE MARKETING]\n{content}", biz_id)
        
        logger.info(f"Campagne: Message envoyé à {wa_id} (Biz {biz_id})")

    except Exception as e:
        logger.error(f"Campagne: Erreur envoi à {wa_id} : {e}")
        marketing_repo.mark_message_status(msg_id, 'failed')

    # Anti-Spam Delay additionnel bloquant UNIQUEMENT ce thread du scheduler,
    # pour s'assurer qu'un autre job ne s'exécute pas immédiatement.
    # Ce délai de 8 à 25 secondes simule un comportement humain et est OBLIGATOIRE
    # pour TOUS les plans afin d'éviter le bannissement par Meta.
    time.sleep(random.randint(8, 25))
