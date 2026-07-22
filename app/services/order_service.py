"""Service Commandes — Extraction et sauvegarde des réservations."""
import logging
import uuid
from app.repositories import order_repo, tag_repo

logger = logging.getLogger(__name__)


def extract_and_save_reservation(reply, wa_id, business_id):
    """Cherche un tag [RESERVATION: ...] dans la réponse IA, sauvegarde la commande.

    Format: [RESERVATION: détails | MONTANT: chiffre | PRIORITE: Normale/Haute]
    Retourne la réponse nettoyée (sans le tag).
    """
    if "[RESERVATION:" not in reply:
        return reply

    try:
        import re
        
        # Regex stricte : on s'attend exactement aux 6 champs dans l'ordre (tolérance sur les espaces et sauts de ligne)
        pattern = r'\[RESERVATION:\s*(.*?)\s*\|\s*DATE:\s*(.*?)\s*\|\s*EMPLOYEE_ID:\s*(.*?)\s*\|\s*MONTANT:\s*(.*?)\s*\|\s*PRIORITE:\s*(.*?)\s*\|\s*TAGS:\s*(.*?)\]'
        match = re.search(pattern, reply, re.DOTALL | re.IGNORECASE)
        
        if not match:
            logger.warning(f"[ORDER] Le tag [RESERVATION] a été détecté mais la syntaxe est invalide. Fallback humain activé. Reply content: {reply}")
            # Fallback humain : créer une commande "Erreur IA" pour alerter le restaurateur
            details_secours = "⚠️ ÉCHEC PARSING IA - Vérifiez manuellement la demande du client."
            order_repo.save_reservation(business_id, wa_id, details_secours, priorite="Haute")
            import uuid
            try:
                from app import socketio
                socketio.emit('nouvelle_commande', {
                    'event_id': str(uuid.uuid4()),
                    'business_id': business_id,
                    'wa_id': wa_id,
                    'details': details_secours,
                    'statut': 'En attente',
                    'priorite': 'Haute',
                    'timestamp': 'now'
                }, room=business_id)
            except Exception:
                pass
            return re.sub(r'\[RESERVATION:.*?\]', '', reply, flags=re.DOTALL | re.IGNORECASE).strip()
            
        details_extract = match.group(1).strip()
        raw_date = match.group(2).strip()
        date_extract = None if raw_date.lower() == "none" or raw_date == "" else raw_date
        
        raw_emp = match.group(3).strip()
        emp_id_extract = None
        try:
            emp_id_extract = int(raw_emp) if raw_emp.lower() != "none" and raw_emp != "" else None
        except:
            pass
            
        raw_price = match.group(4).strip()
        montant_extract = int(''.join(filter(str.isdigit, raw_price)) or 0)
        
        prio_extract = match.group(5).strip()
        tags_extract = match.group(6).strip()

        # Anti-doublon strict : on bloque la création si le client a DÉJÀ une commande en attente
        # MAIS on met à jour la commande existante si elle est toujours en attente (ex: ajout d'heure).
        last_res = order_repo.get_last_for_user(wa_id, business_id)
        if last_res and last_res['statut'] == 'En attente':
            logger.debug("[ORDER] Mise à jour de la commande En attente pour %s.", wa_id)
            order_repo.update_reservation(last_res['id'], details_extract, prio_extract, montant_extract, date_extract, emp_id_extract)
            new_res_id = last_res['id']
            # On supprime les anciens tags de cette commande pour les remplacer par les nouveaux ? 
            # Simplification : on laisse les tags actuels, la DB gérera.
        else:
            new_res_id = order_repo.save_reservation(business_id, wa_id, details_extract, prio_extract, montant_extract, date_extract, emp_id_extract)
            logger.info("[ORDER] Nouvelle réservation créée pour %s — %s", wa_id, details_extract[:60])
            
        # Gérer les tags (pour les nouvelles comme pour les mises à jour)
        if tags_extract:
            # Gérer les tags
            extracted_tags = [t.strip() for t in tags_extract.split(',') if t.strip() and t.strip().lower() != 'aucun']
            
            # 1. Hériter des tags client existants
            client_tags = tag_repo.get_tags_for_client(wa_id, business_id)
            for ct in client_tags:
                tag_repo.add_tag_to_order(new_res_id, ct['id'])
                
            # 2. Appliquer les nouveaux tags extraits
            for tag_name in extracted_tags:
                tag = tag_repo.get_tag_by_name(business_id, tag_name)
                if tag:
                    if tag['type'] == 'Client':
                        # Lier au client
                        tag_repo.add_tag_to_client(wa_id, business_id, tag['id'])
                    # Toujours lier à la commande (même si c'est un tag client, il s'applique à cette commande)
                    tag_repo.add_tag_to_order(new_res_id, tag['id'])


            # Émettre la notification en temps réel vers le dashboard
            try:
                from app import socketio
                from app.services.notification_service import send_push_notification
                
                socketio.emit('nouvelle_commande', {
                    'event_id': str(uuid.uuid4()),
                    'business_id': business_id,
                    'wa_id': wa_id,
                    'details': details_extract,
                    'montant': montant_extract,
                    'priorite': prio_extract,
                    'statut': 'En attente',
                    'res_id': new_res_id,
                }, room=business_id)
                
                # Envoyer une notification push Firebase
                send_push_notification(
                    business_id=business_id,
                    title="Nouvelle Commande 🔔",
                    body=f"Montant: {montant_extract} F\nDétails: {details_extract}",
                    data={
                        "res_id": new_res_id,
                        "type": "nouvelle_commande"
                    }
                )
            except Exception as ws_err:
                logger.debug("[ORDER] Erreur Socket.IO/Firebase: %s", ws_err)

            # Émettre une notification WhatsApp au gérant
            try:
                from app.repositories import business_repo
                from app.services import whatsapp_service
                
                business = business_repo.get_by_id(business_id)
                if business:
                    owner_phone = dict(business).get('owner_phone', '').strip()
                    if owner_phone:
                        owner_phone_clean = owner_phone.replace('+', '').replace(' ', '').replace('-', '')
                        if len(owner_phone_clean) == 8 and owner_phone_clean.isdigit():
                            owner_phone_clean = '228' + owner_phone_clean
                        
                        alert_msg = (
                            f"🔔 *NOUVELLE COMMANDE REÇUE* 🔔\n\n"
                            f"Client : +{wa_id}\n"
                            f"Montant : {montant_extract} F\n"
                            f"Détails :\n{details_extract}\n\n"
                            f"👉 Consultez le Dashboard pour valider !"
                        )
                        whatsapp_service.send_message(
                            owner_phone_clean, 
                            alert_msg, 
                            dict(business).get('phone_id', ''), 
                            dict(business).get('token_wa', '')
                        )
                        logger.info(f"[ORDER] Notification WhatsApp envoyée au gérant {owner_phone_clean}")
            except Exception as notif_err:
                logger.error("[ORDER] Erreur envoi notification WhatsApp au gérant: %s", notif_err)

        # Enlever le tag de la réponse même s'il y a une erreur dans le try
    except Exception as e:
        logger.error("[ORDER] Erreur extraction/sauvegarde: %s", e)

    import re
    reply = re.sub(r'\[RESERVATION:.*?\]', '', reply, flags=re.DOTALL | re.IGNORECASE).strip()
    return reply
