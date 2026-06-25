"""Point d'entree de l'application WhatsApp Bot Pro."""
# /!\ eventlet.monkey_patch() DOIT etre la toute premiere ligne executee,
# avant tout autre import, sinon les locks Python ne sont pas correctement patched
import eventlet
eventlet.monkey_patch()

import os
from app import create_app, socketio
from app.scheduler import start_scheduler

app = create_app()

if __name__ == '__main__':
    start_scheduler()
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    # eventlet gere le serveur HTTP et les WebSockets nativement
    socketio.run(app, host='0.0.0.0', port=5000, debug=debug_mode, use_reloader=False)
