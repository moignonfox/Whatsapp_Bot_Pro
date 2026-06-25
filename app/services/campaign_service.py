"""
campaign_service.py — Service de campagnes marketing (offres PRO et PREMIUM).

Fonctionnalités :
- Envoi de masse avec garde plan (PRO/PREMIUM requis).
- Délais anti-spam aléatoires uniquement pour les offres PREMIUM.
- Personnalisation du message via les variables {prenom} et {wa_id}.

Usage futur :
    from app.services import campaign_service
    campaign_service.send_campaign(biz_id, clients, message_template)
"""

import time
import random
from typing import List, Any

from app.services import whatsapp_service


# ---------------------------------------------------------------------------
# Constantes des délais anti-spam (offre PREMIUM)
# ---------------------------------------------------------------------------
DELAY_MIN_SECONDS = 8   # délai minimum entre deux messages
DELAY_MAX_SECONDS = 25  # délai maximum entre deux messages


def send_campaign(
    biz_id: str,
    business_info: dict,
    clients: List[Any],
    message_template: str,
) -> dict:
    """Envoie une campagne WhatsApp à une liste de clients.

    Args:
        biz_id:           Identifiant du business.
        business_info:    Dictionnaire du business (doit contenir plan_abonnement).
        clients:          Liste des clients destinataires (doivent avoir 'wa_id' et 'nom').
        message_template: Template du message. Supporte {prenom} et {wa_id}.

    Returns:
        Un dict { 'sent': int, 'failed': int, 'skipped_plan': bool }

    Raises:
        PermissionError: Si le plan du business ne permet pas les campagnes.
    """
    plan = business_info.get('plan_abonnement', 'BASIC')
    phone_id = business_info.get('whatsapp_phone_id')
    token = business_info.get('token_wa')

    # -- Garde plan ----------------------------------------------------------
    if plan not in ('PRO', 'PREMIUM'):
        raise PermissionError(
            f"Les campagnes marketing nécessitent au minimum le plan PRO. "
            f"Plan actuel : {plan}."
        )

    is_premium = (plan == 'PREMIUM')
    sent = 0
    failed = 0

    for i, client in enumerate(clients):
        wa_id = client.get('wa_id') or client.get('wa_id', '')
        prenom = (client.get('nom') or wa_id).split()[0]

        # Personnalisation du message
        message = message_template.replace('{prenom}', prenom).replace('{wa_id}', wa_id)

        try:
            whatsapp_service.send_message(wa_id, message, phone_id, token)
            sent += 1
        except Exception as exc:
            print(f"[CampaignService] Erreur envoi vers {wa_id} : {exc}")
            failed += 1

        # Délai anti-spam PREMIUM — appliqué sauf pour le dernier message
        if is_premium and i < len(clients) - 1:
            delay = random.uniform(DELAY_MIN_SECONDS, DELAY_MAX_SECONDS)
            print(f"[CampaignService] Délai anti-spam : {delay:.1f}s avant le prochain message.")
            time.sleep(delay)

    return {
        'sent': sent,
        'failed': failed,
        'skipped_plan': False,
        'anti_spam_active': is_premium,
    }
