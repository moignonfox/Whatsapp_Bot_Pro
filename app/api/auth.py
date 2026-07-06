import logging
from flask import request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)

from app import limiter
from app.api import api_bp
from app.repositories import business_repo

logger = logging.getLogger(__name__)


def _blocklist_token(jti: str, expires_at) -> None:
    """InsÃ¨re un JTI dans la table jwt_blocklist (rÃ©vocation)."""
    import sqlite3
    from app.models.schema import get_db_path
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO jwt_blocklist (jti, expires_at) VALUES (?, ?)",
        (jti, expires_at)
    )
    conn.commit()
    conn.close()


@api_bp.route('/auth/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    data = request.get_json() or {}

    required_fields = ['email', 'password', 'nom', 'owner_name', 'owner_phone', 'business_type', 'devise', 'requested_bot_phone']
    for field in required_fields:
        if not data.get(field):
            return jsonify({"success": False, "error": f"Champ requis manquant : {field}"}), 400

    email = data['email'].strip().lower()

    # Vérifier si l'email est déjà utilisé
    existing = business_repo.get_by_email(email)
    if existing:
        return jsonify({"success": False, "error": "Un compte avec cet email existe déjà."}), 409

    # L'ID unique sera une suite de chiffres générée aléatoirement
    import random
    while True:
        biz_id = str(random.randint(10000000, 99999999))
        if not business_repo.get_by_id(biz_id):
            break

    hashed_password = generate_password_hash(data['password'])

    try:
        business_repo.create_business_registration(
            biz_id=biz_id,
            email=email,
            password=hashed_password,
            nom=data['nom'],
            owner_name=data['owner_name'],
            owner_phone=data['owner_phone'],
            requested_bot_phone=data['requested_bot_phone'],
            business_type=data['business_type'],
            devise=data['devise'],
        )
        try:
            from app.services.notification_master_service import create_master_notification
            create_master_notification('inscription', 'Nouvelle inscription', f"Nouveau business (Mobile) : {data['nom']}", biz_id)
        except Exception:
            pass
    except Exception as e:
        logger.error("Erreur création compte [%s]: %s", biz_id, e, exc_info=True)
        return jsonify({"success": False, "error": "Erreur lors de la création du compte. Veuillez réessayer."}), 500

    try:
        from app.services.notification_master_service import create_master_notification
        create_master_notification('inscription', 'Nouvelle inscription', f'Nouveau business (App) : {data["nom"]}', biz_id)
    except Exception as e:
        logger.error("Erreur notification master [%s]: %s", biz_id, e)

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

    email_input = data['username'].strip().lower()
    password = data['password']

    business = business_repo.get_by_email(email_input)
    if not business:
        business = business_repo.get_by_id(email_input)
    if not business:
        slugified = email_input.replace('@', '_').replace('.', '_')
        business = business_repo.get_by_id(slugified)

    if not business or not check_password_hash(business['password'], password):
        return jsonify({"success": False, "error": "Identifiants incorrects"}), 401

    if not dict(business).get('is_active', 1):
        return jsonify({"success": False, "error": "Compte inactif"}), 403

    biz_id = business['id']

    # GÃ©nÃ©ration des tokens
    access_token = create_access_token(identity=biz_id)
    refresh_token = create_refresh_token(identity=biz_id)

    return jsonify({
        "success": True,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "company": {
            "id": biz_id,
            "nom": business['nom'],
            "business_type": dict(business).get('business_type', 'restaurant')
        }
    }), 200


@api_bp.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    jwt_data = get_jwt()

    # RÃ©voquer l'ancien refresh token (rotation sÃ©curisÃ©e)
    _blocklist_token(jwt_data['jti'], jwt_data.get('exp'))

    access_token = create_access_token(identity=identity)
    new_refresh_token = create_refresh_token(identity=identity)

    return jsonify({
        "success": True,
        "access_token": access_token,
        "refresh_token": new_refresh_token,
    }), 200


@api_bp.route('/auth/logout', methods=['POST'])
@jwt_required(verify_type=False)
def logout():
    """RÃ©voque le token courant (access ou refresh) en l'ajoutant Ã  la blocklist."""
    jwt_data = get_jwt()
    _blocklist_token(jwt_data['jti'], jwt_data.get('exp'))
    return jsonify({"success": True, "message": "DÃ©connexion rÃ©ussie."}), 200


@api_bp.route('/auth/me', methods=['GET'])
@jwt_required()
def me():
    company_id = get_jwt_identity()
    business = business_repo.get_by_id(company_id)

    if not business:
        return jsonify({"success": False, "error": "Utilisateur introuvable"}), 404

    business_data = dict(business)
    # Ne jamais retourner les donnÃ©es sensibles
    business_data.pop('password', None)
    business_data.pop('token_wa', None)
    business_data.pop('cinetpay_apikey', None)

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
        logger.error("Erreur mise Ã  jour profil [%s]: %s", company_id, e, exc_info=True)
        return jsonify({"success": False, "error": "Erreur interne. Veuillez rÃ©essayer."}), 500


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
        logger.error("Erreur changement mot de passe [%s]: %s", company_id, e, exc_info=True)
        return jsonify({"success": False, "error": "Erreur interne. Veuillez rÃ©essayer."}), 500



@api_bp.route('/auth/forgot-password', methods=['POST'])
@limiter.limit("5 per minute")
def forgot_password_api():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    
    if not email:
        return jsonify({"success": False, "error": "L'email est requis."}), 400
        
    business = business_repo.get_by_email(email)
    if business:
        try:
            from app.services.notification_master_service import create_master_notification
            create_master_notification('alerte', 'Mot de passe oublié', f"Mot de passe oublié (Mobile): {business['nom']} ({email})", business['id'])
        except Exception:
            pass
            
    # Succès générique pour sécurité
    return jsonify({
        "success": True, 
        "message": "Si cet email existe, le Master a été notifié et vous contactera pour réinitialiser votre mot de passe."
    }), 200
