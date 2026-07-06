import sys
import re

file_path = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\master\routes.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Ajouter les imports nǸcessaires
if 'from datetime import datetime, timedelta' not in content:
    content = content.replace("import json\n", "import json\nfrom datetime import datetime, timedelta\nfrom app.services import whatsapp_disconnect_service\n")

# Ajouter les routes
routes_to_add = """
@master_bp.route('/business/<biz_id>/change_status', methods=['POST'])
def change_business_status(biz_id):
    if not session.get('is_master'):
        return jsonify({"success": False, "error": "Non autorisǟ"}), 403
    
    data = request.get_json() or {}
    master_password = data.get('master_password')
    new_status = data.get('status')
    
    from werkzeug.security import check_password_hash
    if not master_password or not check_password_hash(current_app.config['MASTER_PASSWORD_HASH'], master_password):
        return jsonify({"success": False, "error": "Mot de passe incorrect"}), 401
    
    business = business_repo.get_by_id(biz_id)
    if not business:
        return jsonify({"success": False, "error": "Business introuvable"}), 404
        
    biz_dict = dict(business)
    now = datetime.now()
    
    import sqlite3
    from app.models.schema import get_db_path
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    msg = "Statut mis ǟ jour."
    if new_status == 'archived':
        cursor.execute("UPDATE businesses SET status = 'archived', archived_at = ?, deletion_scheduled_at = NULL WHERE id = ?", (now.isoformat(), biz_id))
        whatsapp_disconnect_service.disconnect(biz_dict.get('token_wa'), biz_dict.get('whatsapp_phone_id'))
    elif new_status == 'deleted':
        deletion_date = now + timedelta(days=7)
        cursor.execute("UPDATE businesses SET status = 'deleted', deletion_scheduled_at = ?, archived_at = NULL WHERE id = ?", (deletion_date.isoformat(), biz_id))
    elif new_status == 'active':
        cursor.execute("UPDATE businesses SET status = 'active', archived_at = NULL, deletion_scheduled_at = NULL WHERE id = ?", (biz_id,))
        msg = "Business restaurǟ. Le gǟrant doit reconnecter son numǟro WhatsApp depuis son dashboard."
    
    conn.commit()
    conn.close()
        
    return jsonify({"success": True, "message": msg})


@master_bp.route('/business/<biz_id>', methods=['DELETE'])
def delete_business_immediate(biz_id):
    if not session.get('is_master'):
        return jsonify({"success": False, "error": "Non autorisǟ"}), 403
    
    immediate = request.args.get('immediate') == 'true'
    if not immediate:
        return jsonify({"success": False, "error": "Paramǟtre immediate=true requis pour la suppression immǟdiate"}), 400
        
    import sqlite3
    from app.models.schema import get_db_path
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("DELETE FROM businesses WHERE id = ?", (biz_id,))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "Business immǟdiatement purgǟ."})
"""

if 'change_business_status' not in content:
    content += "\n" + routes_to_add

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
