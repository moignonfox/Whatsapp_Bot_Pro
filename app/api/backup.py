import os
import json
from flask import Blueprint, jsonify, request, redirect
from flask_jwt_extended import jwt_required, get_jwt_identity
from google_auth_oauthlib.flow import Flow
import tempfile
from datetime import datetime
import sqlite3

from app.models.schema import get_db_path
from app.services.crypto_service import encrypt_token, decrypt_token
from app.services.google_drive_service import backup_company_to_drive, refresh_google_token_if_needed, export_company_data
from app.api import api_bp

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_oauth_flow():
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')
    
    if not all([client_id, client_secret, redirect_uri]):
        raise ValueError("Google OAuth credentials non configurés.")
        
    client_config = {
        "web": {
            "client_id": client_id,
            "project_id": "vira-backup",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": client_secret,
            "redirect_uris": [redirect_uri]
        }
    }
    
    return Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )

@api_bp.route('/backup/google/auth-url', methods=['GET'])
@jwt_required()
def google_auth_url():
    """Génère l'URL pour l'écran de consentement Google."""
    company_id = get_jwt_identity()
    try:
        flow = get_oauth_flow()
        # On passe company_id dans le paramètre d'état pour le récupérer après
        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',
            state=company_id
        )
        return jsonify({"success": True, "auth_url": auth_url})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route('/backup/google/callback', methods=['GET'])
def google_callback():
    """Reçoit le code de retour Google, stocke le token et redirige."""
    try:
        state = request.args.get('state') # = company_id
        code = request.args.get('code')
        
        if not state or not code:
            return "Paramètres manquants.", 400
            
        flow = get_oauth_flow()
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        enc_access = encrypt_token(credentials.token)
        enc_refresh = encrypt_token(credentials.refresh_token) if credentials.refresh_token else None
        
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        
        query = "UPDATE businesses SET google_access_token = ?, backup_enabled = 1"
        params = [enc_access]
        
        if enc_refresh:
            query += ", google_refresh_token = ?"
            params.append(enc_refresh)
            
        query += " WHERE id = ?"
        params.append(state)
        
        cursor.execute(query, tuple(params))
        conn.commit()
        conn.close()
        
        # Rediriger vers l'application Flutter via Deep Link
        return redirect("vira://backup-success")
        
    except Exception as e:
        return f"Erreur lors de la configuration du Drive: {str(e)}", 500

@api_bp.route('/backup/google/status', methods=['GET'])
@jwt_required()
def get_backup_status():
    company_id = get_jwt_identity()
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT google_access_token, last_backup_at, backup_enabled, email FROM businesses WHERE id = ?", (company_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return jsonify({"success": False, "error": "Company not found"}), 404
        
    return jsonify({
        "success": True,
        "is_connected": bool(row['google_access_token']),
        "last_backup_at": row['last_backup_at'],
        "backup_enabled": bool(row['backup_enabled']),
        "google_email": row['email'] # Temporaire, on n'a pas forcé la collecte de l'email google
    })

@api_bp.route('/backup/google/disconnect', methods=['DELETE'])
@jwt_required()
def disconnect_drive():
    company_id = get_jwt_identity()
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE businesses SET google_access_token = NULL, google_refresh_token = NULL, google_drive_folder_id = NULL, backup_enabled = 0 WHERE id = ?",
        (company_id,)
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Drive déconnecté"})

@api_bp.route('/backup/google/trigger', methods=['POST'])
@jwt_required()
def trigger_backup():
    company_id = get_jwt_identity()
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM businesses WHERE id = ?", (company_id,))
    company = dict(cursor.fetchone())
    conn.close()
    
    if not company.get('google_access_token'):
        return jsonify({"success": False, "error": "Google Drive non connecté."}), 400
        
    try:
        creds = refresh_google_token_if_needed(company)
        link = backup_company_to_drive(company_id, creds)
        return jsonify({"success": True, "drive_link": link, "message": "Sauvegarde réussie"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route('/backup/export/json', methods=['GET'])
@jwt_required()
def export_json():
    """Exporte manuellement les données en JSON."""
    company_id = get_jwt_identity()
    try:
        data = export_company_data(company_id)
        return jsonify(data)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route('/backup/export/csv', methods=['GET'])
@jwt_required()
def export_csv():
    """Export CSV basique (commandes ou clients)"""
    company_id = get_jwt_identity()
    export_type = request.args.get('type', 'orders')
    
    import csv
    from io import StringIO
    from flask import Response
    
    si = StringIO()
    cw = csv.writer(si)
    
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    if export_type == 'orders':
        cursor.execute("SELECT id, wa_id, details, statut, montant, created_at FROM reservations WHERE business_id = ?", (company_id,))
        cw.writerow(['ID', 'Client WhatsApp', 'Details', 'Statut', 'Montant', 'Date'])
        cw.writerows(cursor.fetchall())
        filename = f"commandes_{company_id}.csv"
    else:
        cursor.execute("SELECT wa_id, nom, date_inscription FROM clients WHERE business_id = ?", (company_id,))
        cw.writerow(['WhatsApp', 'Nom', 'Date Inscription'])
        cw.writerows(cursor.fetchall())
        filename = f"clients_{company_id}.csv"
        
    conn.close()
    
    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )
