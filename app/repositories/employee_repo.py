"""
employee_repo.py — Accès aux données des employés (Multi-Employés PREMIUM).

Fournit les fonctions CRUD pour la table 'employees'.
Chaque employé est lié à un business et possède un nom et un poste.
"""

import sqlite3
from typing import List, Optional

from app.models.schema import get_db_path


def get_by_business(business_id: str) -> List[sqlite3.Row]:
    """Retourne la liste des employés actifs d'un business."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM employees WHERE business_id = ? AND actif = 1 ORDER BY nom ASC",
        (business_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_by_id(employee_id: int) -> Optional[sqlite3.Row]:
    """Retourne un employé par son identifiant."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees WHERE id = ?", (employee_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def add(business_id: str, nom: str, poste: str) -> int:
    """Ajoute un nouvel employé et retourne son id."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO employees (business_id, nom, poste, actif) VALUES (?, ?, ?, 1)",
        (business_id, nom, poste),
    )
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id


def update(employee_id: int, nom: str, poste: str) -> None:
    """Met à jour le nom et le poste d'un employé."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE employees SET nom = ?, poste = ? WHERE id = ?",
        (nom, poste, employee_id),
    )
    conn.commit()
    conn.close()


def deactivate(employee_id: int) -> None:
    """Désactive un employé (suppression douce) pour ne pas perdre l'historique."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("UPDATE employees SET actif = 0 WHERE id = ?", (employee_id,))
    conn.commit()
    conn.close()


def delete(employee_id: int) -> None:
    """Supprime définitivement un employé de la base."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
    conn.commit()
    conn.close()
