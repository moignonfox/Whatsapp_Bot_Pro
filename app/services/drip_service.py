import sqlite3
from datetime import datetime, timedelta
import logging
from app.models.schema import get_db_path
from app.repositories import marketing_repo

logger = logging.getLogger(__name__)

def process_daily_drip_campaigns():
    """
    Tâche exécutée quotidiennement pour relancer les clients à J+3.
    Uniquement pour les business PREMIUM ayant activé l'option drip_j3_enabled.
    """
    logger.info("Démarrage du job Drip Marketing (Séquences Automatisées)...")
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Trouver les business éligibles (is_active, plan PREMIUM, option activée)
    cursor.execute("""
        SELECT id, nom, drip_j3_msg 
        FROM businesses 
        WHERE is_active = 1 AND plan_abonnement = 'PREMIUM' AND drip_j3_enabled = 1
    """)
    eligible_businesses = cursor.fetchall()

    if not eligible_businesses:
        conn.close()
        logger.info("Aucun business éligible pour le Drip Marketing.")
        return

    # 2. Pour chaque business, trouver les clients dont le dernier message date d'il y a 3 jours (entre J-3 et J-4)
    # J-3 c'est: timestamp <= now - 3 jours AND timestamp > now - 4 jours
    now = datetime.now()
    limit_start = now - timedelta(days=4)
    limit_end = now - timedelta(days=3)

    for biz in eligible_businesses:
        biz_id = biz['id']
        msg_template = biz['drip_j3_msg']
        if not msg_template or not msg_template.strip():
            continue # Pas de message configuré

        # On prend la dernière interaction par client
        cursor.execute("""
            SELECT h.wa_id, MAX(h.timestamp) as last_timestamp, COALESCE(c.nom, 'Client') as client_name
            FROM history h
            LEFT JOIN clients c ON h.wa_id = c.wa_id AND c.business_id = ?
            WHERE h.business_id = ?
            GROUP BY h.wa_id
        """, (biz_id, biz_id))
        
        clients = cursor.fetchall()
        queued_count = 0
        
        for c in clients:
            try:
                last_ts = datetime.fromisoformat(c['last_timestamp'])
                # Si la dernière interaction était il y a exactement 3 jours (à 24h près)
                if limit_start < last_ts <= limit_end:
                    # Enqueue le message
                    prenom = c['client_name'].split()[0]
                    final_msg = msg_template.replace('{prenom}', prenom)
                    marketing_repo.enqueue_message(biz_id, c['wa_id'], final_msg)
                    queued_count += 1
            except Exception as e:
                logger.error(f"Erreur calcul Drip pour {c['wa_id']} : {e}")
                
        if queued_count > 0:
            logger.info(f"Drip J+3 : {queued_count} messages mis en file d'attente pour {biz['nom']}")

    conn.close()
    logger.info("Job Drip Marketing terminé.")
