import re

filepath = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\master\routes.py'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Ajouter r\u00e9cup\u00e9ration des notifications avant le render_template
insertion = """
    import sqlite3
    from app.models.schema import get_db_path
    
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notifications_master ORDER BY created_at DESC LIMIT 50")
    master_notifications = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT COUNT(*) FROM notifications_master WHERE is_read = 0")
    master_pending_count = cursor.fetchone()[0]
    conn.close()
    
    response = make_response(render_template('master/dashboard.html', businesses=businesses_list, sectors=sectors, metrics=metrics, global_settings=global_settings, master_notifications=master_notifications, master_pending_count=master_pending_count))"""

content = re.sub(
    r"response = make_response\(render_template\('master/dashboard\.html', businesses=businesses_list, sectors=sectors, metrics=metrics, global_settings=global_settings\)\)",
    insertion,
    content
)

# Ajouter la route /notifications/mark-read
new_route = """

@master_bp.route('/notifications/mark-read', methods=['POST'])
def mark_notifications_read():
    if not session.get('is_master'):
        return jsonify({"success": False}), 403
    import sqlite3
    from app.models.schema import get_db_path
    conn = sqlite3.connect(get_db_path())
    conn.cursor().execute("UPDATE notifications_master SET is_read = 1 WHERE is_read = 0")
    conn.commit()
    conn.close()
    return jsonify({"success": True})
"""

content += new_route

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
