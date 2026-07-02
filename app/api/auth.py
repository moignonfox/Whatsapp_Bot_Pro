from flask import request, jsonify
from werkzeug.security import check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity

from app import limiter
from app.api import api_bp
from app.repositories import business_repo

@api_bp.route('/auth/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"success": False, "error": "Identifiants manquants (username et password requis)"}), 400

    username = data['username']
    password = data['password']

    business = business_repo.get_by_id(username)
    if not business or not check_password_hash(business['password'], password):
        return jsonify({"success": False, "error": "Identifiants incorrects"}), 401

    if not dict(business).get('is_active', 1):
        return jsonify({"success": False, "error": "Compte inactif"}), 403

    # Génération du token
    access_token = create_access_token(identity=username)
    refresh_token = create_refresh_token(identity=username)

    return jsonify({
        "success": True,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "company": {
            "id": username,
            "nom": business['nom'],
            "business_type": dict(business).get('business_type', 'restaurant')
        }
    }), 200


@api_bp.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify({
        "success": True,
        "access_token": access_token
    }), 200


@api_bp.route('/auth/me', methods=['GET'])
@jwt_required()
def me():
    company_id = get_jwt_identity()
    business = business_repo.get_by_id(company_id)
    
    if not business:
        return jsonify({"success": False, "error": "Utilisateur introuvable"}), 404

    business_data = dict(business)
    # Ne pas renvoyer le mot de passe
    business_data.pop('password', None)
    business_data.pop('token_wa', None) # Sécurité additionnelle

    return jsonify({
        "success": True,
        "company": business_data
    }), 200

@api_bp.route('/auth/me', methods=['PUT'])
@jwt_required()
def update_me():
    company_id = get_jwt_identity()
    data = request.get_json() or {}
    
    nom = data.get('nom')
    is_active = data.get('is_active')
    prompt = data.get('prompt')
    msg_confirm = data.get('msg_confirm')
    horaires_json = data.get('horaires_json')
    
    # Convert is_active to int if provided
    if is_active is not None:
        is_active = 1 if str(is_active).lower() in ['1', 'true', 'yes'] else 0

    try:
        business_repo.update_basic_profile(
            biz_id=company_id,
            nom=nom,
            is_active=is_active,
            prompt=prompt,
            msg_confirm=msg_confirm,
            horaires_json=horaires_json
        )
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
