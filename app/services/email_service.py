import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging

logger = logging.getLogger(__name__)

def send_deletion_confirmation_email(to_email: str, deletion_date: str):
    """
    Envoie un email de confirmation de suppression de compte au gérant.
    """
    subject = "Confirmation de suppression de votre compte Vira"
    body = f"""Bonjour,

Votre compte Vira a été supprimé.
Votre numéro WhatsApp est maintenant libéré.
Vos données seront supprimées définitivement le {deletion_date}.

Merci d'avoir utilisé Vira.

L'équipe Vira
"""
    
    sender_email = os.environ.get('MAIL_USERNAME')
    sender_password = os.environ.get('MAIL_PASSWORD')
    smtp_server = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('MAIL_PORT', 587))
    
    if not sender_email or not sender_password:
        logger.warning(f"[Email] Identifiants non configurés. Email non envoyé à {to_email}:\n{body}")
        return False
        
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        logger.info(f"[Email] Confirmation de suppression envoyée à {to_email}")
        return True
    except Exception as e:
        logger.error(f"[Email] Erreur d'envoi à {to_email}: {e}")
        return False
