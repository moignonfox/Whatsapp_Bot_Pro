import os

routes_path = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\dashboard\routes.py'

new_route = """

@dashboard_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        if not email:
            return render_template('auth/forgot_password.html', error="Veuillez entrer votre adresse email.")
            
        business = business_repo.get_by_email(email)
        if business:
            try:
                from app.services.notification_master_service import create_master_notification
                create_master_notification('alerte', f"Mot de passe oubli\u00e9: {business['nom']} ({email})", business['id'])
            except Exception:
                pass
                
        # On affiche toujours un message de succ\u00e8s pour ne pas r\u00e9v\u00e9ler si l'email existe ou non (s\u00e9curit\u00e9)
        return render_template('auth/forgot_password.html', success="Si cet email existe dans notre syst\u00e8me, notre \u00e9quipe vous contactera pour r\u00e9initialiser votre mot de passe.")
        
    return render_template('auth/forgot_password.html')
"""

with open(routes_path, 'a', encoding='utf-8') as f:
    f.write(new_route)

