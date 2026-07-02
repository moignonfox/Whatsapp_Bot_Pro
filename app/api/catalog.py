from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.api import api_bp
from app.repositories import catalog_repo

@api_bp.route('/catalog/products', methods=['GET'])
@jwt_required()
def get_products():
    company_id = get_jwt_identity()
    
    only_available = request.args.get('available') == 'true'
    
    products = catalog_repo.get_by_business(company_id, only_available=only_available)
    
    return jsonify({
        "success": True,
        "products": [dict(p) for p in products]
    }), 200


import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

@api_bp.route('/catalog/products', methods=['POST'])
@jwt_required()
def add_product():
    company_id = get_jwt_identity()
    
    # Handle multipart/form-data or json
    content_type = request.content_type or ''
    if content_type.startswith('multipart/form-data'):
        data = request.form
    else:
        data = request.get_json(silent=True) or request.form or {}
        
    nom = data.get('nom')
    prix = data.get('prix', 0)
    
    if not nom:
        return jsonify({"success": False, "error": "Le nom du produit est requis"}), 400
        
    image_url = data.get('image_url')
    
    # Handle file upload
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename:
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(upload_path)
            # Make sure this matches the static path served by Flask
            image_url = f"/static/uploads/{unique_filename}"
            
    is_visible = 1 if str(data.get('is_visible', '1')).lower() in ['1', 'true'] else 0

    try:
        catalog_repo.add_product(
            biz_id=company_id,
            nom=nom,
            prix=int(prix),
            description=data.get('description', ''),
            categorie=data.get('categorie', 'Général'),
            image_url=image_url,
            is_visible=is_visible,
            duree_minutes=int(data.get('duree_minutes', 30))
        )
        return jsonify({"success": True}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/catalog/products/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    company_id = get_jwt_identity()
    
    content_type = request.content_type or ''
    if content_type.startswith('multipart/form-data'):
        data = request.form
    else:
        data = request.get_json(silent=True) or request.form or {}
        
    nom = data.get('nom')
    prix = data.get('prix')
    
    if not nom or prix is None:
        return jsonify({"success": False, "error": "Nom et prix sont requis"}), 400
        
    image_url = data.get('image_url')
    
    # Handle file upload
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename:
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(upload_path)
            image_url = f"/static/uploads/{unique_filename}"
            
    is_visible = 1 if str(data.get('is_visible', '1')).lower() in ['1', 'true'] else 0

    try:
        catalog_repo.update_product(
            product_id=product_id,
            business_id=company_id,
            nom=nom,
            prix=int(prix),
            description=data.get('description', ''),
            categorie=data.get('categorie', 'Général'),
            image_url=image_url,
            is_visible=is_visible,
            duree_minutes=int(data.get('duree_minutes', 30))
        )
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/catalog/products/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    company_id = get_jwt_identity()
    try:
        catalog_repo.delete_product(product_id, company_id)
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/catalog/products/<int:product_id>/stock', methods=['PUT'])
@jwt_required()
def toggle_stock(product_id):
    company_id = get_jwt_identity()
    catalog_repo.toggle_availability(product_id, company_id)
    return jsonify({"success": True, "product_id": product_id}), 200
