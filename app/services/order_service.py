"""Service Commandes — Extraction et sauvegarde des réservations."""
import logging
from app.repositories import order_repo

logger = logging.getLogger(__name__)


def extract_and_save_reservation(reply, wa_id, business_id):
    """Cherche un tag [RESERVATION: ...] dans la réponse IA, sauvegarde la commande.

    Format: [RESERVATION: détails | MONTANT: chiffre | PRIORITE: Normale/Haute]
    Retourne la réponse nettoyée (sans le tag).
    """
    if "[RESERVATION:" not in reply:
        return reply

    try:
        start = reply.find("[RESERVATION:") + len("[RESERVATION:")
        end = reply.find("]", start)
        content = reply[start:end]

        parts = content.split("|")
        details_extract = parts[0].strip()
        montant_extract = 0
        prio_extract = "Normale"

        for p in parts:
            if "MONTANT:" in p:
                raw_price = p.replace("MONTANT:", "").strip()
                montant_extract = int(''.join(filter(str.isdigit, raw_price)))
            elif "PRIORITE:" in p:
                prio_extract = p.replace("PRIORITE:", "").strip()

        # Anti-doublon strict : on bloque la création si le client a DÉJÀ une commande en attente
        last_res = order_repo.get_last_for_user(wa_id)
        if last_res and last_res['statut'] == 'En attente':
            logger.debug("[ORDER] Commande bloquée pour %s : une commande est déjà En attente.", wa_id)
        else:
            new_res_id = order_repo.save_reservation(business_id, wa_id, details_extract, prio_extract, montant_extract)
            logger.info("[ORDER] Nouvelle réservation créée pour %s — %s", wa_id, details_extract[:60])

            # Émettre la notification en temps réel vers le dashboard
            try:
                from app import socketio
                socketio.emit('nouvelle_commande', {
                    'business_id': business_id,
                    'wa_id': wa_id,
                    'details': details_extract,
                    'montant': montant_extract,
                    'priorite': prio_extract,
                    'statut': 'En attente',
                    'res_id': new_res_id,
                }, room=business_id)
            except Exception as ws_err:
                logger.debug("[ORDER] Erreur Socket.IO: %s", ws_err)

        reply = reply.split("[RESERVATION:")[0].strip()
    except Exception as e:
        logger.error("[ORDER] Erreur extraction/sauvegarde: %s", e)

    return reply
