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
    
    # 1. Trouver les business éligibles (is_active, PRO ou PREMIUM, option activée)
    cursor.execute("""
        SELECT id, nom, plan_abonnement, drip_j3_msg 
        FROM businesses 
        WHERE is_active = 1 AND plan_abonnement IN ('PRO', 'PREMIUM') AND drip_j3_enabled = 1
    """)
    eligible_businesses = cursor.fetchall()

    if not eligible_businesses:
        conn.close()
        logger.info("Aucun business éligible pour le Drip Marketing.")
        return

    # 2. Pour chaque business, trouver les clients
    now = datetime.now()
    limit_end = now - timedelta(days=3)

    for biz in eligible_businesses:
        biz_id = biz['id']
        msg_template = biz['drip_j3_msg']
        if not msg_template or not msg_template.strip():
            continue

        cursor.execute("""
            SELECT h1.wa_id, h1.timestamp as last_timestamp, h1.role as last_role, h1.message as last_message, COALESCE(c.nom, 'Client') as client_name
            FROM history h1
            INNER JOIN (
                SELECT wa_id, MAX(timestamp) as max_ts
                FROM history
                WHERE business_id = ?
                GROUP BY wa_id
            ) h2 ON h1.wa_id = h2.wa_id AND h1.timestamp = h2.max_ts
            LEFT JOIN clients c ON h1.wa_id = c.wa_id AND c.business_id = ?
            WHERE h1.business_id = ?
        """, (biz_id, biz_id, biz_id))
        
        clients = cursor.fetchall()
        queued_count = 0
        
        for c in clients:
            try:
                last_ts = datetime.fromisoformat(c['last_timestamp'])
                # Client inactif depuis AU MOINS 3 jours ET n'a pas répondu au dernier message du bot
                if last_ts <= limit_end and c['last_role'] == 'assistant':
                    # Anti-boucle: Si le dernier message envoyé est DÉJÀ la relance, on ne la renvoie pas en boucle
                    if "[CAMPAGNE MARKETING]" in c['last_message'] and msg_template[:20] in c['last_message']:
                        continue
                        
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
