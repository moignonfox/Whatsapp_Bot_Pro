from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.api import api_bp
from app.repositories import business_repo

@api_bp.route('/devices/register', methods=['POST'])
@jwt_required()
def register_device():
    company_id = get_jwt_identity()
    
    data = request.get_json() or {}
    fcm_token = data.get('fcm_token')
    
    if not fcm_token:
        return jsonify({"success": False, "error": "Le champ 'fcm_token' est requis"}), 400

    business_repo.set_fcm_token(company_id, fcm_token)
    
    return jsonify({
        "success": True,
        "message": "Token FCM enregistré avec succès"
    }), 200
