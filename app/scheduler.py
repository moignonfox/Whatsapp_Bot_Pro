import logging
from apscheduler.schedulers.background import BackgroundScheduler
from app.services.report_service import generate_all_daily_reports
from app.services.marketing_worker import process_campaign_queue
from app.services.drip_service import process_daily_drip_campaigns
from app.services.human_mode_worker import check_human_mode_timeouts
from app.services.reminder_worker import check_and_send_reminders

# Configuration du logging pour le scheduler
logging.getLogger('apscheduler').setLevel(logging.INFO)

def start_scheduler():
    scheduler = BackgroundScheduler()
    
    # Exécuter tous les jours à 19:00
    scheduler.add_job(func=generate_all_daily_reports, trigger="cron", hour=19, minute=0)
    
    # Séquences Automatisées (Drip Marketing J+3) - Exécuter tous les matins à 10:00
    scheduler.add_job(func=process_daily_drip_campaigns, trigger="cron", hour=10, minute=0)
    
    # Worker de file d'attente marketing (Anti-Spam)
    # S'exécute toutes les 15 secondes pour dépiler les messages
    scheduler.add_job(func=process_campaign_queue, trigger="interval", seconds=15)
    
    # Worker de timeout du Mode Humain
    # S'exécute toutes les minutes
    scheduler.add_job(func=check_human_mode_timeouts, trigger="interval", minutes=1)

    # Worker de rappel de RDV WhatsApp (client + gérant)
    # S'exécute toutes les minutes
    scheduler.add_job(func=check_and_send_reminders, trigger="interval", minutes=1)
    
    scheduler.start()
    logging.info("APScheduler démarré : Le rapport quotidien sera envoyé à 19h00.")
