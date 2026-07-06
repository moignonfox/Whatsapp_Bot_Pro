import re

filepath = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\__init__.py'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Prolonger la duree du token CSRF a 24h
if "app.config['WTF_CSRF_TIME_LIMIT']" not in content:
    content = content.replace(
        "app.config['WTF_CSRF_CHECK_DEFAULT'] = True",
        "app.config['WTF_CSRF_CHECK_DEFAULT'] = True\n    app.config['WTF_CSRF_TIME_LIMIT'] = 86400  # 24h au lieu de 1h"
    )

# 2. Ajouter un errorhandler pour la CSRFError
csrf_handler = """
    from flask_wtf.csrf import CSRFError
    from flask import jsonify, render_template

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        # Si c'est une requête API
        if request.path.startswith('/api/'):
            return jsonify({'success': False, 'error': "Session expirée. Veuillez recharger la page."}), 400
            
        # Si c'est sur la page d'authentification
        if '/forgot-password' in request.path:
            return render_template('auth/forgot_password.html', error="Votre session a expiré pour des raisons de sécurité. Veuillez soumettre à nouveau le formulaire.")
        elif '/login' in request.path:
            return render_template('auth/login.html', error="Votre session a expiré pour des raisons de sécurité. Veuillez vous reconnecter.")
        elif '/register' in request.path:
            return render_template('auth/register.html', error="Votre session a expiré pour des raisons de sécurité. Veuillez recommencer l'inscription.")
            
        # Par défaut
        return "Erreur de sécurité (CSRF Expired). Veuillez revenir en arrière et rafraîchir la page.", 400
"""

if "def handle_csrf_error(e):" not in content:
    # Insérer ça juste avant les enregistrements de blueprints
    content = content.replace(
        "    # Enregistrement des Blueprints",
        csrf_handler + "\n    # Enregistrement des Blueprints"
    )

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
