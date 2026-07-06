import os
import re

dashboard_routes_path = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\dashboard\routes.py'

with open(dashboard_routes_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Mise à jour de get_chat_history pour renvoyer le display_name et nom
old_get_chat = """    messages = conversation_repo.get_full_history(wa_id, biz_id, limit=50)
    is_human = business_repo.is_human_mode(biz_id, wa_id)
    client = client_repo.get_or_create(biz_id, wa_id)
    client_name = client['nom'] if client else wa_id

    return jsonify({
        'messages': messages,
        'is_human_mode': is_human,
        'client_name': client_name,
        'wa_id': wa_id
    })"""

new_get_chat = """    messages = conversation_repo.get_full_history(wa_id, biz_id, limit=50)
    is_human = business_repo.is_human_mode(biz_id, wa_id)
    client = client_repo.get_or_create(biz_id, wa_id)
    
    c_nom = client['nom'] if client and client['nom'] else ''
    c_disp = client['display_name'] if client and client['display_name'] else ''
    c_main = c_disp or c_nom or wa_id

    return jsonify({
        'messages': messages,
        'is_human_mode': is_human,
        'client_name': c_main,
        'client_real_name': c_nom,
        'client_display_name': c_disp,
        'wa_id': wa_id
    })"""

if "c_main = c_disp or c_nom or wa_id" not in content:
    content = content.replace(old_get_chat, new_get_chat)


# 2. Ajout de la route d'édition du profil client
edit_profile_route = """
@dashboard_bp.route('/admin/<biz_id>/chat/<wa_id>/profile', methods=['PUT'])
def update_chat_client_profile(biz_id, wa_id):
    if 'user_id' not in session or session['user_id'] != biz_id:
        return jsonify({'error': 'Non autorise'}), 403

    data = request.get_json() or {}
    nom = data.get('nom')
    display_name = data.get('display_name')

    try:
        if nom is not None:
            client_repo.update_name(biz_id, wa_id, nom.strip())
        if display_name is not None:
            client_repo.set_display_name(biz_id, wa_id, display_name.strip())
            
        return jsonify({"success": True, "message": "Profil mis à jour"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
"""

if "def update_chat_client_profile" not in content:
    # Insérer avant la route /admin/<biz_id>/chat/send
    content = content.replace("@dashboard_bp.route('/admin/<biz_id>/chat/send', methods=['POST'])", edit_profile_route + "\n\n@dashboard_bp.route('/admin/<biz_id>/chat/send', methods=['POST'])")

with open(dashboard_routes_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("dashboard_routes.py updated.")
