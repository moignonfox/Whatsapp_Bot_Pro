import sys
import os

# Setup sys.path to run like the flask app
sys.path.insert(0, r"c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro")

try:
    from app.services.notification_master_service import create_master_notification
    create_master_notification('alerte', 'Test Script', 'Test de message via script Python', '123')
    print("SUCCESS: Notification créée avec succès")
except Exception as e:
    import traceback
    print("ERROR:")
    traceback.print_exc()
