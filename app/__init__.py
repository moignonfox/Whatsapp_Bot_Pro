"""Factory Pattern — Création et configuration de l'application Flask."""
import os
import logging
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
    app.config['WTF_CSRF_CHECK_DEFAULT'] = True
    app.config['WTF_CSRF_TIME_LIMIT'] = 86400  # 24h au lieu de 1h
    csrf.init_app(app)

    # Injection de csrf_token dans tous les templates
    @app.context_processor
    def inject_csrf_token():
        from flask_wtf.csrf import generate_csrf
        return dict(csrf_token=generate_csrf)

    # Rate limiter
    limiter.init_app(app)

    # Initialisation JWT
    jwt.init_app(app)

    # ------------------------------------------------------------------ #
    # Blocklist JWT — vérification à chaque requête protégée              #
    # ------------------------------------------------------------------ #
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        """Retourne True si le token a été révoqué (logout)."""
        import sqlite3
        from app.models.schema import get_db_path
        jti = jwt_payload.get('jti')
        if not jti:
            return False
        try:
            conn = sqlite3.connect(get_db_path())
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM jwt_blocklist WHERE jti = ?", (jti,))
            row = cursor.fetchone()
            conn.close()
            return row is not None
        except Exception:
            return False

    # ------------------------------------------------------------------ #
    # CORS — origines restreintes (pas de wildcard en API REST)           #
    # ------------------------------------------------------------------ #
    raw_origins = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:5000')
    allowed_api_origins = [o.strip() for o in raw_origins.split(',')]
    cors.init_app(app, resources={r"/api/*": {"origins": allowed_api_origins}})

    # ------------------------------------------------------------------ #
    # Handlers d'erreurs globaux (JSON propre, sans stack trace)          #
    # ------------------------------------------------------------------ #
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

    # ------------------------------------------------------------------ #
    # SocketIO — cors_allowed_origins="*" requis pour mobile natif        #
    # (les apps mobiles n'ont pas d'origine HTTP fixe).                   #
    # Pour un dashboard web, ajouter son domaine dans allowed_api_origins #
    # ------------------------------------------------------------------ #
    socketio.init_app(app, cors_allowed_origins="*", async_mode='eventlet')

    # ------------------------------------------------------------------ #
    # Tâche planifiée — nettoyage périodique de la blocklist JWT          #
    # ------------------------------------------------------------------ #
    def _cleanup_jwt_blocklist():
        """Supprime les tokens révoqués dont la date d'expiration est passée."""
        import sqlite3
        from datetime import datetime, timezone
        from app.models.schema import get_db_path
        try:
            now_ts = int(datetime.now(timezone.utc).timestamp())
            conn = sqlite3.connect(get_db_path())
            cursor = conn.cursor()
            cursor.execute("DELETE FROM jwt_blocklist WHERE expires_at < ?", (now_ts,))
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            if deleted:
                logging.getLogger(__name__).info(
                    "Blocklist cleanup: %d tokens expirés supprimés.", deleted
                )
        except Exception as exc:
            logging.getLogger(__name__).error("Blocklist cleanup error: %s", exc)

    def _cleanup_webhook_seen_ids():
        """Supprime les wam_id vieux de plus de 24h (anti-rejeu)."""
        import sqlite3
        from app.models.schema import get_db_path
        try:
            conn = sqlite3.connect(get_db_path())
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM webhook_seen_ids WHERE seen_at < datetime('now', '-24 hours')"
            )
            conn.commit()
            conn.close()
        except Exception as exc:
            logging.getLogger(__name__).error("Webhook seen_ids cleanup error: %s", exc)

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        scheduler.add_job(_cleanup_jwt_blocklist, 'interval', hours=1, id='jwt_blocklist_cleanup')
        scheduler.add_job(_cleanup_webhook_seen_ids, 'interval', hours=1, id='webhook_seen_ids_cleanup')
        scheduler.start()
    except Exception as sched_err:
        logging.getLogger(__name__).warning("Scheduler non démarré : %s", sched_err)


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

    # Enregistrement des Blueprints
    from app.webhooks.routes import webhooks_bp
    from app.webhooks.cinetpay import cinetpay_bp
    from app.dashboard.routes import dashboard_bp
    from app.master.routes import master_bp
    from app.master.master_notifications import master_notifications_bp
    from app.api import api_bp

    app.register_blueprint(webhooks_bp)
    app.register_blueprint(cinetpay_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(master_bp)
    app.register_blueprint(master_notifications_bp)
    app.register_blueprint(api_bp)

    # Exempter l'API de la protection CSRF de base (JWT est utilisé)
    csrf.exempt(api_bp)

    # Exempter les webhooks de la protection CSRF
    csrf.exempt(webhooks_bp)
    csrf.exempt(cinetpay_bp)

    # ------------------------------------------------------------------ #
    # Handler SocketIO — rooms Session Web (dashboard)                    #
    # ------------------------------------------------------------------ #
    @socketio.on('rejoindre_room')
    def handle_join_room(data):
        from flask import session
        from flask_socketio import join_room
        user_id = session.get('user_id') or session.get('is_master')
        if not user_id:
            return
        room = data.get('room')
        if room and (room == session.get('user_id') or session.get('is_master')):
            join_room(room)

    # ------------------------------------------------------------------ #
    # Handler SocketIO — authentification JWT (app mobile)                #
    # ------------------------------------------------------------------ #
    @socketio.on('authenticate_jwt')
    def handle_authenticate_jwt(data):
        token = data.get('token')
        if not token:
            return
        from flask_jwt_extended import decode_token
        from flask_socketio import join_room
        try:
            decoded = decode_token(token)
            company_id = decoded['sub']
            if company_id:
                join_room(company_id)
        except Exception as e:
            logging.getLogger(__name__).warning("SocketIO JWT Auth échoué : %s", e)

    return app
