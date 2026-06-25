"""
sector_repo.py — Accès aux données des secteurs d'activité (vocabulaire dynamique).
"""

import sqlite3
import json
from typing import List, Dict, Optional

from app.models.schema import get_db_path

def get_all_sectors() -> List[Dict]:
    """Renvoie la liste complète de tous les secteurs."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sectors ORDER BY name ASC")
    rows = cursor.fetchall()
    conn.close()
    
    sectors = []
    for row in rows:
        sector = dict(row)
        try:
            sector['vocab'] = json.loads(sector['vocab'])
        except Exception:
            sector['vocab'] = {}
        sectors.append(sector)
    return sectors

def get_by_id(sector_id: str) -> Optional[Dict]:
    """Renvoie le secteur par son ID, y compris le dictionnaire de vocabulaire."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sectors WHERE id = ?", (sector_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        sector = dict(row)
        try:
            sector['vocab'] = json.loads(sector['vocab'])
        except Exception:
            sector['vocab'] = {}
        return sector
    return None

def add_or_update(sector_id: str, name: str, vocab: dict) -> None:
    """Ajoute ou met à jour un secteur d'activité."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    vocab_str = json.dumps(vocab, ensure_ascii=False)
    
    # Vérifier si le secteur existe
    cursor.execute("SELECT id FROM sectors WHERE id = ?", (sector_id,))
    if cursor.fetchone():
        cursor.execute(
            "UPDATE sectors SET name = ?, vocab = ? WHERE id = ?",
            (name, vocab_str, sector_id),
        )
    else:
        cursor.execute(
            "INSERT INTO sectors (id, name, vocab) VALUES (?, ?, ?)",
            (sector_id, name, vocab_str),
        )
    conn.commit()
    conn.close()
