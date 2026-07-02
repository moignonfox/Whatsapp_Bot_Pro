"""
client_repo.py — Accès aux données des clients.

Fournit les fonctions CRUD pour la table 'clients'.
"""

import sqlite3
from typing import Optional

from app.models.schema import get_db_path


def get_or_create(business_id: str, wa_id: str, nom_par_defaut: str = None) -> sqlite3.Row:
    """
    Récupère un client existant ou en crée un nouveau.

    Retourne toujours la ligne du client.
    """
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM clients WHERE business_id = ? AND wa_id = ?", (business_id, wa_id))
    row = cursor.fetchone()

    if row is None:
        if nom_par_defaut is None:
            # Create a more user-friendly default name instead of just 'Client'
            nom_par_defaut = f"Client ...{wa_id[-4:]}" if len(wa_id) >= 4 else "Client Inconnu"
            
        cursor.execute(
            "INSERT INTO clients (business_id, wa_id, nom) VALUES (?, ?, ?)",
            (business_id, wa_id, nom_par_defaut),
        )
        conn.commit()
        cursor.execute("SELECT * FROM clients WHERE business_id = ? AND wa_id = ?", (business_id, wa_id))
        row = cursor.fetchone()

    conn.close()
    return row


def update_name(business_id: str, wa_id: str, nom: str) -> None:
    """Met à jour le nom d'un client existant ou le crée s'il n'existe pas."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE clients SET nom = ? WHERE business_id = ? AND wa_id = ?",
        (nom, business_id, wa_id),
    )
    if cursor.rowcount == 0:
        cursor.execute(
            "INSERT INTO clients (business_id, wa_id, nom) VALUES (?, ?, ?)",
            (business_id, wa_id, nom)
        )
    conn.commit()
    conn.close()
