"""
order_repo.py — Accès aux données des réservations / commandes.

Fournit les fonctions CRUD et les requêtes statistiques
pour la table 'reservations'.
"""

import sqlite3
from typing import Optional, Tuple, List, Dict, Any

from app.models.schema import get_db_path


def get_date_condition(period: str) -> str:
    """Retourne la condition SQL pour filtrer la période."""
    if period == 'today':
        return "date(created_at, 'localtime') = date('now', 'localtime')"
    elif period == 'week':
        return "created_at >= date('now', '-7 days')"
    elif period == 'month':
        return "created_at >= date('now', 'start of month')"
    elif period == 'semester':
        return "created_at >= date('now', '-6 months')"
    elif period == 'year':
        return "created_at >= date('now', 'start of year')"
    return "1=1" # 'all'


def save_reservation(
    biz_id: str,
    wa_id: str,
    details: str,
    priorite: str,
    montant: int = 0,
    date_heure_debut: str = None,
    employee_id: int = None
) -> int:
    """Crée une nouvelle réservation avec le statut 'En attente'. Retourne l'ID créé."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO reservations
           (business_id, wa_id, details, priorite, statut, montant, created_at, date_heure_debut, employee_id)
           VALUES (?, ?, ?, ?, 'En attente', ?, CURRENT_TIMESTAMP, ?, ?)""",
        (biz_id, wa_id, details, priorite, montant, date_heure_debut, employee_id),
    )
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id


def update_reservation(
    res_id: int,
    details: str,
    priorite: str,
    montant: int = 0,
    date_heure_debut: str = None,
    employee_id: int = None
) -> None:
    """Met à jour une réservation existante."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE reservations
           SET details = ?, priorite = ?, montant = ?, date_heure_debut = ?, employee_id = ?
           WHERE id = ?""",
        (details, priorite, montant, date_heure_debut, employee_id, res_id),
    )
    conn.commit()
    conn.close()


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


def get_last_for_user(wa_id: str, business_id: str) -> Optional[sqlite3.Row]:
    """Renvoie la dernière réservation d'un utilisateur pour un business donné.

    IMPORTANT : business_id est obligatoire pour éviter toute fuite de données
    entre tenants (multi-business). Ne jamais appeler sans ce paramètre.
    """
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM reservations WHERE wa_id = ? AND business_id = ? ORDER BY timestamp DESC LIMIT 1",
        (wa_id, business_id),
    )
    row = cursor.fetchone()
    conn.close()
    return row


def get_by_business(biz_id: str, period: str = 'today') -> List[sqlite3.Row]:
    """Renvoie toutes les réservations d'un business donné avec les infos client."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        f'''SELECT r.*, c.nom as client_name 
           FROM reservations r 
           LEFT JOIN clients c ON r.wa_id = c.wa_id AND r.business_id = c.business_id
           WHERE r.business_id = ? AND {get_date_condition(period)}
           ORDER BY r.timestamp DESC''',
        (biz_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_stats(biz_id: str, period: str = 'today') -> Dict[str, Any]:
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
        f"SELECT SUM(montant) FROM reservations WHERE business_id = ? AND (statut LIKE 'Prêt%' OR statut LIKE 'Livré%') AND {get_date_condition(period)}",
        (biz_id,),
    )
    ca = cursor.fetchone()[0] or 0

    cursor.execute(
        f"SELECT COUNT(*) FROM reservations WHERE business_id = ? AND {get_date_condition(period)}",
        (biz_id,),
    )
    total = cursor.fetchone()[0]

    cursor.execute(
        f"SELECT COUNT(*) FROM reservations WHERE business_id = ? AND statut LIKE 'Annulé%' AND {get_date_condition(period)}",
        (biz_id,),
    )
    annulations = cursor.fetchone()[0]

    conn.close()

    taux_annul = round((annulations / total * 100), 1) if total > 0 else 0
    return {"ca": ca, "total": total, "taux_annul": taux_annul}


def get_peak_hour(biz_id: str, period: str = 'today') -> str:
    """
    Calcule l'heure de pointe dynamique (heure avec le plus de réservations).
    Retourne une chaîne formatée, ex: '14h–15h'.
    Si pas assez de données, retourne 'N/A'.
    """
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute(
        f"""SELECT strftime('%H', created_at) as hour, COUNT(*) as cnt 
           FROM reservations 
           WHERE business_id = ? AND {get_date_condition(period)}
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


def get_daily_activity(biz_id: str, period: str = 'today') -> Tuple[List[str], List[int]]:
    """
    Activité quotidienne (ou horaire/mensuelle) pour un business.

    Retourne un tuple (labels, values) prêt pour un graphique.
    """
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    format_date = "'%d/%m'"
    if period == 'today':
        format_date = "'%H:00'"
    elif period in ('semester', 'year', 'all'):
        format_date = "'%m/%Y'"
        
    cursor.execute(
        f"""SELECT strftime({format_date}, created_at) as jour, COUNT(*)
           FROM reservations
           WHERE business_id = ? AND {get_date_condition(period)}
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
    if row:
        from app.services.crypto_service import decrypt_token
        row_dict = dict(row)
        row_dict['token_wa'] = decrypt_token(row_dict.get('token_wa', ''))
        return row_dict
    return None


def get_upcoming_reminders() -> List[sqlite3.Row]:
    """Récupère les réservations prévues dans moins de 65 minutes et dont le rappel n'a pas encore été envoyé."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    # On prend les réservations Confirmées (ou dont le statut ne commence pas par Annulé ou En attente)
    # entre maintenant et dans 65 minutes.
    cursor.execute("""
        SELECT r.id, r.wa_id, r.business_id, r.details, r.date_heure_debut, 
               b.whatsapp_phone_id, b.token_wa, b.owner_phone as manager_phone
        FROM reservations r
        JOIN businesses b ON r.business_id = b.id
        WHERE r.statut NOT LIKE 'Annulé%' 
          AND r.statut NOT LIKE 'En attente%'
          AND r.date_heure_debut IS NOT NULL
          AND r.rappel_envoye = 0
          AND r.date_heure_debut >= datetime('now')
          AND r.date_heure_debut <= datetime('now', '+65 minutes')
    """)
    rows = cursor.fetchall()
    conn.close()
    from app.services.crypto_service import decrypt_token
    result = []
    for row in rows:
        r = dict(row)
        r['token_wa'] = decrypt_token(r.get('token_wa', ''))
        result.append(r)
    return result

def mark_reminder_sent(res_id: int):
    """Marque une réservation comme ayant reçu son rappel."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("UPDATE reservations SET rappel_envoye = 1 WHERE id = ?", (res_id,))
    conn.commit()
    conn.close()


def get_orders_since(business_id: str, last_order_id: int, limit: int = 100) -> list:
    """Retourne toutes les commandes postérieures à last_order_id pour un business.

    Utilisé lors de la reconnexion d'un client pour lui envoyer les commandes
    créées ou modifiées pendant sa déconnexion.
    La limite à 100 évite un pic mémoire/réseau si le client est resté longtemps absent.

    Args:
        business_id: ID du business concerné.
        last_order_id: ID de la dernière commande reçue par le client.
        limit: Nombre maximum de commandes à retourner (défaut 100).

    Returns:
        Liste de dicts dans l'ordre chronologique.
    """
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        """SELECT id, wa_id, details, statut, priorite, montant, created_at
           FROM reservations
           WHERE business_id = ? AND id > ?
           ORDER BY id ASC
           LIMIT ?""",
        (business_id, last_order_id, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]
