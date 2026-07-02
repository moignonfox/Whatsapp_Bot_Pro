import logging
from app.repositories import order_repo
from app.services.whatsapp_service import send_text_message

def check_and_send_reminders():
    """Vérifie et envoie les rappels WhatsApp pour les réservations imminentes."""
    try:
        reminders = order_repo.get_upcoming_reminders()
        if not reminders:
            return

        for r in reminders:
            res_id = r['id']
            client_wa_id = r['wa_id']
            details = r['details']
            date_heure = r['date_heure_debut']
            wa_phone_id = r['whatsapp_phone_id']
            token_wa = r['token_wa']
            manager_phone = r['manager_phone']

            # 1. Message pour le client
            client_msg = (
                f"📅 *Rappel de Commande / Réservation*\n\n"
                f"Bonjour ! Ceci est un rappel automatique concernant :\n"
                f"🛠️ {details}\n"
                f"🕒 Prévu pour : {date_heure}\n\n"
                f"À très vite !"
            )
            # Envoi au client
            if wa_phone_id and token_wa:
                send_text_message(client_wa_id, client_msg, wa_phone_id, token_wa)

            # 2. Message pour le gérant
            if manager_phone:
                manager_msg = (
                    f"⚠️ *Rappel Commande / Prestation imminente*\n\n"
                    f"Client : {client_wa_id}\n"
                    f"Détails : {details}\n"
                    f"Heure prévue : {date_heure}"
                )
                clean_phone = manager_phone.replace('+', '').replace(' ', '')
                # Si l'API attend un format particulier, send_text_message prend juste le numero
                send_text_message(clean_phone, manager_msg, wa_phone_id, token_wa)

            # 3. Marquer le rappel comme envoyé
            order_repo.mark_reminder_sent(res_id)
            logging.info(f"Rappel envoyé pour la réservation {res_id} (Client: {client_wa_id})")

    except Exception as e:
        logging.error(f"Erreur dans le worker de rappel : {e}")
