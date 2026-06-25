import sqlite3
from typing import List, Dict, Optional
from app.models.schema import get_db_path

def enqueue_message(business_id: str, wa_id: str, message: str) -> None:
    """Ajoute un message dans la file d'attente d'envoi."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO campaign_queue (business_id, wa_id, message, status) VALUES (?, ?, ?, 'pending')",
        (business_id, wa_id, message)
    )
    conn.commit()
    conn.close()

def get_next_pending_message() -> Optional[Dict]:
    """Récupère le prochain message en attente (FIFO)."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, business_id, wa_id, message 
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

def mark_message_status(msg_id: int, status: str) -> None:
    """Met à jour le statut d'un message dans la file ('sent', 'failed')."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("UPDATE campaign_queue SET status = ? WHERE id = ?", (status, msg_id))
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
