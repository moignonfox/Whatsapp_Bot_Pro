"""
agent_repo.py — Accès aux données des agents IA (Multi-Employé Agent IA).
"""

import sqlite3
import json
from typing import List, Optional, Dict, Any

from app.models.schema import get_db_path


def get_by_business(business_id: str) -> List[sqlite3.Row]:
    """Retourne la liste des agents IA actifs d'un business."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM ai_agents WHERE business_id = ? AND is_active = 1",
        (business_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_by_id(agent_id: int) -> Optional[sqlite3.Row]:
    """Retourne un agent par son identifiant."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ai_agents WHERE id = ?", (agent_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def add(business_id: str, name: str, role: str, system_prompt: str, intent_keywords: str, agent_settings: Dict[str, Any]) -> int:
    """Ajoute un nouvel agent IA."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    settings_json = json.dumps(agent_settings)
    cursor.execute(
        "INSERT INTO ai_agents (business_id, name, role, system_prompt, intent_keywords, agent_settings_json, is_active) VALUES (?, ?, ?, ?, ?, ?, 1)",
        (business_id, name, role, system_prompt, intent_keywords, settings_json),
    )
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id


def update(agent_id: int, business_id: str, name: str, role: str, system_prompt: str, intent_keywords: str, agent_settings: Dict[str, Any]) -> None:
    """Met à jour un agent IA en vérifiant qu'il appartient au business."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    settings_json = json.dumps(agent_settings)
    cursor.execute(
        "UPDATE ai_agents SET name = ?, role = ?, system_prompt = ?, intent_keywords = ?, agent_settings_json = ? WHERE id = ? AND business_id = ?",
        (name, role, system_prompt, intent_keywords, settings_json, agent_id, business_id),
    )
    conn.commit()
    conn.close()

def get_agent_stats(business_id: str) -> Dict[int, Dict[str, Any]]:
    """Retourne les statistiques par agent pour un business."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Nombre de messages traités par agent (assistant seulement)
    cursor.execute('''
        SELECT agent_id, COUNT(*) as msg_count
        FROM history
        WHERE business_id = ? AND role = 'assistant' AND agent_id IS NOT NULL
        GROUP BY agent_id
    ''', (business_id,))
    
    stats = {}
    for row in cursor.fetchall():
        agent_id, msg_count = row
        stats[agent_id] = {
            'messages_handled': msg_count
        }
        
    conn.close()
    return stats

def deactivate(agent_id: int, business_id: str) -> None:
    """Désactive un agent IA (soft delete) en vérifiant l'appartenance au business."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("UPDATE ai_agents SET is_active = 0 WHERE id = ? AND business_id = ?", (agent_id, business_id))
    conn.commit()
    conn.close()


def delete(agent_id: int) -> None:
    """Supprime définitivement un agent IA."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ai_agents WHERE id = ?", (agent_id,))
    conn.commit()
    conn.close()
