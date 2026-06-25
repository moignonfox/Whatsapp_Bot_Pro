"""Factory Pattern — Création et configuration de l'application Flask."""
import os
from flask import Flask
from flask_socketio import SocketIO
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import config as app_config
from app.models.schema import init_db

# Instance SocketIO au niveau du module (accessible par les autres modules)
socketio = SocketIO()
# Protection CSRF globale
csrf = CSRFProtect()
# Rate limiter (brute force protection)
limiter = Limiter(key_func=get_remote_address)


def create_app(config_name=None):
    """Crée et configure l'instance Flask."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')

    app = Flask(__name__)

    # Chargement de la configuration
    app.config.from_object(app_config[config_name])

    # Configuration des cookies de session (sécurité de base)
    app.config.setdefault('SESSION_COOKIE_HTTPONLY', True)
    app.config.setdefault('SESSION_COOKIE_SAMESITE', 'Lax')

    # Initialisation de la base de données
    init_db()

    # Protection CSRF (flask-wtf)
    # WTF_CSRF_CHECK_DEFAULT doit être défini AVANT init_app()
    app.config['WTF_CSRF_CHECK_DEFAULT'] = True
    csrf.init_app(app)

    # Injection de csrf_token dans tous les templates via context_processor
    # (méthode fiable indépendante de l'ordre d'initialisation Jinja2)
    @app.context_processor
    def inject_csrf_token():
        from flask_wtf.csrf import generate_csrf
        return dict(csrf_token=generate_csrf)

    # Rate limiter (M-1 : protection brute force)
    limiter.init_app(app)

    # Origines autorisées pour SocketIO
    # En dev : accepter localhost ET 127.0.0.1 (le navigateur peut utiliser l'un ou l'autre)
    # En prod : définir ALLOWED_ORIGINS dans le .env (séparées par des virgules)
    env_origins = os.environ.get('ALLOWED_ORIGINS', '')
    if env_origins:
        allowed_origins = [o.strip() for o in env_origins.split(',')]
    else:
        port = os.environ.get('PORT', '5000')
        allowed_origins = [
            f'http://localhost:{port}',
            f'http://127.0.0.1:{port}',
        ]

    # Initialisation de SocketIO
    socketio.init_app(app, cors_allowed_origins=allowed_origins, async_mode='eventlet')

    # Enregistrement des Blueprints
    from app.webhooks.routes import webhooks_bp
    from app.dashboard.routes import dashboard_bp
    from app.master.routes import master_bp

    app.register_blueprint(webhooks_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(master_bp)

    # Exempter le webhook Meta de la protection CSRF
    # (Meta envoie des requêtes POST sans token CSRF)
    csrf.exempt(webhooks_bp)

    # Handler SocketIO pour les rooms — vérifie que l'utilisateur est bien connecté
    @socketio.on('rejoindre_room')
    def handle_join_room(data):
        from flask import session
        from flask_socketio import join_room
        # Refuser si la session ne contient pas d'utilisateur authentifié
        user_id = session.get('user_id') or session.get('is_master')
        if not user_id:
            return  # Connexion refusée silencieusement
        room = data.get('room')
        # Un business ne peut rejoindre QUE sa propre room
        if room and (room == session.get('user_id') or session.get('is_master')):
            join_room(room)

    return app
