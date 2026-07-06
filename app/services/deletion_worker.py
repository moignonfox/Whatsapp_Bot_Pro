import logging
import sqlite3
import hashlib
from datetime import datetime, timedelta
from app.models.schema import get_db_path

logger = logging.getLogger(__name__)

def process_scheduled_deletions():
    """
    Anonymise et supprime les comptes marqués pour suppression
    dont le délai de 30 jours est écoulé.
    """
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        
        # Trouver les entreprises à supprimer
        now_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        seven_days_ago_str = (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            SELECT id FROM businesses 
            WHERE 
            ((is_active = 0 OR status = 'deleted') AND deletion_scheduled_at IS NOT NULL AND deletion_scheduled_at <= ?)
            OR
            (status = 'archived' AND archived_at IS NOT NULL AND archived_at <= ?)
        ''', (now_str, seven_days_ago_str))
        
        companies = cursor.fetchall()
        
        for (company_id,) in companies:
            logger.info(f"Processing deletion for company: {company_id}")
            
            # 1. Obtenir tous les clients de l'entreprise
            cursor.execute("SELECT wa_id FROM clients WHERE business_id = ?", (company_id,))
            clients = cursor.fetchall()
            
            for (wa_id,) in clients:
                # Créer un ID anonyme basé sur le hash
                # ex: deleted_a3f8...
                wa_hash = hashlib.md5(wa_id.encode('utf-8')).hexdigest()[:8]
                anon_id = f"deleted_{wa_hash}"
                anon_user_id = f"deleted_user_{wa_hash}"
                
                # Update history
                cursor.execute("""
                    UPDATE history 
                    SET wa_id = ? 
                    WHERE business_id = ? AND wa_id = ?
                """, (anon_user_id, company_id, wa_id))
                
                # Update reservations
                cursor.execute("""
                    UPDATE reservations 
                    SET wa_id = ? 
                    WHERE business_id = ? AND wa_id = ?
                """, (anon_id, company_id, wa_id))
                
                # Update clients
                cursor.execute("""
                    UPDATE clients 
                    SET wa_id = ?, nom = 'Client supprimé' 
                    WHERE business_id = ? AND wa_id = ?
                """, (anon_id, company_id, wa_id))

                # Update client_tags (if exists)
                cursor.execute("""
                    UPDATE client_tags
                    SET wa_id = ?
                    WHERE business_id = ? AND wa_id = ?
                """, (anon_id, company_id, wa_id))
                
            # 2. Supprimer les données annexes liées à l'entreprise
            cursor.execute("DELETE FROM employees WHERE business_id = ?", (company_id,))
            cursor.execute("DELETE FROM products WHERE business_id = ?", (company_id,))
            cursor.execute("DELETE FROM ai_agents WHERE business_id = ?", (company_id,))
            cursor.execute("DELETE FROM tags WHERE business_id = ?", (company_id,))
            
            # 3. Marquer le compte entreprise comme supprimé (Soft Delete final) et anonymiser les PII
            cursor.execute('''
                UPDATE businesses 
                SET status = 'deleted', is_active = 0, token_wa = NULL, fcm_token = NULL, password = NULL, email = NULL, owner_phone = NULL
                WHERE id = ?
            ''', (company_id,))
            
            logger.info(f"Successfully soft-deleted and anonymized company: {company_id}")

        conn.commit()
        conn.close()
        if companies:
            logger.info(f"Deleted {len(companies)} companies.")
            
    except Exception as e:
        logger.error(f"Error in process_scheduled_deletions: {e}", exc_info=True)
