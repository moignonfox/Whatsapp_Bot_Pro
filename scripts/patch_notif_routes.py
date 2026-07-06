import re

filepath = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\master\routes.py'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

new_routes = """
@master_bp.route('/notifications/<int:notif_id>', methods=['DELETE'])
def delete_notification(notif_id):
    if not session.get('is_master'):
        return jsonify({"success": False}), 403
    import sqlite3
    from app.models.schema import get_db_path
    conn = sqlite3.connect(get_db_path())
    conn.cursor().execute("DELETE FROM notifications_master WHERE id = ?", (notif_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@master_bp.route('/notifications/clear-all', methods=['DELETE'])
def clear_all_notifications():
    if not session.get('is_master'):
        return jsonify({"success": False}), 403
    import sqlite3
    from app.models.schema import get_db_path
    conn = sqlite3.connect(get_db_path())
    conn.cursor().execute("DELETE FROM notifications_master")
    conn.commit()
    conn.close()
    return jsonify({"success": True})
"""

if "def delete_notification" not in content:
    content += new_routes

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
