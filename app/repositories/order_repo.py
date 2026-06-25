"""
order_repo.py — Accès aux données des réservations / commandes.

Fournit les fonctions CRUD et les requêtes statistiques
pour la table 'reservations'.
"""

import sqlite3
from typing import Optional, Tuple, List, Dict, Any

from app.models.schema import get_db_path


def save_reservation(
    biz_id: str,
    wa_id: str,
    details: str,
    priorite: str,
    montant: int = 0,
) -> int:
    """Crée une nouvelle réservation avec le statut 'En attente'. Retourne l'ID créé."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO reservations
           (business_id, wa_id, details, priorite, statut, montant, created_at)
           VALUES (?, ?, ?, ?, 'En attente', ?, CURRENT_TIMESTAMP)""",
        (biz_id, wa_id, details, priorite, montant),
    )
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id


def get_all_reservations() -> List[sqlite3.Row]:
    """Renvoie toutes les réservations, les plus récentes en premier."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reservations ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows


def update_status(res_id: int, new_status: str) -> Optional[str]:
    """
    Met à jour le statut d'une réservation.

    Retourne le wa_id du client concerné, ou None si la réservation
    n'existe pas.
    """
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE reservations SET statut = ? WHERE id = ?",
        (new_status, res_id),
    )
    conn.commit()

    cursor.execute("SELECT wa_id FROM reservations WHERE id = ?", (res_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def get_last_for_user(wa_id: str) -> Optional[sqlite3.Row]:
    """Renvoie la dernière réservation d'un utilisateur donné."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM reservations WHERE wa_id = ? ORDER BY timestamp DESC LIMIT 1",
        (wa_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return row


def get_by_business(biz_id: str) -> List[sqlite3.Row]:
    """Renvoie toutes les réservations d'un business donné."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM reservations WHERE business_id = ? ORDER BY timestamp DESC",
        (biz_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_stats(biz_id: str) -> Dict[str, Any]:
    """
    Calcule les statistiques clés d'un business.

    Retourne un dict avec :
      - ca        : chiffre d'affaires (hors annulées)
      - total     : nombre total de réservations
      - taux_annul: pourcentage d'annulations
    """
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    cursor.execute(
        "SELECT SUM(montant) FROM reservations WHERE business_id = ? AND statut NOT LIKE 'Annulé%'",
        (biz_id,),
    )
    ca = cursor.fetchone()[0] or 0

    cursor.execute(
        "SELECT COUNT(*) FROM reservations WHERE business_id = ?",
        (biz_id,),
    )
    total = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM reservations WHERE business_id = ? AND statut LIKE 'Annulé%'",
        (biz_id,),
    )
    annulations = cursor.fetchone()[0]

    conn.close()

    taux_annul = round((annulations / total * 100), 1) if total > 0 else 0
    return {"ca": ca, "total": total, "taux_annul": taux_annul}


def get_peak_hour(biz_id: str) -> str:
    """
    Calcule l'heure de pointe dynamique (heure avec le plus de réservations).
    Retourne une chaîne formatée, ex: '14h–15h'.
    Si pas assez de données, retourne 'N/A'.
    """
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute(
        """SELECT strftime('%H', created_at) as hour, COUNT(*) as cnt 
           FROM reservations 
           WHERE business_id = ? 
           GROUP BY hour 
           ORDER BY cnt DESC 
           LIMIT 1""",
        (biz_id,),
    )
    row = cursor.fetchone()
    conn.close()

    if row and row[0]:
        hour = int(row[0])
        next_hour = (hour + 1) % 24
        return f"{hour:02d}h–{next_hour:02d}h"
    return "N/A"


def get_daily_activity(biz_id: str) -> Tuple[List[str], List[int]]:
    """
    Activité quotidienne des 7 derniers jours pour un business.

    Retourne un tuple (labels, values) prêt pour un graphique.
    """
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute(
        """SELECT strftime('%d/%m', created_at) as jour, COUNT(*)
           FROM reservations
           WHERE business_id = ? AND created_at >= date('now', '-7 days')
           GROUP BY jour
           ORDER BY created_at ASC""",
        (biz_id,),
    )
    rows = cursor.fetchall()
    conn.close()

    labels = [r[0] for r in rows]
    values = [r[1] for r in rows]
    return labels, values


def get_res_info(res_id: int) -> Optional[sqlite3.Row]:
    """
    Récupère les informations d'une réservation enrichies
    avec les données du business associé.

    Utile pour envoyer des notifications WhatsApp au client.
    """
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        """SELECT r.wa_id, r.business_id, r.statut,
                  b.token_wa, b.whatsapp_phone_id,
                  b.msg_confirm, b.msg_cancel, b.msg_ready
           FROM reservations r
           JOIN businesses b ON r.business_id = b.id
           WHERE r.id = ?""",
        (res_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return row
