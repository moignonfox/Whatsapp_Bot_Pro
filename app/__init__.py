"""Factory Pattern — Création et configuration de l'application Flask."""
import os
from flask import Flask, request
from flask_socketio import SocketIO
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import config as app_config
from app.models.schema import init_db

# Instance SocketIO au niveau du module (accessible par les autres modules)
socketio = SocketIO()
# Protection CSRF globale
csrf = CSRFProtect()
# Rate limiter (brute force protection)
limiter = Limiter(key_func=get_remote_address)
# Gestionnaire JWT pour l'API
jwt = JWTManager()
# CORS pour l'API
cors = CORS()


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

    # Configuration des uploads
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB max

    # Initialisation de la base de données
    init_db()

    # Initialisation Firebase Admin SDK
    from app.services.notification_service import init_firebase
    init_firebase()

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

    # Initialisation JWT
    jwt.init_app(app)

    # Initialisation CORS (autoriser seulement /api/*)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    # Gestionnaire d'erreurs global pour l'API (pour toujours renvoyer du JSON au lieu du HTML)
    @app.errorhandler(400)
    def bad_request(e):
        if request.path.startswith('/api/'):
            from flask import jsonify
            return jsonify(error=str(e.description)), 400
        return e

    @app.errorhandler(401)
    def unauthorized(e):
        if request.path.startswith('/api/'):
            from flask import jsonify
            return jsonify(error="Non autorisé"), 401
        return e

    @app.errorhandler(403)
    def forbidden(e):
        if request.path.startswith('/api/'):
            from flask import jsonify
            return jsonify(error="Accès refusé"), 403
        return e

    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith('/api/'):
            from flask import jsonify
            return jsonify(error="Ressource introuvable"), 404
        return e

    @app.errorhandler(500)
    def internal_error(e):
        if request.path.startswith('/api/'):
            from flask import jsonify
            return jsonify(error="Erreur interne du serveur"), 500
        return e

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
    socketio.init_app(app, cors_allowed_origins="*", async_mode='eventlet')

    # Enregistrement des Blueprints
    from app.webhooks.routes import webhooks_bp
    from app.dashboard.routes import dashboard_bp
    from app.master.routes import master_bp
    from app.api import api_bp

    app.register_blueprint(webhooks_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(master_bp)
    app.register_blueprint(api_bp)

    # Exempter l'API de la protection CSRF de base (JWT est utilisé)
    csrf.exempt(api_bp)

    # Exempter le webhook Meta de la protection CSRF
    # (Meta envoie des requêtes POST sans token CSRF)
    csrf.exempt(webhooks_bp)

    # Handler SocketIO pour les rooms — vérifie que l'utilisateur est bien connecté (Session Web)
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

    # Handler SocketIO pour les apps mobiles (via JWT)
    @socketio.on('authenticate_jwt')
    def handle_authenticate_jwt(data):
        print("Reçu demande authenticate_jwt")
        token = data.get('token')
        if not token:
            print("Erreur: pas de token")
            return
        from flask_jwt_extended import decode_token
        from flask_socketio import join_room
        try:
            decoded = decode_token(token)
            company_id = decoded['sub']
            if company_id:
                join_room(company_id)
                print(f"✅ JWT Auth réussi ! A rejoint la room : {company_id}")
        except Exception as e:
            print(f"❌ Erreur JWT Auth : {e}")

    return app
