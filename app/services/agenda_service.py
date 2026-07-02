import json
from datetime import datetime, timedelta
import sqlite3
import locale

def set_french_locale():
    try:
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_TIME, 'fr_FR')
        except:
            pass

from app.models.schema import get_db_path

def get_availability_context(business_id: str, days: int = 7) -> str:
    """
    Génère un texte décrivant les disponibilités des employés et les réservations existantes
    pour les X prochains jours, à injecter dans le prompt de l'IA.
    """
    set_french_locale()
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Récupérer le type d'entreprise et les employés actifs (ou tables)
    cursor.execute("SELECT business_type FROM businesses WHERE id = ?", (business_id,))
    biz_row = cursor.fetchone()
    biz_type = biz_row['business_type'] if biz_row else 'service'
    
    is_restaurant = (biz_type == 'restaurant')

    cursor.execute("SELECT id, nom, horaires_json FROM employees WHERE business_id = ? AND actif = 1", (business_id,))
    employees = cursor.fetchall()
    
    if not employees:
        conn.close()
        return "Aucune ressource (employé ou table) configurée pour les réservations."

    # 2. Récupérer les réservations futures (avec date_heure_debut)
    now = datetime.now()
    end_date = now + timedelta(days=days)
    
    cursor.execute('''
        SELECT id, details, date_heure_debut, employee_id, statut 
        FROM reservations 
        WHERE business_id = ? 
        AND date_heure_debut IS NOT NULL
        AND date_heure_debut >= ? 
        AND date_heure_debut <= ?
        AND statut != 'Annulé'
        ORDER BY date_heure_debut ASC
    ''', (business_id, now.strftime('%Y-%m-%d %H:%M:%S'), end_date.strftime('%Y-%m-%d %H:%M:%S')))
    reservations = cursor.fetchall()
    conn.close()

    # 3. Construire le contexte texte
    context_lines = []
    context_lines.append(f"=== CONTEXTE AGENDA (Aujourd'hui : {now.strftime('%A %d %B %Y, %H:%M:%S')}) ===")
    
    label_ressources = "TABLES/ZONES DISPONIBLES ET HORAIRES" if is_restaurant else "HORAIRES DES EMPLOYÉS"
    context_lines.append(f"\n[{label_ressources}]")
    for emp in employees:
        try:
            horaires = json.loads(emp['horaires_json'] or '{}')
            horaires_str = ", ".join([f"{jour}: {h[0]}-{h[1]}" for jour, h in horaires.items() if h and len(h) == 2])
            if not horaires_str:
                horaires_str = "Aucun horaire défini"
            context_lines.append(f"- {emp['nom']} (ID: {emp['id']}) -> {horaires_str}")
        except:
            context_lines.append(f"- {emp['nom']} (ID: {emp['id']}) -> Erreur de lecture des horaires")

    context_lines.append("\n[RÉSERVATIONS DÉJÀ PLANIFIÉES (CRÉNEAUX OCCUPÉS)]")
    if not reservations:
        context_lines.append("Aucune réservation pour les prochains jours. L'agenda est totalement libre !")
    else:
        for res in reservations:
            emp_name = next((e['nom'] for e in employees if e['id'] == res['employee_id']), f"Ressource inconnue (ID {res['employee_id']})")
            context_lines.append(f"- {res['date_heure_debut']} | {emp_name} | Statut: {res['statut']} | (Détails: {res['details'][:30]}...)")
            
    context_lines.append("\n=== RÈGLES POUR PROPOSER UN CRÉNEAU ===")
    context_lines.append(f"1. Ne propose QUE des horaires inclus dans les [{label_ressources}] pour le jour demandé.")
    context_lines.append("2. Vérifie qu'il n'y a pas déjà une réservation à cette heure-là dans [RÉSERVATIONS DÉJÀ PLANIFIÉES]. (Prends en compte la durée de la prestation/repas)")
    context_lines.append("3. Si le client te demande tes disponibilités pour une date, donne-lui les créneaux libres en te basant sur ces horaires et les réservations déjà planifiées.")
    
    return "\n".join(context_lines)
