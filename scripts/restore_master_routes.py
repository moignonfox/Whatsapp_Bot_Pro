import os

routes_path = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\master\routes.py'

block_to_add = """

@master_bp.route('/business/<biz_id>/change_status', methods=['POST'])
def change_business_status(biz_id):
    if not session.get('is_master'):
        return jsonify({"success": False, "error": "Non autoris\u00e9"}), 403
    
    data = request.get_json() or {}
    master_password = data.get('master_password')
    new_status = data.get('status')
    
    from werkzeug.security import check_password_hash
    if not master_password or not check_password_hash(current_app.config.get('MASTER_PASSWORD_HASH', ''), master_password):
        return jsonify({"success": False, "error": "Mot de passe incorrect"}), 401
    
    business = business_repo.get_by_id(biz_id)
    if not business:
        return jsonify({"success": False, "error": "Business introuvable"}), 404
        
    biz_dict = dict(business)
    now = datetime.now()
    
    import sqlite3
    from app.models.schema import get_db_path
    from app.services import whatsapp_disconnect_service
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    msg = "Statut mis \u00e0 jour."
    if new_status == 'archived':
        cursor.execute("UPDATE businesses SET status = 'archived', archived_at = ?, deletion_scheduled_at = NULL WHERE id = ?", (now.isoformat(), biz_id))
        try:
            whatsapp_disconnect_service.disconnect_whatsapp_number(biz_dict.get('token_wa'), biz_dict.get('whatsapp_phone_id'))
        except:
            pass
        msg = "Business archiv\u00e9."
    elif new_status == 'deleted':
        deletion_date = now + timedelta(days=7)
        cursor.execute("UPDATE businesses SET status = 'deleted', deletion_scheduled_at = ?, archived_at = NULL WHERE id = ?", (deletion_date.isoformat(), biz_id))
        msg = "Business supprim\u00e9 (programm\u00e9 dans 7 jours)."
    elif new_status == 'active':
        cursor.execute("UPDATE businesses SET status = 'active', archived_at = NULL, deletion_scheduled_at = NULL WHERE id = ?", (biz_id,))
        msg = "Business restaur\u00e9. Le g\u00e9rant doit reconnecter son num\u00e9ro WhatsApp."
    
    conn.commit()
    conn.close()
    
    flash(msg, 'success')
    return jsonify({"success": True, "message": msg})


@master_bp.route('/business/<biz_id>', methods=['DELETE'])
def delete_business_immediate(biz_id):
    if not session.get('is_master'):
        return jsonify({"success": False, "error": "Non autoris\u00e9"}), 403
    
    immediate = request.args.get('immediate') == 'true'
    if not immediate:
        return jsonify({"success": False, "error": "Param\u00e8tre immediate=true requis pour la purge"}), 400
        
    import sqlite3
    from app.models.schema import get_db_path
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("DELETE FROM businesses WHERE id = ?", (biz_id,))
    conn.commit()
    conn.close()
    
    flash("Le compte de test a \u00e9t\u00e9 purg\u00e9 d\u00e9finitivement.", "success")
    return jsonify({"success": True, "message": "Purg\u00e9"})

"""

with open(routes_path, 'a', encoding='utf-8') as f:
    f.write(block_to_add)

# Remplacer les caracteres non utf-8 dans tout le fichier au cas ou
with open(routes_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('Ǹ', 'é').replace('ǟ', 'é').replace('', 'é')

with open(routes_path, 'w', encoding='utf-8') as f:
    f.write(content)
