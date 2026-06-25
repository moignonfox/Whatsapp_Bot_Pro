"""
settings_repo.py — Accès aux paramètres globaux (Master).
"""

import sqlite3
from app.models.schema import get_db_path

def get_setting(key: str, default: str = None) -> str:
    """Récupère la valeur texte d'un paramètre global, ou retourne la valeur par défaut."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM global_settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    return default

def set_setting(key: str, value: str) -> None:
    """Met à jour ou crée un paramètre global."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO global_settings (key, value)
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
    """, (key, value))
    conn.commit()
    conn.close()

def get_all_settings() -> dict:
    """Récupère tous les paramètres globaux sous forme de dictionnaire."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM global_settings")
    rows = cursor.fetchall()
    conn.close()
    return {k: v for k, v in rows}
