import os

api_auth_path = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\api\auth.py'

new_route = """

@api_bp.route('/auth/forgot-password', methods=['POST'])
@limiter.limit("5 per minute")
def forgot_password_api():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    
    if not email:
        return jsonify({"success": False, "error": "L'email est requis."}), 400
        
    business = business_repo.get_by_email(email)
    if business:
        try:
            from app.services.notification_master_service import create_master_notification
            create_master_notification('alerte', f"Mot de passe oubli\u00e9 (Mobile): {business['nom']} ({email})", business['id'])
        except Exception:
            pass
            
    # Succ\u00e8s g\u00e9n\u00e9rique pour s\u00e9curit\u00e9
    return jsonify({
        "success": True, 
        "message": "Si cet email existe, le Master a \u00e9t\u00e9 notifi\u00e9 et vous contactera pour r\u00e9initialiser votre mot de passe."
    }), 200
"""

with open(api_auth_path, 'a', encoding='utf-8') as f:
    f.write(new_route)

