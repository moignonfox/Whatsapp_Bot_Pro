from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
import sqlite3
from datetime import date

from app.api import api_bp
from app.models.schema import get_db_path

@api_bp.route('/stats/today', methods=['GET'])
@jwt_required()
def get_today_stats():
    company_id = get_jwt_identity()
    period = request.args.get('period', 'today')
    
    from app.repositories.order_repo import get_date_condition
    date_cond = get_date_condition(period)
    
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Revenue (Seulement Prêt et Livré, comme option A)
    cursor.execute(
        f"""SELECT SUM(montant) 
           FROM reservations 
           WHERE business_id = ? 
             AND {date_cond}
             AND (statut LIKE 'Prêt%' OR statut LIKE 'Livré%')""",
        (company_id,)
    )
    revenue = cursor.fetchone()[0] or 0
    
    # Commandes validées (Confirmé + Prêt/Livré = tout sauf Annulé et En attente)
    cursor.execute(
        f"""SELECT COUNT(*) 
           FROM reservations 
           WHERE business_id = ? 
             AND {date_cond}
             AND statut NOT LIKE 'Annulé%'
             AND statut NOT LIKE 'En attente%'""",
        (company_id,)
    )
    orders_count = cursor.fetchone()[0] or 0
    
    # Annulations
    cursor.execute(
        f"""SELECT COUNT(*) 
           FROM reservations 
           WHERE business_id = ? 
             AND {date_cond}
             AND statut LIKE 'Annulé%'""",
        (company_id,)
    )
    cancellations = cursor.fetchone()[0] or 0
    
    # Commandes en attente (Global, peu importe la date)
    cursor.execute(
        """SELECT COUNT(*) 
           FROM reservations 
           WHERE business_id = ? 
             AND statut LIKE 'En attente%'""",
        (company_id,)
    )
    pending_count = cursor.fetchone()[0] or 0
    
    conn.close()

    # Génération du label dynamique
    import datetime
    today = datetime.date.today()
    if period == 'today':
        period_label = "Aujourd'hui"
    elif period == 'week':
        period_label = "7 derniers jours"
    elif period == 'month':
        months = ["", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
        period_label = f"{months[today.month]} {today.year}"
    elif period == 'semester':
        period_label = "6 derniers mois"
    elif period == 'year':
        period_label = f"Année {today.year}"
    else:
        period_label = "Toutes les dates"

    return jsonify({
        "success": True,
        "date": today.isoformat(),
        "period_label": period_label,
        "orders_count": orders_count,
        "revenue": revenue,
        "cancellations": cancellations,
        "pending_count": pending_count
    }), 200
