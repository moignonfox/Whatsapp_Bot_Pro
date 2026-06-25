"""Service Principal — Orchestration du traitement des messages."""
import logging
import threading
import time
from app.services import ai_service, crm_service, order_service, whatsapp_service
from app.repositories import business_repo, conversation_repo, employee_repo, agent_repo

logger = logging.getLogger(__name__)

active_timers = {}
first_msg_time = {}
processing_lock = set()
warned_truncation_users = set()
MAX_DEBOUNCE_WAIT = 20 # Limite absolue d'attente (secondes)


def enqueue_message(wa_id, user_text, business, phone_id):
    """Reçoit un message et gère le délai (debounce) avant traitement."""
    try:
        if not isinstance(business, dict):
            business = dict(business)
        biz_id = business['id']

        # 0. Enregistrer IMMEDIATEMENT le message entrant
        conversation_repo.save_message(wa_id, 'user', user_text, biz_id)

        # Coupe-circuit : Mode humain
        if business_repo.is_human_mode(biz_id, wa_id):
            print(f"MODE HUMAIN actif pour {wa_id} sur {biz_id} - IA ignoree")
            return

        delay = business.get('debounce_delay', 3)
        if delay <= 0:
            trigger_processing(wa_id, business, phone_id)
            return

        now = time.time()
        if wa_id not in first_msg_time:
            first_msg_time[wa_id] = now
            
        elapsed = now - first_msg_time[wa_id]
        
        # Annuler le timer existant si on n'a pas dépassé la limite absolue
        if wa_id in active_timers:
            if elapsed < MAX_DEBOUNCE_WAIT:
                active_timers[wa_id].cancel()
            else:
                # On ne fait rien, on laisse le timer expirer et traiter
                return

        # Créer et démarrer un nouveau timer
        timer = threading.Timer(
            delay, 
            trigger_processing, 
            args=[wa_id, business, phone_id]
        )
        active_timers[wa_id] = timer
        timer.start()

    except Exception as e:
        print(f"Erreur dans enqueue_message: {e}")

def trigger_processing(wa_id, business, phone_id):
    """Se déclenche après le délai, gère les verrous de concurrence."""
    if wa_id in active_timers:
        del active_timers[wa_id]
    if wa_id in first_msg_time:
        del first_msg_time[wa_id]
        
    if wa_id in processing_lock:
        # Relance dans 2 secondes si l'IA est DÉJÀ en train d'écrire pour cet utilisateur
        timer = threading.Timer(2.0, trigger_processing, args=[wa_id, business, phone_id])
        active_timers[wa_id] = timer
        timer.start()
        return
        
    processing_lock.add(wa_id)
    try:
        process_debounced_messages(wa_id, business, phone_id)
    finally:
        processing_lock.discard(wa_id)


def process_debounced_messages(wa_id, business, phone_id):
    """Traite les messages regroupés de bout en bout."""
    try:
        biz_id = business['id']

        # Récupérer tous les messages en attente depuis la dernière réponse
        pending_msgs = conversation_repo.get_pending_user_messages(wa_id, biz_id)
        if not pending_msgs:
            return # Déjà traité ou erreur
            
        combined_text = "\n".join(pending_msgs)
        # M-3 : masquage du numéro — on n'affiche que les 4 derniers chiffres
        safe_id = f"****{wa_id[-4:]}" if len(wa_id) >= 4 else "****"
        logger.debug("[DEBOUNCE] %d messages regroupés pour %s", len(pending_msgs), safe_id)

        # Troncature Intelligente
        plan = business.get('plan_abonnement', 'BASIC')
        from app.repositories.settings_repo import get_setting
        
        if plan == 'PREMIUM':
            limit_str = get_setting('max_input_premium', '3000')
        elif plan == 'PRO':
            limit_str = get_setting('max_input_pro', '1000')
        else:
            limit_str = get_setting('max_input_basic', '500')
            
        try:
            max_input_len = int(limit_str)
        except ValueError:
            max_input_len = 500
            
        if len(combined_text) > max_input_len:
            # Conserver les premiers 20% (contexte intro) et la fin (question)
            keep_start = int(max_input_len * 0.2)
            keep_end = max_input_len - keep_start - 30  # 30 pour la chaîne de troncature
            if keep_end > 0:
                combined_text = combined_text[:keep_start] + "\n...[MESSAGE TRONQUÉ]...\n" + combined_text[-keep_end:]
            else:
                combined_text = combined_text[:max_input_len]
                
            # Prévenir l'utilisateur (une fois par session/serveur)
            if wa_id not in warned_truncation_users:
                warn_msg = "⚠️ Votre message était très long et a été traité partiellement. N'hésitez pas à poser vos questions séparément si j'ai manqué un détail !"
                whatsapp_service.send_message(wa_id, warn_msg, phone_id, business['token_wa'])
                warned_truncation_users.add(wa_id)

        # Enrichissement PREMIUM : injection de la liste des employés
        if business.get('plan_abonnement') == 'PREMIUM':
            employees = employee_repo.get_by_business(biz_id)
            business['employees'] = [dict(e) for e in employees]
        else:
            business['employees'] = []

        # =====================================================================
        # VERIFICATION DU QUOTA MENSUEL (Filet de Sécurité Facturation)
        # =====================================================================
        from app.repositories import settings_repo
        
        current_ai_usage = conversation_repo.get_monthly_ai_message_count(biz_id)
        if plan == 'PREMIUM':
            quota = int(settings_repo.get_setting('quota_messages_premium', '10000'))
        elif plan == 'PRO':
            quota = int(settings_repo.get_setting('quota_messages_pro', '2000'))
        else:
            quota = int(settings_repo.get_setting('quota_messages_basic', '500'))
            
        overage_behavior = settings_repo.get_setting('overage_behavior', 'FALLBACK')
        
        # Alerte à 80% (une seule fois exacte)
        if current_ai_usage == int(quota * 0.8):
            logger.warning("[QUOTA ALERTE] Business %s a atteint 80%% de son quota IA (%d/%d)", biz_id, current_ai_usage, quota)
            from app.repositories import order_repo
            alert_msg = f"⚠️ ALERTE QUOTA : Vous avez consommé {current_ai_usage} messages IA sur {quota} autorisés pour ce mois. Pensez à upgrader."
            order_repo.save_reservation(biz_id, wa_id, alert_msg, priorite="Haute")
            
        if current_ai_usage >= quota:
            logger.warning("[QUOTA ATTEINT] Business %s a dépassé son quota IA (%d/%d)", biz_id, current_ai_usage, quota)
            if overage_behavior == 'BLOCK':
                logger.info("[QUOTA BLOCK] IA coupée silencieusement pour %s", biz_id)
                return
            elif overage_behavior == 'FALLBACK':
                logger.info("[QUOTA FALLBACK] Mode dégradé pour %s", biz_id)
                from app.repositories import order_repo
                fallback_alert = f"⚠️ QUOTA ATTEINT - IA SUSPENDUE. Message client à gérer manuellement: {combined_text}"
                order_repo.save_reservation(biz_id, wa_id, fallback_alert, priorite="Haute")
                
                fallback_msg = "Notre assistant automatique a atteint sa limite pour le mois. Le gérant a été notifié de votre message et vous répondra manuellement au plus vite."
                conversation_repo.save_message(wa_id, 'assistant', fallback_msg, biz_id)
                whatsapp_service.send_message(wa_id, fallback_msg, phone_id, business.get('token_wa', ''))
                
                try:
                    from app import socketio
                    socketio.emit('nouveau_message', {
                        'business_id': biz_id, 'wa_id': wa_id, 'content': fallback_msg, 'role': 'assistant', 'timestamp': 'now'
                    }, room=biz_id)
                except Exception:
                    pass
                return
            elif overage_behavior == 'OVERAGE':
                print("[QUOTA OVERAGE] Comportement OVERAGE: on continue, surconsommation activée.")
                # L'IA est autorisée à continuer malgré le dépassement


        # =====================================================================
        # 1. Appel a l'IA avec gestion de la Dégradation Fluide et Transfert Humain
        # =====================================================================
        agent_id = None
        human_handoff_triggered = False
        
        # A. Déclencheur Déterministe (Mots-clés)
        trigger_pattern = r'\b(humain|conseiller|responsable|manager|quelqu\'un de vrai|parler à quelqu\'un)\b'
        import re
        if re.search(trigger_pattern, combined_text, re.IGNORECASE):
            human_handoff_triggered = True
            agent_reply = ""
            logger.info(f"[HANDOFF] Transfert humain déclenché par détection déterministe pour {wa_id}")
        else:
            try:
                # Récupérer les agents IA de l'entreprise
                ai_agents = agent_repo.get_by_business(biz_id)
                ai_agents_dicts = [dict(a) for a in ai_agents]
                
                # Classification d'intention si des agents sont définis
                selected_agent = None
                if ai_agents_dicts:
                    # Retrouver le dernier agent utilisé dans cette session (pour le fallback)
                    last_agent_id = conversation_repo.get_last_agent_id(wa_id, biz_id)
                    selected_agent = ai_service.classify_intent(
                        wa_id, biz_id, combined_text, ai_agents_dicts,
                        last_agent_id=last_agent_id
                    )
                    if selected_agent:
                        agent_id = selected_agent['id']

                agent_reply = ai_service.get_ai_response(wa_id, combined_text, business, selected_agent)
                
                # B. Déclencheur IA
                if "[TRANSFERT_HUMAIN]" in agent_reply:
                    human_handoff_triggered = True
                    agent_reply = agent_reply.replace("[TRANSFERT_HUMAIN]", "").strip()
                    logger.info(f"[HANDOFF] Transfert humain déclenché par l'IA pour {wa_id}")
                    
            except Exception as ai_err:
                logger.error("[FALLBACK IA] Echec de l'IA : %s", ai_err)
                
                try:
                    from app.repositories import order_repo
                    
                    # Verification anti-spam : on recupere la derniere commande
                    last_res = order_repo.get_last_for_user(wa_id)
                    
                    # Si on a DEJA cree une alerte, on ignore (on ne spamme pas le dashboard)
                    if last_res and last_res['details'].startswith("⚠️ IA INDISPONIBLE"):
                        logger.debug("[FALLBACK IA] Alerte déjà envoyée, ignorée.")
                    else:
                        details_secours = f"⚠️ IA INDISPONIBLE - Nouveau message client reçu (voir conversation)"
                        order_repo.save_reservation(biz_id, wa_id, details_secours, priorite="Haute")
                        logger.info("[FALLBACK IA] Réservation de secours créée.")
                        
                        # Message de secours
                        fallback_msg = "Notre système automatique est momentanément indisponible, mais le gérant vient de recevoir votre demande et va vous répondre manuellement d'un instant à l'autre !"
                        
                        # Sauvegarde et envoi du message de secours
                        conversation_repo.save_message(wa_id, 'assistant', fallback_msg, biz_id)
                        whatsapp_service.send_message(wa_id, fallback_msg, phone_id, business.get('token_wa', ''))
                        logger.info("[FALLBACK IA] Message de secours envoyé.")

                        try:
                            from app import socketio
                            socketio.emit('nouveau_message', {
                                'business_id': biz_id, 'wa_id': wa_id, 'content': fallback_msg,
                                'role': 'assistant', 'timestamp': 'now'
                            }, room=biz_id)
                        except Exception as ws_err:
                            logger.warning("[FALLBACK IA] Erreur SocketIO: %s", ws_err)
                except Exception as fallback_err:
                    logger.error("[FALLBACK IA] ERREUR CRITIQUE pendant le fallback: %s", fallback_err)
                
                return # Arrêter le traitement automatique ici

        
        # =====================================================================
        # 1.5 Gestion du Transfert Humain
        # =====================================================================
        if human_handoff_triggered:
            # Activer le mode humain en base
            business_repo.set_human_mode(biz_id, wa_id, True)
            
            # Message d'attente au client
            wait_msg = "Je comprends. Je viens de transférer votre demande à un conseiller humain. Il va vous répondre très vite sur cette même conversation. Merci de patienter quelques instants."
            
            # S'il y avait une réponse avant le tag, on la garde
            if agent_reply:
                final_msg = f"{agent_reply}\n\n{wait_msg}"
            else:
                final_msg = wait_msg
                
            conversation_repo.save_message(wa_id, 'assistant', final_msg, biz_id, agent_id)
            whatsapp_service.send_message(wa_id, final_msg, phone_id, business.get('token_wa', ''))
            
            # Alerte au gérant (si owner_phone configuré)
            owner_phone = business.get('owner_phone', '').strip()
            logger.info(f"[HANDOFF] owner_phone lu depuis business: '{owner_phone}'")
            if owner_phone:
                # Normaliser : supprimer +, espaces, tirets
                owner_phone_clean = owner_phone.replace('+', '').replace(' ', '').replace('-', '')
                
                # Si le numéro fait exactement 8 chiffres (format local Togo), on ajoute 228
                if len(owner_phone_clean) == 8 and owner_phone_clean.isdigit():
                    owner_phone_clean = '228' + owner_phone_clean
                    
                motif = "Détection mots-clés" if not agent_reply else "Transfert décidé par l'IA"
                alert_msg = (
                    f"🔔 *TRANSFERT HUMAIN DEMANDÉ* 🔔\n\n"
                    f"Client : +{wa_id}\n"
                    f"Motif : {motif}\n\n"
                    f"👉 Prenez le relais sur le Dashboard !"
                )
                # Envoi au gérant (sans enregistrer dans l'historique du client)
                status = whatsapp_service.send_message(owner_phone_clean, alert_msg, phone_id, business.get('token_wa', ''))
                logger.info(f"[HANDOFF] Notification envoyée au gérant {owner_phone_clean} — statut HTTP: {status}")
            else:
                logger.warning("[HANDOFF] Pas de notification : owner_phone non configuré dans les paramètres du business.")
                
            # Emission socket pour mettre à jour le dashboard en temps réel
            try:
                from app import socketio
                socketio.emit('human_mode_toggled', {'business_id': biz_id, 'wa_id': wa_id, 'state': True}, room=biz_id)
                socketio.emit('nouveau_message', {
                    'business_id': biz_id, 'wa_id': wa_id, 'content': final_msg,
                    'role': 'assistant', 'timestamp': 'now'
                }, room=biz_id)
            except Exception as ws_err:
                logger.warning(f"[HANDOFF] Erreur SocketIO: {ws_err}")
                
            return # Fin du traitement (on ne passe pas aux réservations)


        # Sauvegarder IMMEDIATEMENT la reponse generee par l'IA
        conversation_repo.save_message(wa_id, 'assistant', agent_reply, biz_id, agent_id)
        
        # 2. Capture du Nom (CRM)
        agent_reply = crm_service.extract_and_save_client_name(agent_reply, wa_id, biz_id)
        
        # 3. Extraction de la Reservation
        agent_reply = order_service.extract_and_save_reservation(agent_reply, wa_id, biz_id)
        
        # 4. Envoi du message WhatsApp
        whatsapp_service.send_message(wa_id, agent_reply, phone_id, business['token_wa'])

        # 5. Diffusion de la reponse du bot au Dashboard via SocketIO
        try:
            from app import socketio
            socketio.emit('nouveau_message', {
                'business_id': biz_id,
                'wa_id': wa_id,
                'content': agent_reply,
                'role': 'assistant',
                'timestamp': 'now'
            }, room=biz_id)
        except Exception as ws_err:
            print(f"Erreur SocketIO emit (bot reply): {ws_err}")
    
    except Exception as e:
        logger.error("Erreur dans le thread de traitement: %s", e)
