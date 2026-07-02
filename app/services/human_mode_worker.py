import logging
import sqlite3
import json
from datetime import datetime, timezone, timedelta
from app.repositories import business_repo, conversation_repo
from app.services import whatsapp_service
from app.repositories.business_repo import get_db_path

logger = logging.getLogger(__name__)

TIMEOUT_MINUTES = 30

def check_human_mode_timeouts():
    """Vérifie si des sessions en mode humain ont expiré et rend la main à l'IA."""
    try:
        conn = sqlite3.connect(get_db_path())
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Récupérer tous les business qui ont le human_mode configuré (non nul)
        cursor.execute("SELECT id, token_wa, whatsapp_phone_id, human_mode FROM businesses WHERE human_mode IS NOT NULL AND human_mode != '{}'")
        businesses = cursor.fetchall()
        
        now = datetime.now(timezone.utc)
        
        for biz in businesses:
            biz_id = biz['id']
            try:
                modes = json.loads(biz['human_mode'])
            except json.JSONDecodeError:
                continue
                
            has_changes = False
            expired_was = []
            
            for wa_id, timestamp_str in list(modes.items()):
                # Si c'était un vieux format (bool = True), on l'écrase avec le timestamp actuel pour lui donner 30 min
                if isinstance(timestamp_str, bool):
                    modes[wa_id] = now.isoformat()
                    has_changes = True
                    continue
                    
                try:
                    # Parse timestamp
                    start_time = datetime.fromisoformat(timestamp_str)
                    
                    # Si la date est naive, on lui assigne UTC pour éviter les crashs
                    if start_time.tzinfo is None:
                        start_time = start_time.replace(tzinfo=timezone.utc)
                        
                    # Rendre la main si dépassé
                    if now - start_time > timedelta(minutes=TIMEOUT_MINUTES):
                        expired_was.append(wa_id)
                except Exception as e:
                    logger.error(f"[HUMAN_MODE_WORKER] Erreur parsing date pour {wa_id}: {e}")
                    # En cas d'erreur de parsing (ex: vieux format invalide), on réinitialise le timer 
                    # au lieu d'expirer brusquement la conversation.
                    modes[wa_id] = now.isoformat()
                    has_changes = True
                    
            if expired_was:
                for wa_id in expired_was:
                    logger.info(f"[HUMAN_MODE_WORKER] Timeout expiré pour {wa_id} sur {biz_id}. Réactivation de l'IA.")
                    del modes[wa_id]
                    
                    # 1. Message d'excuse au client
                    msg_client = "Toutes nos excuses, nos conseillers sont actuellement tous occupés. Notre assistant virtuel reprend la main. Comment puis-je continuer à vous aider ?"
                    conversation_repo.save_message(wa_id, 'assistant', msg_client, biz_id)
                    whatsapp_service.send_message(wa_id, msg_client, biz['whatsapp_phone_id'], biz['token_wa'])
                    
                    # 2. Informer le dashboard en temps réel
                    try:
                        from app import socketio
                        socketio.emit('human_mode_toggled', {'business_id': biz_id, 'wa_id': wa_id, 'state': False}, room=biz_id)
                        socketio.emit('nouveau_message', {
                            'business_id': biz_id, 'wa_id': wa_id, 'content': msg_client,
                            'role': 'assistant', 'timestamp': 'now'
                        }, room=biz_id)
                    except Exception as e:
                        pass
                        
                has_changes = True
                
            # Sauvegarder les changements dans la BD
            if has_changes:
                cursor.execute(
                    "UPDATE businesses SET human_mode = ? WHERE id = ?",
                    (json.dumps(modes), biz_id)
                )
                conn.commit()
                
    except Exception as e:
        logger.error(f"[HUMAN_MODE_WORKER] Erreur globale: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
