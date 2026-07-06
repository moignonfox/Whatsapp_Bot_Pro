"""
catalog_repo.py — Accès aux données du catalogue de produits.

Gère les produits ou services disponibles pour un business.
"""

import sqlite3
from typing import List, Optional

from app.models.schema import get_db_path


def add_product(biz_id: str, nom: str, prix: int, description: str = "", categorie: str = "Général", image_url: str = None, is_visible: int = 1, duree_minutes: int = 30) -> None:
    """Ajoute un produit au catalogue du business."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO products (business_id, categorie, nom, description, prix, disponible, image_url, is_visible, duree_minutes) VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?)",
        (biz_id, categorie, nom, description, prix, image_url, is_visible, duree_minutes)
    )
    conn.commit()
    conn.close()
    


def get_by_business(biz_id: str, only_available: bool = False) -> List[dict]:
    """Récupère le catalogue d'un business (caché en mémoire pour réduire les requêtes)."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if only_available:
        cursor.execute("SELECT * FROM products WHERE business_id = ? AND disponible = 1 ORDER BY categorie, nom", (biz_id,))
    else:
        cursor.execute("SELECT * FROM products WHERE business_id = ? ORDER BY categorie, nom", (biz_id,))
        
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_product(product_id: int, business_id: str) -> None:
    """Supprime définitivement un produit en vérifiant qu'il appartient au business."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ? AND business_id = ?", (product_id, business_id))
    conn.commit()
    conn.close()
    

def toggle_availability(product_id: int, business_id: str) -> None:
    """Active ou désactive un produit en vérifiant qu'il appartient au business."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE products SET disponible = CASE WHEN disponible = 1 THEN 0 ELSE 1 END WHERE id = ? AND business_id = ?",
        (product_id, business_id)
    )
    conn.commit()
    conn.close()
    

def toggle_visibility(product_id: int, business_id: str) -> None:
    """Active ou désactive la visibilité d'un produit sur la vitrine web."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE products SET is_visible = CASE WHEN is_visible = 1 THEN 0 ELSE 1 END WHERE id = ? AND business_id = ?",
        (product_id, business_id)
    )
    conn.commit()
    conn.close()
    

def update_product(product_id: int, business_id: str, nom: str, prix: int, description: str = "", categorie: str = "Général", image_url: str = None, is_visible: int = 1, duree_minutes: int = 30) -> None:
    """Met à jour un produit existant."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    if image_url is not None:
        cursor.execute(
            "UPDATE products SET categorie = ?, nom = ?, description = ?, prix = ?, image_url = ?, is_visible = ?, duree_minutes = ? WHERE id = ? AND business_id = ?",
            (categorie, nom, description, prix, image_url, is_visible, duree_minutes, product_id, business_id)
        )
    else:
        cursor.execute(
            "UPDATE products SET categorie = ?, nom = ?, description = ?, prix = ?, is_visible = ?, duree_minutes = ? WHERE id = ? AND business_id = ?",
            (categorie, nom, description, prix, is_visible, duree_minutes, product_id, business_id)
        )
    conn.commit()
    conn.close()
    