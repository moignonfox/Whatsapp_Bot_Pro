import os
import json
import logging
from datetime import date, datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import tempfile
import sqlite3

from app.models.schema import get_db_path
from app.services.crypto_service import decrypt_token, encrypt_token

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_drive_service(creds):
    """Construit le service Google Drive."""
    return build('drive', 'v3', credentials=creds)

def refresh_google_token_if_needed(company) -> Credentials:
    """Rafraîchit le token Google si nécessaire et retourne l'objet Credentials."""
    access_token = decrypt_token(company['google_access_token']) if company.get('google_access_token') else None
    refresh_token = decrypt_token(company['google_refresh_token']) if company.get('google_refresh_token') else None
    
    if not access_token or not refresh_token:
        raise ValueError("Tokens Google manquants.")
        
    creds = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri='https://oauth2.googleapis.com/token',
        client_id=os.getenv('GOOGLE_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
        scopes=SCOPES
    )
    
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # Sauvegarder le nouveau token en DB
        new_encrypted = encrypt_token(creds.token)
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE businesses SET google_access_token = ? WHERE id = ?",
            (new_encrypted, company['id'])
        )
        conn.commit()
        conn.close()
        
    return creds

def get_or_create_folder(service, folder_name: str) -> str:
    """Récupère l'ID du dossier ou le crée s'il n'existe pas."""
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    files = results.get('files', [])
    
    if not files:
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = service.files().create(body=file_metadata, fields='id').execute()
        return folder.get('id')
    return files[0].get('id')

def cleanup_old_backups(service, folder_id: str, keep: int = 7):
    """Ne conserve que les N derniers backups dans le dossier."""
    query = f"'{folder_id}' in parents and trashed=false"
    results = service.files().list(
        q=query, 
        orderBy="createdTime desc",
        fields="files(id, name)"
    ).execute()
    
    files = results.get('files', [])
    for file in files[keep:]:
        try:
            service.files().delete(fileId=file['id']).execute()
            logger.info(f"Fichier de backup ancien supprimé : {file['name']}")
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de l'ancien backup {file['name']}: {e}")

def export_company_data(company_id: str) -> dict:
    """Collecte toutes les données exportables d'une entreprise (SANS clés API/tokens)."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Business info
    cursor.execute("SELECT * FROM businesses WHERE id = ?", (company_id,))
    biz = cursor.fetchone()
    if not biz:
        conn.close()
        raise ValueError("Business introuvable")
        
    biz_dict = dict(biz)
    # 🔴 SUPPRESSION DES DONNÉES SENSIBLES
    sensitive_keys = ['token_wa', 'password', 'google_access_token', 'google_refresh_token', 'fcm_token', 'cinetpay_apikey', 'cinetpay_site_id']
    for k in sensitive_keys:
        biz_dict.pop(k, None)
        
    # Clients
    cursor.execute("SELECT wa_id, nom, date_inscription FROM clients WHERE business_id = ?", (company_id,))
    clients = [dict(r) for r in cursor.fetchall()]
    
    # Catalogue
    cursor.execute("SELECT categorie, nom, description, prix, disponible, is_visible FROM products WHERE business_id = ?", (company_id,))
    catalog = [dict(r) for r in cursor.fetchall()]
    
    # Commandes (90 derniers jours)
    cursor.execute(
        "SELECT id, wa_id, details, statut, priorite, montant, created_at FROM reservations WHERE business_id = ? AND created_at >= date('now', '-90 days')", 
        (company_id,)
    )
    orders = [dict(r) for r in cursor.fetchall()]
    
    conn.close()
    
    return {
        "backup_date": datetime.now().isoformat(),
        "version": "1.0",
        "company": biz_dict,
        "clients": clients,
        "catalog": catalog,
        "orders_last_90_days": orders,
    }

def backup_company_to_drive(company_id: str, creds: Credentials) -> str:
    """Sauvegarde les données d'une entreprise sur son Google Drive."""
    # 1. Collecter les données
    data = export_company_data(company_id)
    
    # 2. Écrire le fichier JSON
    filename = f"vira_backup_{company_id}_{date.today().isoformat()}.json"
    tmp_path = os.path.join(tempfile.gettempdir(), filename)
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    # 3. Upload sur Google Drive
    service = get_drive_service(creds)
    folder_id = get_or_create_folder(service, "Vira Backups")
    
    file_metadata = {
        'name': filename,
        'parents': [folder_id]
    }
    media = MediaFileUpload(
        tmp_path,
        mimetype='application/json'
    )
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, name, webViewLink'
    ).execute()
    
    # 4. Rotation des backups
    cleanup_old_backups(service, folder_id, keep=7)
    
    # Nettoyer fichier temporaire
    os.remove(tmp_path)
    
    # MAJ date de backup dans la db
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE businesses SET last_backup_at = ?, google_drive_folder_id = ? WHERE id = ?",
        (datetime.now().isoformat(), folder_id, company_id)
    )
    conn.commit()
    conn.close()
    
    return file.get('webViewLink')
