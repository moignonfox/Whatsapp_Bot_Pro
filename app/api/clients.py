"""Routes API pour la gestion des clients (ajout manuel et import CSV)."""
import csv
import io
import re
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.api import api_bp
from app.repositories import business_repo, client_repo

from app.utils import format_whatsapp_number, validate_whatsapp_number

@api_bp.route('/clients/add', methods=['POST'])
@jwt_required()
def add_client():
    """Ajoute un client manuellement."""
    biz_id = get_jwt_identity()
    data = request.get_json() or {}
    nom = data.get('nom', '').strip()
    numero = data.get('numero', '').strip()

    if not nom or not numero:
        return jsonify({"success": False, "error": "Le nom et le numéro sont obligatoires"}), 400

    wa_id = format_whatsapp_number(numero)
    is_valid, err_msg = validate_whatsapp_number(wa_id)
    if not is_valid:
        return jsonify({"success": False, "error": err_msg}), 400

    try:
        client_repo.update_name(biz_id, wa_id, nom)
        return jsonify({"success": True, "message": "Client ajouté avec succès"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route('/clients/import-csv', methods=['POST'])
@jwt_required()
def import_clients_csv():
    """Importe une liste de clients via un fichier CSV."""
    biz_id = get_jwt_identity()
    
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "Aucun fichier fourni"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "Aucun fichier sélectionné"}), 400
        
    if not file.filename.endswith('.csv'):
        return jsonify({"success": False, "error": "Le fichier doit être un CSV"}), 400

    try:
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.reader(stream)
        
        count = 0
        for i, row in enumerate(csv_input):
            if i == 0 and len(row) > 0 and 'nom' in str(row[0]).lower():
                continue # Skip header
                
            if len(row) >= 2:
                nom = row[0].strip()
                numero = row[1].strip()
                
                if nom and numero:
                    wa_id = format_whatsapp_number(numero)
                    if wa_id:
                        is_valid, _ = validate_whatsapp_number(wa_id)
                        if is_valid:
                            client_repo.update_name(biz_id, wa_id, nom)
                            count += 1
                        
        return jsonify({"success": True, "message": f"{count} clients importés avec succès", "count": count}), 200
    except Exception as e:
        return jsonify({"success": False, "error": f"Erreur lors de la lecture du CSV: {str(e)}"}), 500
