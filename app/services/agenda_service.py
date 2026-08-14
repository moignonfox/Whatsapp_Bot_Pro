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

def get_business_hours_context(business_info: dict, days: int = 14) -> str:
    """
    Construit le contexte unifié des horaires et de l'agenda.
    Ordre de priorité pour les horaires :
    1. Si businesses.horaires_json est rempli et valide -> Horaires globaux
    2. Sinon, on utilise les horaires des employés/tables
    Ajoute également le calendrier des prochains jours et les réservations existantes.
    """
    set_french_locale()
    now = datetime.now()
    business_id = business_info.get('id')
    
    # -- 1. Le calendrier des X prochains jours --
    calendar_lines = ["\n📅 CALENDRIER DES PROCHAINS JOURS (Utilise ceci pour trouver la date exacte) :"]
    for i in range(days):
        d = now + timedelta(days=i)
        suffix = " (Aujourd'hui)" if i == 0 else " (Demain)" if i == 1 else ""
        calendar_lines.append(f"- {d.strftime('%A %d %B %Y')} -> {d.strftime('%Y-%m-%d')}{suffix}")
    calendar_str = "\n".join(calendar_lines) + "\n"

    # -- 2. Horaires Globaux vs Employés --
    horaires_globaux_str = ""
    raw_biz_horaires = business_info.get('horaires_json')
    has_global_hours = False
    
    if raw_biz_horaires and raw_biz_horaires != '{}':
        try:
            h_data = json.loads(raw_biz_horaires)
            if any(h_data.values()): # Au moins un jour configuré
                has_global_hours = True
                jours = {'lun':'Lundi', 'mar':'Mardi', 'mer':'Mercredi', 'jeu':'Jeudi', 'ven':'Vendredi', 'sam':'Samedi', 'dim':'Dimanche'}
                lignes = []
                for k, v in jours.items():
                    plages = h_data.get(k, [])
                    if plages and len(plages) >= 2:
                        lignes.append(f"- {v} : {plages[0]} à {plages[1]}")
                    else:
                        lignes.append(f"- {v} : Fermé")
                horaires_globaux_str = (
                    "\nHORAIRES D'OUVERTURE DE L'ENTREPRISE :\n" 
                    + "\n".join(lignes) + 
                    "\n\n🚨 RÈGLE STRICTE SUR LES HORAIRES :\n"
                    "Tu ne DOIS SOUS AUCUN PRÉTEXTE accepter une commande ou réservation pour un jour ou une heure de fermeture.\n"
                    "Si le client demande un créneau fermé, refuse catégoriquement et propose un autre jour ouvert.\n"
                )
        except Exception:
            pass

    # -- 3. Agenda et réservations (employés/tables) --
    agenda_str = get_availability_context(business_id, days=days)
    
    # Si on a des horaires globaux, on garde l'agenda mais on évite la redondance d'erreur
    # Si on n'a pas d'horaires globaux, l'agenda (qui contient les horaires employés) fait foi.
    
    final_context = f"{calendar_str}\n"
    if has_global_hours:
        final_context += f"{horaires_globaux_str}\n"
    final_context += f"\n{agenda_str}\n"
    
    return final_context


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
    cursor.execute("SELECT business_type, horaires_json FROM businesses WHERE id = ?", (business_id,))
    biz_row = cursor.fetchone()
    biz_type = biz_row['business_type'] if biz_row else 'service'
    raw_biz_horaires = biz_row['horaires_json'] if biz_row else None
    
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
    
    # Injection stricte des horaires globaux de l'entreprise au cas où
    if raw_biz_horaires and raw_biz_horaires != '{}':
        try:
            h_data = json.loads(raw_biz_horaires)
            jours = {'lun':'Lundi', 'mar':'Mardi', 'mer':'Mercredi', 'jeu':'Jeudi', 'ven':'Vendredi', 'sam':'Samedi', 'dim':'Dimanche'}
            lignes = []
            for k, v in jours.items():
                plages = h_data.get(k, [])
                if plages and len(plages) >= 2:
                    lignes.append(f"- {v} : {plages[0]} à {plages[1]}")
                else:
                    lignes.append(f"- {v} : Fermé")
            context_lines.append(
                "\nHORAIRES GLOBAUX DE L'ENTREPRISE :\n" + "\n".join(lignes) + 
                "\n🚨 RÈGLE STRICTE SUR LES HORAIRES : Tu ne DOIS SOUS AUCUN PRÉTEXTE accepter une commande ou réservation pour un jour ou une heure de fermeture globale."
                "\nSi le client demande un créneau en dehors des heures, refuse catégoriquement et propose un autre moment ouvert."
            )
        except Exception:
            pass

    return "\n".join(context_lines)

def is_business_open_now(business_info: dict) -> bool:
    """Retourne True si l'entreprise est ouverte actuellement, False sinon.
    Si les horaires ne sont pas définis, on considère par défaut que c'est ouvert.
    Gère les horaires qui dépassent minuit (ex: 18:00 à 02:00).
    """
    raw_biz_horaires = business_info.get('horaires_json')
    if not raw_biz_horaires or raw_biz_horaires == '{}':
        return True
        
    try:
        h_data = json.loads(raw_biz_horaires)
        if not any(h_data.values()): # Aucun jour configuré
            return True
            
        now = datetime.now()
        # map weekday to key: Monday is 0
        jours_keys = ['lun', 'mar', 'mer', 'jeu', 'ven', 'sam', 'dim']
        current_day_key = jours_keys[now.weekday()]
        
        plages = h_data.get(current_day_key, [])
        
        def parse_time(t_str):
            parts = t_str.split(':')
            return int(parts[0]) * 60 + int(parts[1])
            
        current_minutes = now.hour * 60 + now.minute
        
        # 1. Vérifier la plage d'aujourd'hui
        if plages and len(plages) >= 2:
            start_minutes = parse_time(plages[0])
            end_minutes = parse_time(plages[1])
            
            if end_minutes < start_minutes:
                # Cas où ça ferme le lendemain (ex: 18:00 à 02:00)
                if current_minutes >= start_minutes or current_minutes <= end_minutes:
                    return True
            else:
                if start_minutes <= current_minutes <= end_minutes:
                    return True
                    
        # 2. Vérifier si on est dans la continuité du jour précédent qui a croisé minuit
        prev_day_key = jours_keys[(now.weekday() - 1) % 7]
        prev_plages = h_data.get(prev_day_key, [])
        if prev_plages and len(prev_plages) >= 2:
            p_start = parse_time(prev_plages[0])
            p_end = parse_time(prev_plages[1])
            if p_end < p_start: # La plage d'hier a croisé minuit
                if current_minutes <= p_end:
                    return True
                    
        return False
        
    except Exception as e:
        # En cas d'erreur de parsing, on ne bloque pas les commandes par sécurité
        return True
