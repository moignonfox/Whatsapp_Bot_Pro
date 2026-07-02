import sqlite3
from datetime import datetime
from collections import Counter
from app.models.schema import get_db_path
from app.services.whatsapp_service import send_text_message

def parse_top_vente(details_list):
    """Extrait rudimentairement le produit le plus vendu des details."""
    counter = Counter()
    for details in details_list:
        lines = details.split('\n')
        for line in lines:
            if ' - ' in line and ' FCFA' in line:
                parts = line.split(' - ')
                if len(parts) >= 2:
                    nom = parts[0].strip()
                    # Si format "Nom - ... x Quantite"
                    if ' x ' in parts[1]:
                        try:
                            qte = int(parts[1].split(' x ')[-1].strip())
                        except:
                            qte = 1
                    else:
                        qte = 1
                    counter[nom] += qte
    if counter:
        top_item = counter.most_common(1)[0]
        return f"{top_item[0]} ({top_item[1]} commandes)"
    return "Aucune"

def generate_daily_report_for_business(biz_id: str, owner_phone: str, biz_nom: str, token_wa: str, whatsapp_phone_id: str):
    """Génère et envoie le rapport quotidien pour un business spécifique."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    today_str = datetime.now().strftime('%Y-%m-%d')
    date_formatted = datetime.now().strftime('%d/%m/%Y')

    # 1. Chiffre d'affaires & Commandes
    cursor.execute("""
        SELECT montant, statut, details 
        FROM reservations 
        WHERE business_id = ? 
          AND date(timestamp) = ?
    """, (biz_id, today_str))
    orders = cursor.fetchall()

    revenus = 0
    commandes_validees = 0
    details_list = []

    for order in orders:
        statut = order['statut'] or ''
        if statut != 'En attente' and 'Annulé' not in statut:
            commandes_validees += 1
            if statut.startswith('Prêt') or statut.startswith('Livré'):
                revenus += order['montant'] or 0
            if order['details']:
                details_list.append(order['details'])

    top_vente = parse_top_vente(details_list)

    # 2. Statistiques IA
    cursor.execute("""
        SELECT role, wa_id 
        FROM history 
        WHERE business_id = ? 
          AND date(timestamp) = ?
    """, (biz_id, today_str))
    history = cursor.fetchall()
    conn.close()

    messages_traites = sum(1 for h in history if h['role'] == 'assistant')
    clients_renseignes = len(set(h['wa_id'] for h in history))
    interventions_manuelles = sum(1 for h in history if h['role'] == 'agent')

    # Si rien ne s'est passé, on ne spamme pas le gérant
    if clients_renseignes == 0 and commandes_validees == 0:
        return 

    report_text = f"📊 *Bilan de la journée - {biz_nom}*\n"
    report_text += f"📅 {date_formatted}\n\n"
    report_text += f"Bonsoir patron ! Voici le résumé du travail de votre assistant IA aujourd'hui :\n\n"
    report_text += f"💰 *Revenus générés :* {revenus:,} FCFA\n".replace(',', ' ')
    report_text += f"📦 *Commandes validées :* {commandes_validees}\n\n"
    report_text += f"🤖 *Travail de l'IA :*\n"
    report_text += f"  - {messages_traites} messages traités\n"
    report_text += f"  - {clients_renseignes} clients renseignés\n"
    report_text += f"  - {interventions_manuelles} intervention(s) manuelle(s) requise(s)\n\n"
    report_text += f"⭐ *Top vente du jour :* {top_vente}\n\n"
    report_text += f"Excellente soirée, votre bot reste de garde cette nuit ! 🌙"

    # Envoi via whatsapp_service
    send_text_message(owner_phone, report_text, whatsapp_phone_id, token_wa)


def generate_all_daily_reports():
    """Tâche Cron : Boucle sur tous les business et envoie le rapport s'ils ont un owner_phone."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, nom, owner_phone, token_wa, whatsapp_phone_id FROM businesses WHERE is_active = 1")
    businesses = cursor.fetchall()
    conn.close()

    for biz in businesses:
        owner_phone = biz['owner_phone']
        if owner_phone and owner_phone.strip():
            # Nettoyage rudimentaire du numéro (retirer les espaces, + etc)
            clean_phone = ''.join(c for c in owner_phone if c.isdigit())
            if clean_phone.startswith('00'):
                clean_phone = clean_phone[2:]
            if len(clean_phone) == 8:
                clean_phone = f"228{clean_phone}"
                
            if clean_phone:
                generate_daily_report_for_business(biz['id'], clean_phone, biz['nom'], biz['token_wa'], biz['whatsapp_phone_id'])
