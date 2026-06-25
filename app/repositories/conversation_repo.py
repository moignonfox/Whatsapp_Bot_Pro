"""
conversation_repo.py — Acces aux donnees de l'historique des conversations.

Fournit les fonctions CRUD pour la table 'history'.
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

from app.models.schema import get_db_path


def save_message(wa_id: str, role: str, content: str, business_id: str = '', agent_id: int = None) -> None:
    """Enregistre un message dans l'historique.
    
    Args:
        wa_id: Numero WhatsApp du client.
        role: 'user', 'assistant' (bot IA), ou 'agent' (humain gerant).
        content: Contenu du message.
        business_id: Identifiant du business concerne.
        agent_id: ID de l'agent IA ayant repondu (optionnel).
    """
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO history (wa_id, role, content, timestamp, business_id, agent_id) VALUES (?, ?, ?, ?, ?, ?)",
        (wa_id, role, content, datetime.now(), business_id, agent_id),
    )
    conn.commit()
    conn.close()


def get_recent_history(wa_id: str, business_id: str, limit: int = 5) -> List[Dict[str, str]]:
    """
    Recupere les N derniers messages d'une conversation pour un business specifique.

    Retourne une liste de dicts [{"role": ..., "content": ...}]
    en ordre chronologique (du plus ancien au plus recent).
    """
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role, content FROM history WHERE wa_id = ? AND business_id = ? ORDER BY id DESC LIMIT ?",
        (wa_id, business_id, limit),
    )
    rows = cursor.fetchall()
    conn.close()

    # Inverser pour obtenir l'ordre chronologique
    rows.reverse()
    return [{"role": r, "content": c} for r, c in rows]


def get_monthly_ai_message_count(business_id: str) -> int:
    """
    Compte le nombre de messages envoyés par l'IA (role = 'assistant')
    pour un business donné sur le mois calendaire en cours.
    """
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM history
        WHERE business_id = ? 
          AND role = 'assistant' 
          AND strftime('%Y-%m', timestamp) = strftime('%Y-%m', 'now')
    """, (business_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0


def get_conversations_for_business(business_id: str) -> List[Dict]:
    """Recupere la liste des conversations uniques pour un business.
    
    Retourne pour chaque wa_id: le dernier message, le nom du client, et le timestamp.
    Ordonne par date du dernier message (plus recent en premier).
    """
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT h.wa_id,
               h.content AS last_message,
               h.role AS last_role,
               h.timestamp AS last_timestamp,
               COALESCE(c.nom, h.wa_id) AS client_name
        FROM history h
        LEFT JOIN clients c ON h.wa_id = c.wa_id AND c.business_id = ?
        WHERE h.business_id = ?
          AND h.id = (
              SELECT MAX(h2.id) FROM history h2 
              WHERE h2.wa_id = h.wa_id AND h2.business_id = ?
          )
        ORDER BY h.id DESC
    """, (business_id, business_id, business_id))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_full_history(wa_id: str, business_id: str, limit: int = 50) -> List[Dict]:
    """Recupere l'historique complet d'une conversation pour un business donne.
    
    Retourne les N derniers messages en ordre chronologique.
    Chaque message contient: role, content, timestamp.
    """
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("""
        SELECT role, content, timestamp 
        FROM history 
        WHERE wa_id = ? AND business_id = ?
        ORDER BY id DESC LIMIT ?
    """, (wa_id, business_id, limit))
    rows = cursor.fetchall()
    conn.close()
    
    rows.reverse()
    return [{"role": r, "content": c, "timestamp": t} for r, c, t in rows]

def get_pending_user_messages(wa_id: str, business_id: str) -> List[str]:
    """Récupère tous les messages envoyés par le client depuis la dernière réponse de l'assistant."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Trouver l'ID du dernier message de l'assistant pour cette conversation
    cursor.execute("""
        SELECT MAX(id) FROM history 
        WHERE wa_id = ? AND business_id = ? AND role = 'assistant'
    """, (wa_id, business_id))
    
    row = cursor.fetchone()
    last_assistant_id = row[0] if row and row[0] else 0
    
    # Récupérer tous les messages 'user' après cet ID
    cursor.execute("""
        SELECT content FROM history
        WHERE wa_id = ? AND business_id = ? AND role = 'user' AND id > ?
        ORDER BY id ASC
    """, (wa_id, business_id, last_assistant_id))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [r[0] for r in rows]

def get_unread_message_count_for_business(business_id: str) -> int:
    """Retourne le nombre total de messages non lus pour le business."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM history
        WHERE business_id = ? AND role = 'user' AND is_read = 0
    """, (business_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

def get_unread_message_counts_by_client(business_id: str) -> Dict[str, int]:
    """Retourne un dictionnaire {wa_id: unread_count} pour un business."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("""
        SELECT wa_id, COUNT(*) FROM history
        WHERE business_id = ? AND role = 'user' AND is_read = 0
        GROUP BY wa_id
    """, (business_id,))
    rows = cursor.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}

def mark_conversation_as_read(wa_id: str, business_id: str) -> None:
    """Marque tous les messages d'un client comme lus pour un business donné."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE history SET is_read = 1
        WHERE wa_id = ? AND business_id = ? AND role = 'user' AND is_read = 0
    """, (wa_id, business_id))
    conn.commit()
    conn.close()

def get_last_agent_id(wa_id: str, business_id: str) -> Optional[int]:
    """Retourne l'ID du dernier agent IA qui a répondu dans cette conversation.

    Utilisé par le routeur pour assurer la continuité en cas d'échec du routage.
    Retourne None si aucun agent n'a encore répondu.
    """
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("""
        SELECT agent_id FROM history
        WHERE wa_id = ? AND business_id = ? AND role = 'assistant' AND agent_id IS NOT NULL
        ORDER BY id DESC LIMIT 1
    """, (wa_id, business_id))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

