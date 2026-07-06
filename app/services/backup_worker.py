import logging
import sqlite3
from app.models.schema import get_db_path
from app.services.google_drive_service import backup_company_to_drive, refresh_google_token_if_needed
from app.services.notification_service import send_push_notification

logger = logging.getLogger(__name__)

def daily_backup_premium_companies():
    """
    Sauvegarde automatique des données pour les gérants ayant connecté leur Google Drive
    et dont le backup est activé.
    """
    logger.info("[Backup Worker] Démarrage de la tâche de sauvegarde nocturne.")
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Récupérer les business premium (ou avec backup activé)
    cursor.execute(
        "SELECT * FROM businesses WHERE is_active = 1 AND backup_enabled = 1 AND google_access_token IS NOT NULL"
    )
    companies = [dict(row) for row in cursor.fetchall()]
    conn.close()

    for company in companies:
        try:
            logger.info(f"[Backup Worker] Traitement du backup pour l'entreprise {company['id']}")
            # 1. Vérifier et rafraîchir le token Google
            creds = refresh_google_token_if_needed(company)
            
            # 2. Effectuer le backup
            link = backup_company_to_drive(company['id'], creds)
            logger.info(f"[Backup Worker] Sauvegarde réussie pour {company['id']}")
            
            # 3. Notifier le succès
            if company.get('fcm_token'):
                send_push_notification(
                    company['fcm_token'],
                    title="✅ Sauvegarde réussie",
                    body="Vos données Vira ont été sauvegardées sur Google Drive."
                )
                
        except Exception as e:
            logger.error(f"[Backup Worker] Échec du backup pour {company['id']}: {e}")
            if company.get('fcm_token'):
                send_push_notification(
                    company['fcm_token'],
                    title="⚠️ Échec de la sauvegarde",
                    body="Votre sauvegarde Google Drive a échoué. Veuillez vérifier votre connexion depuis l'application."
                )
