from flask import request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
import uuid

from app import limiter
from app.api import api_bp
from app.repositories import business_repo

@api_bp.route('/auth/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    data = request.get_json() or {}
    
    required_fields = ['email', 'password', 'nom', 'owner_name', 'owner_phone', 'business_type', 'devise']
    for field in required_fields:
        if not data.get(field):
            return jsonify({"success": False, "error": f"Champ requis manquant : {field}"}), 400
    
    email = data['email'].strip().lower()
    
    # Vérifier si l'email est déjà utilisé
    existing = business_repo.get_by_email(email)
    if existing:
        return jsonify({"success": False, "error": "Un compte avec cet email existe déjà."}), 409
    
    # L'ID unique sera l'email lui-même (slugifié)
    biz_id = email.replace('@', '_').replace('.', '_')
    
    hashed_password = generate_password_hash(data['password'])
    
    try:
        business_repo.create_business_registration(
            biz_id=biz_id,
            email=email,
            password=hashed_password,
            nom=data['nom'],
            owner_name=data['owner_name'],
            owner_phone=data['owner_phone'],
            requested_bot_phone=data.get('requested_bot_phone', ''),
            business_type=data['business_type'],
            devise=data['devise'],
        )
    except Exception as e:
        return jsonify({"success": False, "error": f"Erreur lors de la création du compte : {str(e)}"}), 500
    
    # Connexion automatique après inscription
    access_token = create_access_token(identity=biz_id)
    refresh_token = create_refresh_token(identity=biz_id)
    
    return jsonify({
        "success": True,
        "message": "Compte créé. En attente de validation par l'administrateur.",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "company": {
            "id": biz_id,
            "nom": data['nom'],
            "is_approved": 0,
        }
    }), 201


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
    email = data.get('email')
    owner_phone = data.get('owner_phone')
    
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
            horaires_json=horaires_json,
            email=email,
            owner_phone=owner_phone
        )
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/auth/password', methods=['PUT'])
@jwt_required()
def update_password():
    company_id = get_jwt_identity()
    data = request.get_json() or {}
    
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not old_password or not new_password:
        return jsonify({"success": False, "error": "Ancien et nouveau mot de passe requis"}), 400
        
    business = business_repo.get_by_id(company_id)
    if not business or not check_password_hash(business['password'], old_password):
        return jsonify({"success": False, "error": "Ancien mot de passe incorrect"}), 401
        
    try:
        import sqlite3
        from app.models.schema import get_db_path
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        hashed_pw = generate_password_hash(new_password)
        cursor.execute("UPDATE businesses SET password = ? WHERE id = ?", (hashed_pw, company_id))
        conn.commit()
        conn.close()
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

