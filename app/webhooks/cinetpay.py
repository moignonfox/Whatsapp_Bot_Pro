"""
cinetpay.py — Webhook de notification de paiement CinetPay.

Vérification HMAC de chaque notification entrante pour garantir
l'authenticité de la source. Chaque business a ses propres clés
CinetPay (multi-tenant), stockées chiffrées en base.
"""

import hmac
import hashlib
import logging
from flask import Blueprint, request, make_response, jsonify
from app.models.schema import get_db_path

cinetpay_bp = Blueprint('cinetpay', __name__)
logger = logging.getLogger(__name__)


def _get_cinetpay_secret(site_id: str) -> str | None:
    """Récupère et déchiffre la clé API CinetPay d'un business par site_id."""
    import sqlite3
    from app.services.crypto_service import decrypt_token
    try:
        conn = sqlite3.connect(get_db_path())
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT cinetpay_apikey FROM businesses WHERE cinetpay_site_id = ?",
            (site_id,)
        )
        row = cursor.fetchone()
        conn.close()
        if row and row['cinetpay_apikey']:
            return decrypt_token(row['cinetpay_apikey'])
        return None
    except Exception as e:
        logger.error("Erreur récupération clé CinetPay: %s", e)
        return None


def _verify_cinetpay_signature(payload: dict, api_key: str) -> bool:
    """Vérifie la signature HMAC-SHA256 de la notification CinetPay.

    CinetPay signe avec : HMAC-SHA256(api_key, cpm_site_id + cpm_trans_id + cpm_trans_date + cpm_amount)
    Référence : documentation CinetPay Webhook V2.
    """
    try:
        data_to_sign = (
            payload.get('cpm_site_id', '') +
            payload.get('cpm_trans_id', '') +
            payload.get('cpm_trans_date', '') +
            str(payload.get('cpm_amount', ''))
        )
        expected = hmac.new(
            api_key.encode(),
            data_to_sign.encode(),
            hashlib.sha256
        ).hexdigest()
        received = payload.get('cpm_page_action', '')
        return hmac.compare_digest(expected, received)
    except Exception as e:
        logger.error("Erreur vérification signature CinetPay: %s", e)
        return False


@cinetpay_bp.route('/webhook/cinetpay', methods=['POST'])
def cinetpay_notification():
    """Point d'entrée des notifications de paiement CinetPay."""
    payload = request.get_json(silent=True) or request.form.to_dict()

    if not payload:
        return make_response("Payload invalide", 400)

    site_id = payload.get('cpm_site_id', '')
    if not site_id:
        return make_response("site_id manquant", 400)

    # Récupérer la clé API du business concerné
    api_key = _get_cinetpay_secret(site_id)
    if not api_key:
        logger.warning("Aucune clé CinetPay trouvée pour site_id: %s", site_id)
        return make_response("Business inconnu", 404)

    # Vérification HMAC
    if not _verify_cinetpay_signature(payload, api_key):
        logger.warning("Signature CinetPay invalide pour site_id: %s", site_id)
        return make_response("Signature invalide", 403)

    # Traitement du paiement validé
    transaction_id = payload.get('cpm_trans_id', '')
    status = payload.get('cpm_result', '')  # '00' = succès

    logger.info("CinetPay notification reçue — trans_id=%s, status=%s", transaction_id, status)

    if status == '00':
        # TODO : mettre à jour le statut d'abonnement du business
        # Exemple : business_repo.activate_subscription(site_id, transaction_id)
        logger.info("Paiement CinetPay validé : %s", transaction_id)
    else:
        logger.warning("Paiement CinetPay échoué ou annulé : trans_id=%s, result=%s", transaction_id, status)

    # CinetPay attend une réponse vide avec 200 pour confirmer la réception
    return make_response("", 200)
