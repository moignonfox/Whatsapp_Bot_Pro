import sqlite3
from typing import List, Dict, Optional
from app.models.schema import get_db_path

def enqueue_message(business_id: str, wa_id: str, message: str, campaign_id: int = None) -> None:
    """Ajoute un message dans la file d'attente d'envoi."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO campaign_queue (business_id, wa_id, message, status, campaign_id) VALUES (?, ?, ?, 'pending', ?)",
        (business_id, wa_id, message, campaign_id)
    )
    conn.commit()
    conn.close()

def get_next_pending_message() -> Optional[Dict]:
    """Récupère le prochain message en attente (FIFO)."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, business_id, wa_id, message, campaign_id 
        FROM campaign_queue 
        WHERE status = 'pending' 
        ORDER BY id ASC 
        LIMIT 1
    """)
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def mark_message_status(msg_id: int, status: str, campaign_id: int = None) -> None:
    """Met à jour le statut d'un message dans la file ('sent', 'failed')."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("UPDATE campaign_queue SET status = ? WHERE id = ?", (status, msg_id))
    
    if campaign_id and status == 'sent':
        cursor.execute("UPDATE campaigns SET sent_count = sent_count + 1 WHERE id = ?", (campaign_id,))
    
    conn.commit()
    conn.close()

def get_queue_stats(business_id: str) -> Dict[str, int]:
    """Récupère les statistiques de la file pour un business."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("""
        SELECT status, COUNT(*) 
        FROM campaign_queue 
        WHERE business_id = ? 
        GROUP BY status
    """, (business_id,))
    rows = cursor.fetchall()
    conn.close()
    
    stats = {'pending': 0, 'sent': 0, 'failed': 0}
    for status, count in rows:
        if status in stats:
            stats[status] = count
    return stats

def get_today_campaigns_count(business_id: str) -> int:
    """Compte le nombre de campagnes uniques envoyées aujourd'hui."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(DISTINCT message)
        FROM campaign_queue
        WHERE business_id = ? AND date(created_at) = date('now')
    """, (business_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def create_campaign(business_id: str, title: str, message: str, target: str, recipients_count: int) -> int:
    """Crée une nouvelle campagne et retourne son ID."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO campaigns (business_id, title, message, target, status, recipients_count) 
        VALUES (?, ?, ?, ?, 'Terminée', ?)
    """, (business_id, title, message, target, recipients_count))
    campaign_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return campaign_id

def get_campaigns_for_business(business_id: str) -> List[Dict]:
    """Récupère l'historique des campagnes d'un business."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM campaigns WHERE business_id = ? ORDER BY created_at DESC
    """, (business_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def enqueue_campaign(business_id: str, clients: List[Dict], message_template: str, title: str = "Campagne", target: str = "all") -> int:
    """Ajoute une campagne en masse dans la file d'attente. Retourne le nombre ajouté."""
    import json
    
    campaign_id = create_campaign(business_id, title, message_template, target, len(clients))
    
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    count = 0
    
    is_json = False
    try:
        json_data = json.loads(message_template)
        is_json = isinstance(json_data, dict) and 'template_name' in json_data
    except:
        pass

    for client in clients:
        prenom = client.get('client_name', 'Client').split()[0] if client.get('client_name') else 'Client'
        
        if is_json:
            client_data = json.loads(message_template)
            if 'variables' in client_data and isinstance(client_data['variables'], list):
                client_data['variables'] = [
                    str(v).replace('{prenom}', prenom) if isinstance(v, str) else v 
                    for v in client_data['variables']
                ]
            msg = json.dumps(client_data, ensure_ascii=False)
        else:
            msg = message_template.replace('{prenom}', prenom)
            
        cursor.execute(
            "INSERT INTO campaign_queue (business_id, wa_id, message, status, campaign_id) VALUES (?, ?, ?, 'pending', ?)",
            (business_id, client['wa_id'], msg, campaign_id)
        )
        count += 1
    conn.commit()
    conn.close()
    return count
