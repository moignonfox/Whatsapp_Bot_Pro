"""Service de Notifications Master"""
import sqlite3
from app.models.schema import get_db_path
import logging

logger = logging.getLogger(__name__)

def create_master_notification(type_notif: str, title: str, message: str, business_id: str = None):
    """
    Crée une notification Master et l'émet en temps réel.
    """
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO notifications_master (type, title, message, business_id)
        VALUES (?, ?, ?, ?)
    ''', (type_notif, title, message, business_id))
    
    notif_id = cursor.lastrowid
    
    # On récupère le nombre de notifications non lues pour l'envoyer dans le socket
    cursor.execute('SELECT COUNT(*) FROM notifications_master WHERE is_read = 0')
    count = cursor.fetchone()[0]
    
    conn.commit()
    conn.close()
    
    # Emission Socket.IO
    try:
        from app import socketio
        socketio.emit('master_notification', {
            'id': notif_id,
            'type': type_notif,
            'title': title,
            'message': message,
            'business_id': business_id,
            'count': count
        }, room='master')
    except Exception as e:
        logger.error(f"Erreur d'émission notification Master: {e}")

def get_unread_notifications(limit=10):
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM notifications_master 
        WHERE is_read = 0 
        ORDER BY created_at DESC 
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def mark_as_read(notif_id):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute('UPDATE notifications_master SET is_read = 1 WHERE id = ?', (notif_id,))
    conn.commit()
    conn.close()

def mark_all_as_read():
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute('UPDATE notifications_master SET is_read = 1 WHERE is_read = 0')
    conn.commit()
    conn.close()
