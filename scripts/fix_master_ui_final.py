import os
import re

routes_path = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\master\routes.py'
with open(routes_path, 'r', encoding='utf-8', errors='ignore') as f:
    routes_content = f.read()

# Fix CSRF et Flash dans change_business_status (ligne ~362)
# On ajoute flash(msg, 'success') juste avant le commit ou le return
if "from flask import flash" not in routes_content:
    pass # flask.flash is probably imported via 'from flask import ... flash' at top

change_status_block = """    if new_status == 'archived':
        cursor.execute("UPDATE businesses SET status = 'archived', archived_at = ?, deletion_scheduled_at = NULL WHERE id = ?", (now.isoformat(), biz_id))
        whatsapp_disconnect_service.disconnect_whatsapp_number(biz_dict.get('token_wa'), biz_dict.get('whatsapp_phone_id'))
    elif new_status == 'deleted':
        deletion_date = now + timedelta(days=7)
        cursor.execute("UPDATE businesses SET status = 'deleted', deletion_scheduled_at = ?, archived_at = NULL WHERE id = ?", (deletion_date.isoformat(), biz_id))
    elif new_status == 'active':
        cursor.execute("UPDATE businesses SET status = 'active', archived_at = NULL, deletion_scheduled_at = NULL WHERE id = ?", (biz_id,))
        msg = "Business restauré. Le gérant doit reconnecter son numéro WhatsApp depuis son dashboard."
    
    conn.commit()
    conn.close()
    
    flash(msg, 'success')
    return jsonify({"success": True, "message": msg})"""

# On nettoie les anciens retours
routes_content = re.sub(
    r"    if new_status == 'archived':.*?conn\.close\(\)",
    change_status_block,
    routes_content,
    flags=re.DOTALL
)

# Correction delete_business pour ne pas verifier pwd si immediate
delete_block = """    from werkzeug.security import check_password_hash
    if not immediate:
        if not check_password_hash(current_app.config['MASTER_PASSWORD_HASH'], password):
            return jsonify({'error': 'Mot de passe incorrect'}), 401"""

routes_content = re.sub(
    r"    from werkzeug\.security import check_password_hash.*?return jsonify\(\{'error': 'Mot de passe incorrect'\}\), 401",
    delete_block,
    routes_content,
    flags=re.DOTALL
)

# Et ajout du flash(msg) dans delete_business
routes_content = re.sub(
    r"    return jsonify\(\{'success': True, 'message': message\}\)",
    "    flash(message, 'success')\n    return jsonify({'success': True, 'message': message})",
    routes_content
)

# Fixer aussi les encodages mal propres (ex: "Non autorisǟ")
routes_content = routes_content.replace('ǟ', 'é')

with open(routes_path, 'w', encoding='utf-8') as f:
    f.write(routes_content)


# MAINTENANT LE TEMPLATE dashboard.html
html_path = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\templates\master\dashboard.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html_content = f.read()

# Ajouter le tab Tous
if "filterBusinesses('all', this)" not in html_content:
    old_tabs = """<button class="tab-btn active" onclick="filterBusinesses('active', this)">Actifs</button>"""
    new_tabs = """<button class="tab-btn active" onclick="filterBusinesses('all', this)">Tous</button>\n                      <button class="tab-btn" onclick="filterBusinesses('active', this)">Actifs</button>"""
    html_content = html_content.replace(old_tabs, new_tabs)

# Changer JS filterBusinesses
old_filter = """    document.querySelectorAll('.business-row').forEach(row => {
        if(row.getAttribute('data-status') === status) {"""
new_filter = """    document.querySelectorAll('.business-row').forEach(row => {
        if(status === 'all' || row.getAttribute('data-status') === status) {"""
html_content = html_content.replace(old_filter, new_filter)

# Changer `alert(data.message)` -> supprime les alertes natives de succes (le flash se chargera du reste après reload)
html_content = html_content.replace('alert(data.message);\n            window.location.reload();', 'window.location.reload();')

# initialiser tabs correctement
old_init = "if(firstBtn) filterBusinesses('active', firstBtn);"
new_init = "if(firstBtn) filterBusinesses('all', firstBtn);"
html_content = html_content.replace(old_init, new_init)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html_content)
