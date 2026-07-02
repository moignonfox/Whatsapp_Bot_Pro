import os
import firebase_admin
from firebase_admin import credentials, messaging
from app.repositories import business_repo

# Initialisation du SDK Firebase
def init_firebase():
    if not firebase_admin._apps:
        # Le chemin vers votre fichier firebase-adminsdk.json
        cred_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'firebase-adminsdk.json')
        if os.path.exists(cred_path):
            try:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                print("[Firebase] Admin SDK initialisé avec succès.")
            except Exception as e:
                print(f"[Firebase] Erreur lors de l'initialisation: {e}")
        else:
            print(f"[Firebase] AVERTISSEMENT: Fichier firebase-adminsdk.json introuvable au chemin : {cred_path}")

def send_push_notification(business_id: str, title: str, body: str, data: dict = None) -> bool:
    """
    Envoie une notification push au téléphone du business concerné.
    """
    if not firebase_admin._apps:
        return False
        
    business = business_repo.get_by_id(business_id)
    if not business:
        return False

    business_dict = dict(business)
    fcm_token = business_dict.get('fcm_token')
    if not fcm_token:
        print(f"[Firebase] Aucun FCM token pour le business {business_id}. Notification non envoyée.")
        return False

    if data is None:
        data = {}

    # Convertir les valeurs de `data` en string, car Firebase n'accepte que des strings dans data payload
    data = {str(k): str(v) for k, v in data.items()}

    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=data,
        token=fcm_token,
        android=messaging.AndroidConfig(
            priority='high',
            notification=messaging.AndroidNotification(
                sound='default'
            )
        )
    )

    try:
        response = messaging.send(message)
        print(f"[Firebase] Notification envoyée avec succès à {business_id}: {response}")
        return True
    except Exception as e:
        print(f"[Firebase] Erreur lors de l'envoi de la notification à {business_id}: {e}")
        return False
