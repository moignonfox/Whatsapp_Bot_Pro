import logging
from datetime import datetime, timedelta
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from werkzeug.security import check_password_hash

from app.api import api_bp
from app.repositories import business_repo
from app.api.auth import _blocklist_token
from app.services.whatsapp_disconnect_service import disconnect_whatsapp_number
from app.services.email_service import send_deletion_confirmation_email
import sqlite3
from app.models.schema import get_db_path

logger = logging.getLogger(__name__)

@api_bp.route('/account', methods=['DELETE'])
@jwt_required()
def delete_account():
    company_id = get_jwt_identity()
    data = request.get_json() or {}
    password = data.get('password')

    if not password:
        return jsonify({"success": False, "error": "Mot de passe requis pour confirmer la suppression."}), 400

    business = business_repo.get_by_id(company_id)
    if not business:
        return jsonify({"success": False, "error": "Compte introuvable."}), 404

    # Vérification stricte du mot de passe avec bcrypt via werkzeug
    if not check_password_hash(business['password'], password):
        return jsonify({"success": False, "error": "Mot de passe incorrect."}), 401

    try:
        # 1. Appeler l'API Meta pour désabonner le numéro
        token_wa_encrypted = business.get('token_wa')
        phone_number_id = business.get('whatsapp_phone_id')
        whatsapp_released = False
        
        if token_wa_encrypted and phone_number_id:
            whatsapp_released = disconnect_whatsapp_number(token_wa_encrypted, phone_number_id)

        # 2. Marquer le compte comme inactif et planifier la suppression
        deletion_date = datetime.utcnow() + timedelta(days=30)
        deletion_date_str = deletion_date.strftime('%Y-%m-%d %H:%M:%S')
        deletion_date_human = deletion_date.strftime('%d/%m/%Y')

        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        
        # On passe is_active = 0, on met le deletion_scheduled_at
        # Optionnel: on peut aussi supprimer token_wa pour éviter tout appel futur
        cursor.execute("""
            UPDATE businesses 
            SET is_active = 0, 
                deletion_scheduled_at = ?,
                token_wa = NULL
            WHERE id = ?
        """, (deletion_date_str, company_id))
        
        conn.commit()
        conn.close()

        try:
            from app.services.notification_master_service import create_master_notification
            create_master_notification('alerte', 'Suppression compte', f"Le gérant {business.get('nom', 'Inconnu')} a supprimé son compte (J+30)", company_id)
        except Exception:
            pass

        # 3. Révoquer le token actuel (blocklist)
        jwt_data = get_jwt()
        _blocklist_token(jwt_data['jti'], jwt_data.get('exp'))

        # 4. Envoyer l'email de confirmation
        email = business.get('email')
        if email:
            send_deletion_confirmation_email(email, deletion_date_human)

        return jsonify({
            "success": True,
            "message": "Compte supprimé. Votre numéro WhatsApp est libéré.",
            "whatsapp_released": whatsapp_released,
            "data_deletion_date": deletion_date_human
        }), 200

    except Exception as e:
        logger.error(f"Erreur lors de la suppression du compte {company_id}: {e}", exc_info=True)
        return jsonify({"success": False, "error": "Erreur interne lors de la suppression du compte."}), 500
