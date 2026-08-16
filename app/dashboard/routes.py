"""Routes Dashboard â€” Interface de gestion pour les partenaires business."""
from flask import Blueprint, request, render_template, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
from app import limiter
import threading
import time
import random
from app.services import whatsapp_service
from app.repositories import (
    tag_repo, business_repo, order_repo, client_repo, conversation_repo, sector_repo, employee_repo, catalog_repo, marketing_repo, agent_repo
)

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.before_request
def check_active_status():
    if request.endpoint and request.endpoint.startswith('dashboard.') and request.endpoint not in ['dashboard.login', 'dashboard.logout', 'dashboard.register', 'dashboard.pending']:
        user_id = session.get('user_id')
        if user_id:
            business = business_repo.get_by_id(user_id)
            if not business or not dict(business).get('is_active', 1):
                session.pop('user_id', None)
                return redirect(url_for('dashboard.login'))
            if not dict(business).get('whatsapp_phone_id'):
                return redirect(url_for('dashboard.pending', biz_id=user_id))

@dashboard_bp.context_processor
def inject_dashboard_context():
    user_id = session.get('user_id')
    ctx = {'global_unread_count': 0, 'plan': 'FREE'}
    if user_id:
        business = business_repo.get_by_id(user_id)
        if business:
            ctx['plan'] = dict(business).get('plan_abonnement', 'FREE')
        ctx['global_unread_count'] = conversation_repo.get_unread_message_count_for_business(user_id)
    return ctx

@dashboard_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")  # M-1 : max 10 tentatives/minute/IP
def login():
    """Connexion d'un partenaire business au tableau de bord."""
    if request.method == 'POST':
        biz_id_or_email = request.form.get('biz_id', '').strip().lower()
        password = request.form.get('password')

        business = business_repo.get_by_email(biz_id_or_email)
        if not business:
            business = business_repo.get_by_id(biz_id_or_email)
        if not business:
            slugified = biz_id_or_email.replace('@', '_').replace('.', '_')
            business = business_repo.get_by_id(slugified)

        if business and check_password_hash(business['password'], password):
            if not dict(business).get('is_active', 1):
                return render_template('auth/login.html', error="Compte inactif. Veuillez contacter le support.")
            session.clear() # CLEAR PREVIOUS BLOAT
            session.permanent = True
            session['user_id'] = business['id']
            return redirect(url_for('dashboard.admin_dashboard', biz_id=business['id']))
        else:
            return render_template('auth/login.html', error="Identifiants incorrects")

    return render_template('auth/login.html')


@dashboard_bp.route('/logout')
def logout():
    """Déconnexion du partenaire."""
    session.pop('user_id', None)
    return redirect(url_for('dashboard.login'))


@dashboard_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Inscription autonome d'un nouveau partenaire business (Wizard Onboarding)."""
    if request.method == 'POST':
        # On peut recevoir du JSON (API/Ajax via fetch dans le JS du Wizard) ou du Form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
            if hasattr(request, 'form') and 'bot_tasks[]' in request.form:
                data['bot_tasks'] = request.form.getlist('bot_tasks[]')
            elif 'bot_tasks' in data and isinstance(data['bot_tasks'], str):
                data['bot_tasks'] = [data['bot_tasks']]
                
        nom = data.get('nom')
        email = data.get('email', '').strip().lower()
        password = data.get('password')
        owner_name = data.get('owner_name')
        owner_phone = data.get('owner_phone')
        business_type = data.get('business_type')
        devise = data.get('devise', 'FCFA')
        requested_bot_phone = data.get('requested_bot_phone')
        
        ville = data.get('ville')
        bot_tasks = data.get('bot_tasks', [])
        tone = data.get('tone')
        business_info = data.get('business_info')

        if not (nom and email and password and owner_name and owner_phone and business_type and ville and tone):
            if request.is_json: return jsonify({"success": False, "error": "Champs manquants."})
            return render_template('auth/register.html', error="Veuillez remplir tous les champs.")

        if business_repo.get_by_email(email):
            if request.is_json: return jsonify({"success": False, "error": "Email dǸj utilisǸ."})
            return render_template('auth/register.html', error="Cet email est dǸj utilisǸ.")

        import uuid
        biz_id = str(uuid.uuid4())
        hashed = generate_password_hash(password)
        
        # Generation du prompt
        from app.services.ai_service import generate_bot_prompt_from_answers
        generated_prompt = generate_bot_prompt_from_answers(
            nom.strip(), business_type.strip(), ville.strip(), bot_tasks, tone.strip(), business_info.strip() if business_info else ""
        )

        business_repo.create_business_registration(
            biz_id, email, hashed, nom, owner_name, owner_phone, requested_bot_phone, business_type, devise, prompt=generated_prompt
        )
        
        # M-14 Notification au Master
        try:
            from app.services.notification_master_service import create_master_notification
            create_master_notification('inscription', 'Nouvelle Inscription Web', f"Nouveau Business (Web) : {nom}", biz_id)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to notify master: {e}")
        
        if request.is_json:
            return jsonify({'success': True, 'message': 'Inscription rǸussie.'})
        return redirect(url_for('dashboard.login'))

    return render_template('auth/register.html')


@dashboard_bp.route('/admin/<biz_id>/pending', methods=['GET', 'POST'])
def pending(biz_id):
    """Page d'attente VIP tant que l'ID Meta n'est pas renseignÃ©."""
    if 'user_id' not in session or session['user_id'] != biz_id:
        return redirect(url_for('dashboard.login'))

    business = business_repo.get_by_id(biz_id)
    if dict(business).get('whatsapp_phone_id'):
        return redirect(url_for('dashboard.admin_dashboard', biz_id=biz_id))

    if request.method == 'POST':
        requested_bot_phone = request.form.get('requested_bot_phone')
        owner_phone = request.form.get('owner_phone')
        
        if requested_bot_phone is not None:
            business_repo.set_requested_bot_phone(biz_id, requested_bot_phone)
            
        if owner_phone and owner_phone != dict(business).get('owner_phone'):
            business_repo.add_or_update(
                biz_id, business['nom'], business['whatsapp_phone_id'],
                business['token_wa'], business['password'], business['prompt'],
                business['msg_confirm'], business['msg_cancel'], business['msg_ready'],
                dict(business).get('business_type', 'restaurant'),
                dict(business).get('plan_abonnement', 'FREE'),
                dict(business).get('is_active', 1),
                owner_phone,
                dict(business).get('drip_j3_enabled', 0),
                dict(business).get('drip_j3_msg'),
                dict(business).get('debounce_delay', 3),
                0, # buffer_minutes default
                dict(business).get('email')
            )
            
        flash("Vos informations ont Ã©tÃ© enregistrÃ©es. Nous vous contacterons sous peu.", "success")
        return redirect(url_for('dashboard.pending', biz_id=biz_id))

    return render_template('dashboard/pending.html', business=business, biz_id=biz_id, active_page='')


@dashboard_bp.route('/admin/<biz_id>')
def admin_dashboard(biz_id):
    """Tableau de bord principal du partenaire."""
    if 'user_id' not in session or session['user_id'] != biz_id:
        return redirect(url_for('dashboard.login'))

    period = request.args.get('period', 'today')

    raw_reservations = order_repo.get_by_business(biz_id, period=period)
    business = business_repo.get_by_id(biz_id)
    
    reservations = []
    for r in raw_reservations:
        r_dict = dict(r)
        client = client_repo.get_or_create(biz_id, r['wa_id'])
        nom = client['nom'] if client else r['wa_id']
        # Migrate old "Client" to nice format
        if nom == "Client" and len(r['wa_id']) >= 4:
            nom = f"Client ...{r['wa_id'][-4:]}"
        r_dict['client_name'] = nom
        
        # Inject tags
        try:
            from app.repositories import tag_repo
            order_tags = tag_repo.get_tags_for_order(r['id'])
            r_dict['tags'] = [dict(t) for t in order_tags]
        except Exception as e:
            r_dict['tags'] = []
        reservations.append(r_dict)

    labels, values = order_repo.get_daily_activity(biz_id, period=period)
    stats = order_repo.get_stats(biz_id, period=period)
    peak_hour = order_repo.get_peak_hour(biz_id, period=period)

    biz_type = dict(business).get('business_type', 'restaurant') if business else 'restaurant'
    sector = sector_repo.get_by_id(biz_type)
    vocab = sector['vocab'] if sector else {}
    plan = dict(business).get('plan_abonnement', 'FREE') if business else 'BASIC'
    employees = employee_repo.get_by_business(biz_id) if plan in ('GROWTH', 'SCALE') else []
    
    # --- Custom dashboard stats ---
    import sqlite3
    import statistics
    import re
    from datetime import datetime
    from app.models.schema import get_db_path
    from app.repositories.order_repo import get_date_condition
    
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    date_cond = get_date_condition(period)
    history_date_cond = date_cond.replace('created_at', 'timestamp')
    client_date_cond = date_cond.replace('created_at', 'date_inscription')
    
    # 1. Total conversations (unique wa_id in history)
    cursor.execute(f"SELECT COUNT(DISTINCT wa_id) FROM history WHERE business_id = ? AND {history_date_cond}", (biz_id,))
    stats['conversations'] = cursor.fetchone()[0] or 0
    
    # 2. Nouveaux clients
    cursor.execute(f"SELECT COUNT(*) FROM clients WHERE business_id = ? AND {client_date_cond}", (biz_id,))
    stats['nouveaux_clients'] = cursor.fetchone()[0] or 0
    
    # 3. Automation rate (AI vs Human messages sent)
    cursor.execute(f"SELECT COUNT(*) FROM history WHERE business_id = ? AND role = 'assistant' AND {history_date_cond}", (biz_id,))
    total_assistant_msgs = cursor.fetchone()[0] or 0
    
    cursor.execute(f"SELECT COUNT(*) FROM history WHERE business_id = ? AND role = 'assistant' AND agent_id IS NOT NULL AND {history_date_cond}", (biz_id,))
    human_msgs = cursor.fetchone()[0] or 0
    
    if total_assistant_msgs > 0:
        stats['ai_rate'] = int(((total_assistant_msgs - human_msgs) / total_assistant_msgs) * 100)
    else:
        stats['ai_rate'] = 100
        
    # 4. Commandes & CA (Discovery+)
    cursor.execute(f"SELECT COUNT(*), SUM(montant) FROM reservations WHERE business_id = ? AND {date_cond} AND statut NOT LIKE 'Annul%' AND statut != 'Refusée'", (biz_id,))
    row = cursor.fetchone()
    stats['commandes'] = row[0] or 0
    stats['ca'] = row[1] or 0
    
    cursor.execute(f"SELECT COUNT(*) FROM reservations WHERE business_id = ? AND {date_cond} AND statut IN ('Confirmée', 'Livrée', 'En préparation')", (biz_id,))
    stats['commandes_acceptees'] = cursor.fetchone()[0] or 0
    
    cursor.execute(f"SELECT COUNT(*) FROM reservations WHERE business_id = ? AND {date_cond} AND statut IN ('Refusée', 'Annulée')", (biz_id,))
    stats['commandes_refusees'] = cursor.fetchone()[0] or 0

    # 5. Advanced Stats (Growth+)
    # Panier Moyen
    stats['panier_moyen'] = int(stats['ca'] / stats['commandes']) if stats['commandes'] > 0 else 0
    
    # Taux de Conversion (Commandes / Conversations uniques)
    stats['taux_conversion'] = round((stats['commandes'] / stats['conversations']) * 100, 1) if stats['conversations'] > 0 else 0
    
    # Top Produits (Normalisation basique)
    cursor.execute(f"SELECT details FROM reservations WHERE business_id = ? AND {date_cond} AND statut NOT LIKE 'Annul%' AND statut != 'Refusée'", (biz_id,))
    product_rows = cursor.fetchall()
    product_counts = {}
    for r in product_rows:
        text = r[0]
        if not text or "IA INDISPONIBLE" in text:
            continue
        # Split by comma or newline if multiple items
        items = re.split(r',|\n', text)
        for item in items:
            # Normalize: lower, remove qty (e.g. "2x", "1 "), remove size (e.g. "taille 45")
            item = item.lower().strip()
            item = re.sub(r'^[0-9]+[xX]?\s*', '', item)  # remove "2x " or "3 "
            item = re.sub(r'taille\s*[0-9A-Za-z]+', '', item)  # remove "taille 45"
            item = re.sub(r'\s+', ' ', item).strip()
            if len(item) > 2:
                product_counts[item] = product_counts.get(item, 0) + 1
    
    top_produits = sorted(product_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # 6. Advanced Stats (Scale+)
    # Temps de réponse (Médiane, hors > 60 min)
    cursor.execute(f"SELECT timestamp, role, wa_id FROM history WHERE business_id = ? AND {history_date_cond} ORDER BY wa_id, timestamp", (biz_id,))
    hist_rows = cursor.fetchall()
    
    response_times = []
    last_user_time = {}
    
    for r in hist_rows:
        try:
            ts = datetime.strptime(r['timestamp'], '%Y-%m-%d %H:%M:%S.%f')
        except:
            continue
        wa_id = r['wa_id']
        role = r['role']
        
        if role == 'user':
            last_user_time[wa_id] = ts
        elif role == 'assistant' and wa_id in last_user_time:
            delta = (ts - last_user_time[wa_id]).total_seconds()
            if delta < 3600:  # Exclure > 60 minutes
                response_times.append(delta)
            del last_user_time[wa_id]
            
    if response_times:
        median_rt = statistics.median(response_times)
        if median_rt < 60:
            stats['temps_reponse'] = f"{int(median_rt)} sec"
        else:
            stats['temps_reponse'] = f"{int(median_rt//60)} min"
    else:
        stats['temps_reponse'] = "-"
        
    # Taux de rétention (Clients ayant > 1 commande)
    cursor.execute(f"SELECT wa_id, COUNT(*) as c FROM reservations WHERE business_id = ? AND {date_cond} GROUP BY wa_id", (biz_id,))
    retention_rows = cursor.fetchall()
    clients_total = len(retention_rows)
    clients_recurrents = sum(1 for r in retention_rows if r['c'] > 1)
    stats['taux_retention'] = int((clients_recurrents / clients_total) * 100) if clients_total > 0 else 0
    
    # 7. Lists for dashboard
    from app.repositories.conversation_repo import get_conversations_for_business
    all_convs = get_conversations_for_business(biz_id)
    recent_convs = all_convs[:5] if all_convs else []
    
    recent_orders = reservations[:5]
    
    ai_words_used = (total_assistant_msgs - human_msgs) * 45
    ai_words_limit = 100000
    ai_usage_percent = min(int((ai_words_used / ai_words_limit) * 100), 100) if ai_words_limit > 0 else 0
    
    conn.close()

    return render_template('dashboard/admin.html',
                           reservations=reservations,
                           labels=labels,
                           values=values,
                           biz_id=biz_id,
                           stats=stats,
                           peak_hour=peak_hour,
                           business=business,
                           vocab=vocab,
                           plan=plan,
                           employees=employees,
                           recent_convs=recent_convs,
                           recent_orders=recent_orders,
                           ai_words_used=f"{ai_words_used:,}",
                           ai_words_limit=f"{ai_words_limit:,}",
                           ai_usage_percent=ai_usage_percent,
                           top_produits=top_produits,
                           current_period=period,
                           active_page='dashboard')


@dashboard_bp.route('/admin/<biz_id>/settings', methods=['GET', 'POST'])
def business_settings(biz_id):
    """ParamÃ¨tres du business (prompt, messages, mot de passe)."""
    if 'user_id' not in session or session['user_id'] != biz_id:
        return redirect(url_for('dashboard.login'))

    business = business_repo.get_by_id(biz_id)

    if request.method == 'POST':
        nom = request.form.get('nom')
        owner_phone = request.form.get('owner_phone')
        requested_bot_phone = request.form.get('requested_bot_phone')
        prompt = request.form.get('prompt')
        msg_confirm = request.form.get('msg_confirm')
        msg_cancel = request.form.get('msg_cancel')
        msg_ready = request.form.get('msg_ready')
        password = request.form.get('password')
        email = request.form.get('email', dict(business).get('email'))
        adresse = request.form.get('adresse', dict(business).get('adresse'))
        site_web = request.form.get('site_web', dict(business).get('site_web'))

        # Si un nouveau mot de passe est saisi, on le hache, sinon on garde l'ancien (dÃ©jÃ  hachÃ©)
        final_password = business['password']
        if password:
            final_password = generate_password_hash(password)

        current_plan = dict(business).get('plan_abonnement', 'FREE') if business else 'BASIC'
        
        # On conserve les paramÃ¨tres marketing existants
        drip_j3_enabled = dict(business).get('drip_j3_enabled', 0) if business else 0
        drip_j3_msg = dict(business).get('drip_j3_msg', None) if business else None
        
        # Debounce
        try:
            debounce_delay = int(request.form.get('debounce_delay', 3))
        except ValueError:
            debounce_delay = 3
        
        try:
            buffer_minutes = int(request.form.get('buffer_minutes', 0))
        except ValueError:
            buffer_minutes = 0

        # Horaires JSON
        horaires_json = request.form.get('horaires_json', '{}')
        business_repo.set_business_horaires(biz_id, horaires_json)

        business_repo.add_or_update(
            biz_id, nom, business['whatsapp_phone_id'],
            business['token_wa'], final_password, prompt,
            msg_confirm, msg_cancel, msg_ready,
            dict(business).get('business_type', 'restaurant') if business else 'restaurant',
            current_plan,
            dict(business).get('is_active', 1) if business else 1,
            owner_phone,
            drip_j3_enabled,
            drip_j3_msg,
            debounce_delay,
            buffer_minutes,
            email,
            adresse,
            site_web
        )
        
        if requested_bot_phone is not None:
            business_repo.update_bot_phone(biz_id, requested_bot_phone)

        daily_report_time = request.form.get('daily_report_time')
        if daily_report_time:
            business_repo.set_daily_report_time(biz_id, daily_report_time)
        
        flash("Les paramÃ¨tres ont Ã©tÃ© mis Ã  jour avec succÃ¨s !", "success")
        return redirect(url_for('dashboard.business_settings', biz_id=biz_id))

    biz_type = dict(business).get('business_type', 'restaurant') if business else 'restaurant'
    sector = sector_repo.get_by_id(biz_type)
    vocab = sector['vocab'] if sector else {}
    plan = dict(business).get('plan_abonnement', 'FREE') if business else 'BASIC'

    from app.repositories import employee_repo
    employees_rows = employee_repo.get_by_business(biz_id)
    employees_list = [dict(e) for e in employees_rows]
    
    agents_list = []
    try:
        from app.repositories import agent_repo
        agents = agent_repo.get_all_by_business(biz_id)
        agents_list = [dict(a) for a in agents]
    except Exception:
        pass
        
    return render_template('dashboard/settings.html', business=business, vocab=vocab, biz_id=biz_id, plan=plan, employees=employees_list, agents=agents_list, active_page='settings')


@dashboard_bp.route('/admin/<biz_id>/marketing-settings', methods=['POST'])
def marketing_settings(biz_id):
    """Sauvegarde les paramÃ¨tres de marketing automatisÃ© (Relance J+3)."""
    if 'user_id' not in session or session['user_id'] != biz_id:
        return redirect(url_for('dashboard.login'))

    business = business_repo.get_by_id(biz_id)
    plan = dict(business).get('plan_abonnement', 'FREE') if business else 'BASIC'

    if plan == 'SCALE':
        drip_j3_enabled = 1 if request.form.get('drip_j3_enabled') else 0
        drip_j3_msg = request.form.get('drip_j3_msg')

        business_repo.add_or_update(
            biz_id, business['nom'], business['whatsapp_phone_id'],
            business['token_wa'], business['password'], business['prompt'],
            business['msg_confirm'], business['msg_cancel'], business['msg_ready'],
            dict(business).get('business_type', 'restaurant') if business else 'restaurant',
            plan,
            dict(business).get('is_active', 1) if business else 1,
            dict(business).get('owner_phone'),
            drip_j3_enabled,
            drip_j3_msg,
            dict(business).get('debounce_delay', 3),
            0, # buffer_minutes default
            dict(business).get('email')
        )
        flash("ParamÃ¨tres de marketing automatisÃ© enregistrÃ©s avec succÃ¨s.", "success")
    else:
        flash("La sÃ©quence automatisÃ©e nÃ©cessite le plan PREMIUM.", "error")

    return redirect(url_for('dashboard.business_marketing', biz_id=biz_id))


def _emit_statut_commande(biz_id, res_id, statut):
    """Helper â€” diffuse le changement de statut d'une commande en temps rÃ©el."""
    try:
        from app import socketio
        socketio.emit('statut_commande', {
            'business_id': biz_id,
            'res_id': res_id,
            'statut': statut,
        }, room=biz_id)
    except Exception as e:
        logger.debug("[ORDER] Erreur Socket.IO statut: %s", e)


@dashboard_bp.route('/confirm/<int:res_id>', methods=['GET', 'POST'])
def confirm_reservation(res_id):
    """Confirmer une rÃ©servation et notifier le client."""
    if 'user_id' not in session:
        if request.method == 'POST':
            return jsonify({'error': 'Non autorisÃ©'}), 401
        return redirect(url_for('dashboard.login'))
    res = order_repo.get_res_info(res_id)
    if not res or res['business_id'] != session['user_id']:
        if request.method == 'POST':
            return jsonify({'error': 'AccÃ¨s refusÃ©'}), 403
        return "AccÃ¨s refusÃ©", 403

    if res['statut'] == "ConfirmÃ© âœ…":
        if request.method == 'POST':
            return jsonify({'status': 'ok', 'statut': 'ConfirmÃ© âœ…'})
        return redirect(url_for('dashboard.admin_dashboard', biz_id=res['business_id']))

    order_repo.update_status(res_id, "ConfirmÃ© âœ…")
    msg = res['msg_confirm'] if res['msg_confirm'] else "Votre demande est confirmÃ©e !"
    whatsapp_service.send_message(res['wa_id'], msg, res['whatsapp_phone_id'], res['token_wa'])
    _emit_statut_commande(res['business_id'], res_id, "ConfirmÃ© âœ…")
    if request.method == 'POST':
        return jsonify({'status': 'ok', 'statut': 'ConfirmÃ© âœ…'})
    return redirect(url_for('dashboard.admin_dashboard', biz_id=res['business_id']))


@dashboard_bp.route('/cancel/<int:res_id>', methods=['GET', 'POST'])
def cancel_reservation(res_id):
    """Annuler une rÃ©servation et notifier le client."""
    if 'user_id' not in session:
        if request.method == 'POST':
            return jsonify({'error': 'Non autorisÃ©'}), 401
        return redirect(url_for('dashboard.login'))
    res = order_repo.get_res_info(res_id)
    if not res or res['business_id'] != session['user_id']:
        if request.method == 'POST':
            return jsonify({'error': 'AccÃ¨s refusÃ©'}), 403
        return "AccÃ¨s refusÃ©", 403

    if res['statut'] == "AnnulÃ© âŒ":
        if request.method == 'POST':
            return jsonify({'status': 'ok', 'statut': 'AnnulÃ© âŒ'})
        return redirect(url_for('dashboard.admin_dashboard', biz_id=res['business_id']))

    order_repo.update_status(res_id, "AnnulÃ© âŒ")
    msg = res['msg_cancel'] if res['msg_cancel'] else "DÃ©solÃ©, nous ne pouvons pas confirmer..."
    whatsapp_service.send_message(res['wa_id'], msg, res['whatsapp_phone_id'], res['token_wa'])
    _emit_statut_commande(res['business_id'], res_id, "AnnulÃ© âŒ")
    if request.method == 'POST':
        return jsonify({'status': 'ok', 'statut': 'AnnulÃ© âŒ'})
    return redirect(url_for('dashboard.admin_dashboard', biz_id=res['business_id']))




@dashboard_bp.route('/handoff_cancel/<int:res_id>', methods=['POST'])
def handoff_cancel(res_id):
    """Le gÃ©rant refuse le transfert humain."""
    if 'user_id' not in session:
        return jsonify({'error': 'Non autorisÃ©'}), 401
        
    res = order_repo.get_res_info(res_id)
    if not res or res['business_id'] != session['user_id']:
        return jsonify({'error': 'AccÃ¨s refusÃ©'}), 403

    order_repo.update_status(res_id, "Indisponible âŒ")
    _emit_statut_commande(res['business_id'], res_id, "Indisponible âŒ")
    
    # Message d'excuse
    msg = "DÃ©solÃ©, tous nos conseillers sont actuellement occupÃ©s ou absents. N'hÃ©sitez pas Ã  reposer votre question plus tard ou Ã  continuer avec moi (l'assistant virtuel) !"
    whatsapp_service.send_message(res['wa_id'], msg, res['whatsapp_phone_id'], res['token_wa'])
    
    # RÃ©activer le bot (enlever le mode humain)
    from app.repositories import tag_repo, business_repo
    business_repo.set_human_mode(res['business_id'], res['wa_id'], False)
    
    # Notifier SocketIO que le mode a changÃ©
    try:
        from app import socketio
        socketio.emit('human_mode_toggled', {'business_id': res['business_id'], 'wa_id': res['wa_id'], 'state': False}, room=res['business_id'])
        # Ajouter le message dans le chat
        socketio.emit('nouveau_message', {
            'business_id': res['business_id'], 'wa_id': res['wa_id'], 'content': msg,
            'role': 'assistant', 'timestamp': 'now'
        }, room=res['business_id'])
    except Exception as e:
        logger.debug("[ORDER] Erreur Socket.IO statut: %s", e)

    return jsonify({'status': 'ok', 'statut': 'Indisponible âŒ'})


@dashboard_bp.route('/ready/<int:res_id>', methods=['GET', 'POST'])
def ready_reservation(res_id):
    """Marquer une rÃ©servation comme prÃªte et notifier le client."""
    if 'user_id' not in session:
        if request.method == 'POST':
            return jsonify({'error': 'Non autorisÃ©'}), 401
        return redirect(url_for('dashboard.login'))
    res = order_repo.get_res_info(res_id)
    if not res or res['business_id'] != session['user_id']:
        if request.method == 'POST':
            return jsonify({'error': 'AccÃ¨s refusÃ©'}), 403
        return "AccÃ¨s refusÃ©", 403

    business = business_repo.get_by_id(res['business_id'])
    biz_type = dict(business).get('business_type', 'restaurant') if business else 'restaurant'
    sector = sector_repo.get_by_id(biz_type)
    vocab = sector['vocab'] if sector else {}
    status_ready = vocab.get('status_ready', 'PrÃªt âœ…')

    if res['statut'] == status_ready:
        if request.method == 'POST':
            return jsonify({'status': 'ok', 'statut': status_ready})
        return redirect(url_for('dashboard.admin_dashboard', biz_id=res['business_id']))

    order_repo.update_status(res_id, status_ready)
    fallback_msg = f"C'est {vocab.get('btn_ready', 'prÃªt').lower()} !"
    msg = res['msg_ready'] if res['msg_ready'] else fallback_msg
    whatsapp_service.send_message(res['wa_id'], msg, res['whatsapp_phone_id'], res['token_wa'])
    _emit_statut_commande(res['business_id'], res_id, status_ready)
    if request.method == 'POST':
        return jsonify({'status': 'ok', 'statut': status_ready})
    return redirect(url_for('dashboard.admin_dashboard', biz_id=res['business_id']))



@dashboard_bp.route('/admin/<biz_id>/orders')
def business_orders(biz_id):
    """Affiche l'historique complet des commandes/rÃ©servations."""
    if 'user_id' not in session or session['user_id'] != biz_id:
        return redirect(url_for('dashboard.login'))

    business = business_repo.get_by_id(biz_id)
    if not business:
        return redirect(url_for('dashboard.login'))

    biz_type = dict(business).get('business_type', 'restaurant')
    sector = sector_repo.get_by_id(biz_type)
    vocab = sector['vocab'] if sector else {}
    plan = dict(business).get('plan_abonnement', 'FREE')

    reservations = order_repo.get_by_business(biz_id)
    
    # On ajoute le nom du client Ã  chaque rÃ©servation
    res_list = []
    for r in reservations:
        r_dict = dict(r)
        client = client_repo.get_or_create(biz_id, r['wa_id'])
        r_dict['client_name'] = client['nom'] if client else r['wa_id']
        
        # Inject tags
        try:
            from app.repositories import tag_repo
            order_tags = tag_repo.get_tags_for_order(r['id'])
            r_dict['tags'] = [dict(t) for t in order_tags]
        except Exception as e:
            r_dict['tags'] = []
        res_list.append(r_dict)

    return render_template('dashboard/orders.html', 
                           business=business, 
                           biz_id=biz_id, 
                           reservations=res_list, 
                           vocab=vocab,
                           plan=plan,
                           active_page='orders')


@dashboard_bp.route('/admin/<biz_id>/catalog')
def business_catalog(biz_id):
    """Interface de gestion du catalogue (menu, produits, services)."""
    if 'user_id' not in session or session['user_id'] != biz_id:
        return redirect(url_for('dashboard.login'))

    business = business_repo.get_by_id(biz_id)
    if not business:
        return redirect(url_for('dashboard.login'))

    biz_type = dict(business).get('business_type', 'restaurant')
    sector = sector_repo.get_by_id(biz_type)
    vocab = sector['vocab'] if sector else {}
    plan = dict(business).get('plan_abonnement', 'FREE')

    products = catalog_repo.get_by_business(biz_id)
    
    # Grouper par catÃ©gorie
    grouped_products = {}
    for p in products:
        cat = p['categorie'] or 'GÃ©nÃ©ral'
        if cat not in grouped_products:
            grouped_products[cat] = []
        grouped_products[cat].append(p)

    return render_template('dashboard/catalog.html',
                           business=business,
                           biz_id=biz_id,
                           grouped_products=grouped_products,
                           vocab=vocab,
                           plan=plan,
                           active_page='catalog')


@dashboard_bp.route('/admin/<biz_id>/catalog/add', methods=['POST'])
def add_catalog_product(biz_id):
    """API: Ajouter un produit au catalogue."""
    if 'user_id' not in session or session['user_id'] != biz_id:
        return redirect(url_for('dashboard.login'))

    import os
    from werkzeug.utils import secure_filename
    from flask import current_app

    nom = request.form.get('nom')
    categorie = request.form.get('categorie', 'GÃ©nÃ©ral')
    prix = request.form.get('prix', 0)
    description = request.form.get('description', '')
    is_visible = 1 if request.form.get('is_visible') == 'on' else 0
    duree_minutes = request.form.get('duree_minutes', 30)

    try:
        prix = int(prix)
    except ValueError:
        prix = 0

    try:
        duree_minutes = int(duree_minutes)
    except ValueError:
        duree_minutes = 30

    image_url = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            biz_upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'businesses', biz_id, 'products')
            os.makedirs(biz_upload_dir, exist_ok=True)
            filepath = os.path.join(biz_upload_dir, filename)
            file.save(filepath)
            # URL relative pour l'affichage
            image_url = f"/static/uploads/businesses/{biz_id}/products/{filename}"

    if nom:
        catalog_repo.add_product(biz_id, nom, prix, description, categorie, image_url, is_visible, duree_minutes)

    return redirect(url_for('dashboard.business_catalog', biz_id=biz_id))


@dashboard_bp.route('/admin/<biz_id>/catalog/toggle/<int:product_id>', methods=['GET', 'POST'])
def toggle_catalog_product(biz_id, product_id):
    """API: Activer/Désactiver un produit pour le bot."""
    if 'user_id' not in session or session['user_id'] != biz_id:
        return redirect(url_for('dashboard.login'))

    catalog_repo.toggle_availability(product_id, biz_id)
    return redirect(url_for('dashboard.business_catalog', biz_id=biz_id))


@dashboard_bp.route('/admin/<biz_id>/catalog/toggle_visibility/<int:product_id>', methods=['GET', 'POST'])
def toggle_catalog_visibility(biz_id, product_id):
    """API: Activer/Désactiver un produit sur la vitrine web."""
    if 'user_id' not in session or session['user_id'] != biz_id:
        return redirect(url_for('dashboard.login'))

    catalog_repo.toggle_visibility(product_id, biz_id)
    return redirect(url_for('dashboard.business_catalog', biz_id=biz_id))


@dashboard_bp.route('/admin/<biz_id>/catalog/delete/<int:product_id>')
def delete_catalog_product(biz_id, product_id):
    """API: Supprimer un produit."""
    if 'user_id' not in session or session['user_id'] != biz_id:
        return redirect(url_for('dashboard.login'))

    catalog_repo.delete_product(product_id, biz_id)
    return redirect(url_for('dashboard.business_catalog', biz_id=biz_id))


@dashboard_bp.route('/admin/<biz_id>/chat')
def chat_inbox(biz_id):
    """Boite de reception â€” Interface de chat temps reel."""
    if 'user_id' not in session or session['user_id'] != biz_id:
        return redirect(url_for('dashboard.login'))

    business = business_repo.get_by_id(biz_id)
    conversations = conversation_repo.get_conversations_for_business(biz_id)
    unread_counts = conversation_repo.get_unread_message_counts_by_client(biz_id)

    biz_type = dict(business).get('business_type', 'restaurant') if business else 'restaurant'
    sector = sector_repo.get_by_id(biz_type)
    vocab = sector['vocab'] if sector else {}

    plan = dict(business).get('plan_abonnement', 'FREE') if business else 'BASIC'
    business_tags = tag_repo.get_business_tags(biz_id)

    return render_template('dashboard/chat.html',
                           business_tags=business_tags,
                           biz_id=biz_id,
                           business=business,
                           conversations=conversations,
                           unread_counts=unread_counts,
                           vocab=vocab,
                           plan=plan,
                           active_page='chat')


@dashboard_bp.route('/admin/<biz_id>/chat/<wa_id>')
def get_chat_history(biz_id, wa_id):
    """API JSON â€” Historique d'une conversation."""
    if 'user_id' not in session or session['user_id'] != biz_id:
        return jsonify({'error': 'Non autorise'}), 403

    conversation_repo.mark_conversation_as_read(wa_id, biz_id)

    messages = conversation_repo.get_full_history(wa_id, biz_id, limit=50)
    is_human = business_repo.is_human_mode(biz_id, wa_id)
    client = client_repo.get_or_create(biz_id, wa_id)
    
    c_nom = client['nom'] if client and client['nom'] else ''
    c_disp = client['display_name'] if client and client['display_name'] else ''
    c_main = c_disp or c_nom or wa_id

    tags_rows = tag_repo.get_tags_for_client(wa_id, biz_id)
    tags = [{"name": t['name'], "color": t['color']} for t in tags_rows]
    
    last_order_row = order_repo.get_last_for_user(wa_id, biz_id)
    last_order = None
    if last_order_row:
        last_order = {
            "id": last_order_row['id'],
            "statut": last_order_row['statut'],
            "details": last_order_row['details'],
            "montant": last_order_row['montant'],
            "created_at": last_order_row['created_at']
        }

    crm_data = {
        "name": c_nom,
        "display_name": c_disp,
        "date_inscription": client.get('date_inscription') if client else None,
        "tags": tags,
        "last_order": last_order
    }

    return jsonify({
        'messages': messages,
        'is_human_mode': is_human,
        'client_name': c_main,
        'client_real_name': c_nom,
        'client_display_name': c_disp,
        'wa_id': wa_id,
        'crm': crm_data
    })



@dashboard_bp.route('/admin/<biz_id>/chat/<wa_id>/tags', methods=['POST'])
def add_chat_client_tag(biz_id, wa_id):
    if 'user_id' not in session or session['user_id'] != biz_id:
        return jsonify({'error': 'Non autorise'}), 403

    data = request.get_json() or {}
    tag_id = data.get('tag_id')
    if not tag_id:
        return jsonify({'error': 'Missing tag_id'}), 400

    try:
        tag_repo.add_tag_to_client(wa_id, biz_id, tag_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/admin/<biz_id>/chat/<wa_id>/profile', methods=['PUT'])
def update_chat_client_profile(biz_id, wa_id):
    if 'user_id' not in session or session['user_id'] != biz_id:
        return jsonify({'error': 'Non autorise'}), 403

    data = request.get_json() or {}
    nom = data.get('nom')
    display_name = data.get('display_name')

    try:
        if nom is not None:
            client_repo.update_name(biz_id, wa_id, nom.strip())
        if display_name is not None:
            client_repo.set_display_name(biz_id, wa_id, display_name.strip())
            
        return jsonify({"success": True, "message": "Profil mis à jour"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@dashboard_bp.route('/admin/<biz_id>/chat/send', methods=['POST'])
def send_chat_message(biz_id):
    """Envoie un message humain (gerant) au client via WhatsApp."""
    if 'user_id' not in session or session['user_id'] != biz_id:
        return jsonify({'error': 'Non autorise'}), 403

    data = request.get_json()
    wa_id = data.get('wa_id')
    text = data.get('text')

    if not wa_id or not text:
        return jsonify({'error': 'wa_id et text requis'}), 400

    business = business_repo.get_by_id(biz_id)
    if not business:
        return jsonify({'error': 'Business introuvable'}), 404
        
    # Vérification fenêtre 24h
    from datetime import datetime
    last_user_msg_time = conversation_repo.get_last_user_message_timestamp(wa_id, biz_id)
    if last_user_msg_time:
        try:
            last_dt = datetime.strptime(last_user_msg_time, '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            try:
                last_dt = datetime.strptime(last_user_msg_time, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                last_dt = datetime.now()
        if (datetime.now() - last_dt).total_seconds() > 24 * 3600:
            return jsonify({'error': 'Le client ne vous a pas écrit depuis plus de 24h. Envoi impossible.'}), 400
    else:
        # Aucun message du client ? Interdit d'initier avec un message libre
        return jsonify({'error': 'Le client ne vous a jamais écrit. Envoi impossible.'}), 400

    # Sauvegarde en base avec role 'agent' (statut processing par défaut pour la latence, puis sent après l'API)
    msg_id = conversation_repo.save_message(wa_id, 'agent', text, biz_id, message_status='processing')

    # Envoi via l'API WhatsApp
    response = whatsapp_service.send_text_message(wa_id, text, business['whatsapp_phone_id'], business['token_wa'])

    if response and 'messages' in response:
        meta_id = response['messages'][0]['id']
        conversation_repo.update_message_status_by_id(msg_id, 'sent', meta_id)
    else:
        conversation_repo.update_message_status_by_id(msg_id, 'failed')
        return jsonify({'error': 'Erreur lors de l\'envoi du message via WhatsApp.'}), 500
    
    # Si on est en mode humain, on réinitialise le timer à cet instant précis
    if business_repo.is_human_mode(biz_id, wa_id):
        business_repo.set_human_mode(biz_id, wa_id, True)

    # Diffusion au Dashboard via SocketIO
    try:
        from app import socketio
        socketio.emit('nouveau_message', {
            'business_id': biz_id,
            'wa_id': wa_id,
            'message_id': msg_id,
            'content': text,
            'role': 'agent',
            'timestamp': 'now',
            'message_type': 'text',
            'message_status': 'sent'
        }, room=biz_id)
    except Exception as e:
        print(f"Erreur SocketIO: {e}")

    return jsonify({'status': 'sent'})


@dashboard_bp.route('/admin/<biz_id>/chat/upload_media', methods=['POST'])
def upload_media_route(biz_id):
    """Point d'entrée pour l'upload de médias depuis le chat (image, audio)."""
    if 'user_id' not in session or session['user_id'] != biz_id:
        return jsonify({'error': 'Non autorisé'}), 403

    wa_id = request.form.get('wa_id')
    media_type = request.form.get('media_type')  # 'image' ou 'audio'
    
    if not wa_id or not media_type or 'file' not in request.files:
        return jsonify({'error': 'Paramètres invalides'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Aucun fichier sélectionné'}), 400

    business = business_repo.get_by_id(biz_id)
    if not business:
        return jsonify({'error': 'Business introuvable'}), 404

    # Vérification fenêtre 24h
    from datetime import datetime
    last_user_msg_time = conversation_repo.get_last_user_message_timestamp(wa_id, biz_id)
    if last_user_msg_time:
        try:
            last_dt = datetime.strptime(last_user_msg_time, '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            try:
                last_dt = datetime.strptime(last_user_msg_time, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                last_dt = datetime.now()
        if (datetime.now() - last_dt).total_seconds() > 24 * 3600:
            return jsonify({'error': 'Le client ne vous a pas écrit depuis plus de 24h.'}), 400
    else:
        return jsonify({'error': 'Le client ne vous a jamais écrit.'}), 400

    # Validation MIME & Taille
    import os
    from werkzeug.utils import secure_filename
    from flask import current_app
    from app.services.media_worker import enqueue_media_processing
    
    mime_type = file.mimetype
    if media_type == 'image':
        if not mime_type.startswith('image/'):
            return jsonify({'error': 'Le fichier n\'est pas une image.'}), 400
        if request.content_length > 5 * 1024 * 1024:
            return jsonify({'error': 'Image trop volumineuse (max 5 Mo).'}), 400
    elif media_type == 'audio':
        if not mime_type.startswith('audio/') and not mime_type.startswith('video/'): # Safari can send video/mp4 for audio
            return jsonify({'error': 'Le fichier n\'est pas un audio.'}), 400
        if request.content_length > 16 * 1024 * 1024:
            return jsonify({'error': 'Audio trop volumineux (max 16 Mo).'}), 400
    else:
        return jsonify({'error': 'Type de média non supporté.'}), 400

    # Sauvegarder dans temp
    temp_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', os.path.join(current_app.root_path, 'static', 'uploads')), 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    import uuid
    ext = os.path.splitext(secure_filename(file.filename))[1]
    temp_filename = f"{uuid.uuid4()}_temp{ext}"
    temp_path = os.path.join(temp_dir, temp_filename)
    file.save(temp_path)
    
    # Enregistrer le message avec statut 'processing'
    content = '📸 Image envoyée' if media_type == 'image' else '🎤 Message vocal'
    msg_id = conversation_repo.save_message(
        wa_id=wa_id, role='agent', content=content, business_id=biz_id,
        message_type=media_type, message_status='processing'
    )
    
    # Démarrer le worker asynchrone
    enqueue_media_processing(
        current_app._get_current_object(), biz_id, wa_id, temp_path, mime_type, media_type, dict(business), msg_id
    )
    
    # Diffuser SocketIO (processing) pour afficher le message gris/chargement
    try:
        from app import socketio
        socketio.emit('nouveau_message', {
            'business_id': biz_id,
            'wa_id': wa_id,
            'message_id': msg_id,
            'content': content,
            'role': 'agent',
            'timestamp': 'now',
            'message_type': media_type,
            'message_status': 'processing'
        }, room=biz_id)
    except Exception as e:
        print(f"Erreur SocketIO: {e}")

    return jsonify({'status': 'processing', 'message_id': msg_id})


@dashboard_bp.route('/admin/<biz_id>/chat/manual-order', methods=['POST'])
def manual_order(biz_id):
    """Enregistre manuellement une commande/rÃ©servation depuis le chat."""
    if 'user_id' not in session or session['user_id'] != biz_id:
        return jsonify({'error': 'Non autorise'}), 403

    data = request.get_json()
    wa_id = data.get('wa_id')
    nature = data.get('nature')
    montant = data.get('montant', 0)

    if not wa_id or not nature:
        return jsonify({'error': 'wa_id et nature requis'}), 400

    try:
        montant = int(montant)
    except ValueError:
        montant = 0

    business = business_repo.get_by_id(biz_id)
    if not business:
        return jsonify({'error': 'Business introuvable'}), 404

    # On enregistre proprement comme si l'IA l'avait fait
    order_repo.save_reservation(biz_id, wa_id, details=nature, priorite="Haute", montant=montant)
    
    return jsonify({"status": "success", "message": "Commande enregistrÃ©e avec succÃ¨s."})


@dashboard_bp.route('/admin/<biz_id>/chat/rewrite', methods=['POST'])
def rewrite_message(biz_id):
    if 'user_id' not in session or session['user_id'] != biz_id:
        return jsonify({'error': 'Non autorise'}), 403
    
    data = request.get_json() or {}
    text = data.get('text', '')
    if not text:
        return jsonify({'error': 'Texte vide'}), 400
        
    try:
        from app.services.ai_service import rewrite_chat_message
        improved_text = rewrite_chat_message(biz_id, text)
        return jsonify({'success': True, 'text': improved_text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/admin/<biz_id>/chat/toggle-mode', methods=['POST'])
def toggle_human_mode(biz_id):
    """Active ou desactive le mode humain pour une conversation."""
    if 'user_id' not in session or session['user_id'] != biz_id:
        return jsonify({'error': 'Non autorise'}), 403

    data = request.get_json()
    wa_id = data.get('wa_id')
    activate = data.get('activate', True)

    if not wa_id:
        return jsonify({'error': 'wa_id requis'}), 400

    business_repo.set_human_mode(biz_id, wa_id, activate)

    return jsonify({
        'status': 'ok',
        'is_human_mode': activate,
        'wa_id': wa_id
    })


@dashboard_bp.route('/admin/<biz_id>/clients/<wa_id>/edit', methods=['POST'])
def edit_client(biz_id, wa_id):
    """Met à jour le nom légal et le display_name d'un client."""
    if 'user_id' not in session or session['user_id'] != biz_id:
        return jsonify({'error': 'Non autorisé'}), 403

    nom = request.form.get('nom', '').strip()
    display_name = request.form.get('display_name', '').strip()

    client_repo.update_name(biz_id, wa_id, nom)
    client_repo.set_display_name(biz_id, wa_id, display_name)
    
    flash("Profil client mis à jour avec succès.", "success")
    # Redirect back to where the user came from (clients list or chat view)
    return redirect(request.referrer or url_for('dashboard.business_clients', biz_id=biz_id))

@dashboard_bp.route('/admin/<biz_id>/clients')
def business_clients(biz_id):
    """Mini-CRM : Liste des clients ayant interagi avec le business."""
    if 'user_id' not in session or session['user_id'] != biz_id:
        return redirect(url_for('dashboard.login'))

    business = business_repo.get_by_id(biz_id)
    # On rÃ©utilise la fonction qui donne les conversations uniques avec nom et dernier message
    clients = conversation_repo.get_conversations_for_business(biz_id)

    biz_type = dict(business).get('business_type', 'restaurant') if business else 'restaurant'
    sector = sector_repo.get_by_id(biz_type)
    vocab = sector['vocab'] if sector else {}
    plan = dict(business).get('plan_abonnement', 'FREE') if business else 'BASIC'

    return render_template('dashboard/clients.html',
                           biz_id=biz_id,
                           business=business,
                           clients=clients,
                           vocab=vocab,
                           plan=plan,
                           active_page='clients')


@dashboard_bp.route('/admin/<biz_id>/marketing')
def business_marketing(biz_id):
    """Page Marketing (accÃ¨s rÃ©servÃ© aux plans PRO et PREMIUM)."""
    if 'user_id' not in session or session['user_id'] != biz_id:
        return redirect(url_for('dashboard.login'))

    business = business_repo.get_by_id(biz_id)
    plan = dict(business).get('plan_abonnement', 'FREE') if business else 'BASIC'

    if plan not in ('GROWTH', 'SCALE'):
        return redirect(url_for('dashboard.admin_dashboard', biz_id=biz_id))

    biz_type = dict(business).get('business_type', 'restaurant') if business else 'restaurant'
    sector = sector_repo.get_by_id(biz_type)
    vocab = sector['vocab'] if sector else {}
    clients = conversation_repo.get_conversations_for_business(biz_id)

    from app.repositories import marketing_repo
    campaigns = marketing_repo.get_campaigns_for_business(biz_id)
    return render_template('dashboard/marketing.html',
                           biz_id=biz_id,
                           business=business,
                           vocab=vocab,
                           plan=plan,
                           clients=clients,
                           campaigns=campaigns,
                           active_page='marketing')


@dashboard_bp.route('/admin/<biz_id>/generate-campaign-copy', methods=['POST'])
def generate_campaign_copy(biz_id):
    if 'user_id' not in session or session['user_id'] != biz_id:
        return jsonify({"error": "Non autorisÃ©"}), 403

    business = business_repo.get_by_id(biz_id)
    if not business:
        return jsonify({"error": "Business introuvable"}), 404

    message = ''
    if request.is_json:
        message = request.json.get('text', request.json.get('message', '')).strip()
    else:
        message = request.form.get('text', '').strip()

    if not message:
        return jsonify({"success": False, "error": "Message vide"}), 400

    from app.services.ai_service import improve_marketing_message
    
    try:
        improved = improve_marketing_message(message)
        return jsonify({"success": True, "improved_text": improved, "copy": improved})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==========================================
# GESTION DES EMPLOYÃ‰S (Ã‰QUIPE)
# ==========================================
@dashboard_bp.route('/admin/<biz_id>/employees', methods=['GET', 'POST'])
def business_employees(biz_id):
    """GÃ¨re l'Ã©quipe (employÃ©s et leurs horaires)."""
    if 'user_id' not in session or session['user_id'] != biz_id:
        return redirect(url_for('dashboard.login'))

    business = business_repo.get_by_id(biz_id)
    plan = dict(business).get('plan_abonnement', 'FREE')

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            nom = request.form.get('nom')
            poste = request.form.get('poste')
            horaires_json = request.form.get('horaires_json')
            employee_repo.add(biz_id, nom, poste, horaires_json)
            flash("EmployÃ© ajoutÃ©.", "success")
        elif action == 'edit':
            employee_id = request.form.get('employee_id')
            nom = request.form.get('nom')
            poste = request.form.get('poste')
            horaires_json = request.form.get('horaires_json')
            employee_repo.update(employee_id, nom, poste, horaires_json)
            flash("EmployÃ© modifiÃ©.", "success")
        elif action == 'delete':
            employee_id = request.form.get('employee_id')
            employee_repo.delete(employee_id)
            flash("EmployÃ© supprimÃ©.", "success")
        return redirect(url_for('dashboard.business_employees', biz_id=biz_id))

    employees = employee_repo.get_by_business(biz_id)
    
    biz_type = dict(business).get('business_type', 'restaurant') if business else 'restaurant'
    sector = sector_repo.get_by_id(biz_type)
    vocab = sector['vocab'] if sector else {}

    return redirect(url_for('dashboard.business_settings', biz_id=biz_id) + '?tab=tab-employes')

# ==========================================
# AGENDA (FULLCALENDAR)
# ==========================================
@dashboard_bp.route('/admin/<biz_id>/agenda')
def business_agenda(biz_id):
    """Affiche l'agenda visuel des réservations."""
    if 'user_id' not in session or session['user_id'] != biz_id:
        return redirect(url_for('dashboard.login'))

    business = business_repo.get_by_id(biz_id)
    plan = dict(business).get('plan_abonnement', 'FREE')
    employees = employee_repo.get_by_business(biz_id)
    agents = agent_repo.get_all_by_business(biz_id)
    
    from datetime import datetime
    upcoming_appointments = []
    raw_upcoming = order_repo.get_upcoming_appointments(biz_id, limit=5)
    
    # Mois en français pour un bel affichage
    mois_fr = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sep", "Oct", "Nov", "Déc"]
    jours_fr = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    
    for rdv in raw_upcoming:
        rdv_dict = dict(rdv)
        if rdv_dict['date_heure_debut']:
            try:
                dt = datetime.strptime(rdv_dict['date_heure_debut'][:16], '%Y-%m-%d %H:%M')
                rdv_dict['date_str'] = f"{jours_fr[dt.weekday()]} {dt.day} {mois_fr[dt.month-1]}"
                rdv_dict['time_str'] = dt.strftime('%H:%M')
            except Exception:
                rdv_dict['date_str'] = rdv_dict['date_heure_debut'][:10]
                rdv_dict['time_str'] = rdv_dict['date_heure_debut'][11:16]
        upcoming_appointments.append(rdv_dict)
        
    agenda_stats = order_repo.get_agenda_stats(biz_id)
    
    return render_template('dashboard/agenda.html',
                           biz_id=biz_id,
                           business=business,
                           plan=plan,
                           employees=employees,
                           agents=agents,
                           upcoming_appointments=upcoming_appointments,
                           agenda_stats=agenda_stats,
                           active_page='agenda')

@dashboard_bp.route('/api/agenda/events/<biz_id>')
def api_agenda_events(biz_id):
    """Retourne les rÃ©servations (orders) au format FullCalendar."""
    if 'user_id' not in session or session['user_id'] != biz_id:
        return jsonify([])

    agent_filter = request.args.get('agent', 'all')
    type_filter = request.args.get('type', 'all')

    orders = order_repo.get_by_business(biz_id, period='all')
    events = []
    for order in orders:
        # Apply filters
        order_dict = dict(order)
        if agent_filter != 'all' and str(order_dict.get('employee_id')) != agent_filter:
            continue
        if type_filter != 'all' and order_dict.get('details') != type_filter:
            continue

        if order['date_heure_debut']:
            title_name = order['client_name'] if order['client_name'] else (f"+{order['wa_id']}" if order['wa_id'] else "Inconnu")
            # Replace space with T to make it ISO 8601 compliant (fixes iOS Safari bug where events don't show)
            start_iso = order['date_heure_debut'].replace(' ', 'T')
            
            # Map statut to color for FullCalendar
            statut = order['statut']
            color = 'purple' # default
            if statut == 'Confirmé':
                color = 'green'
            elif statut == 'En attente':
                color = 'orange'
            elif statut == 'Terminé' or statut.startswith('Prêt') or statut.startswith('Livré'):
                color = 'blue'
            elif statut == 'Annulé':
                color = 'red'

            events.append({
                "id": order['id'],
                "title": f"{order['details']}",
                "start": start_iso,
                # "end": sera calculÃ© si nÃ©cessaire (date_heure_debut + duree)
                "extendedProps": {
                    "client": title_name,
                    "statut": statut,
                    "employee_id": order['employee_id'],
                    "color": color,
                    "agent": "Agent" # Can be mapped if needed
                }
            })
    return jsonify(events)

@dashboard_bp.route('/api/agenda/create/<biz_id>', methods=['POST'])
def api_agenda_create(biz_id):
    """Création manuelle d'une réservation depuis l'agenda."""
    if 'user_id' not in session or session['user_id'] != biz_id:
        return jsonify({"success": False, "error": "Non autorisé"}), 403
        
    data = request.json
    if not data:
        return jsonify({"success": False, "error": "Données manquantes"}), 400
        
    client_name = data.get('client_name')
    phone = data.get('phone', '').strip()
    date = data.get('date')
    time = data.get('time')
    details = data.get('details')
    agent_id = data.get('agent_id')
    
    if not client_name or not date or not time:
        return jsonify({"success": False, "error": "Veuillez remplir le nom, la date et l'heure."}), 400
        
    date_heure_debut = f"{date} {time}"
    
    wa_id = None
    if phone:
        # Nettoyer le numéro pour en faire un wa_id valide (que des chiffres)
        wa_id = ''.join(filter(str.isdigit, phone))
        if not wa_id:
            wa_id = None
            
    try:
        # Si on a un vrai numéro, on peut créer le client proprement
        if wa_id:
            from app.repositories import client_repo
            import sqlite3
            from app.models.schema import get_db_path
            
            client = client_repo.get_or_create(biz_id, wa_id)
            if client['nom'] != client_name:
                # Mettre à jour le nom si c'est un nouveau ou s'il a changé (simplifié)
                conn = sqlite3.connect(get_db_path())
                c = conn.cursor()
                c.execute("UPDATE clients SET nom = ? WHERE business_id = ? AND wa_id = ?", (client_name, biz_id, wa_id))
                conn.commit()
                conn.close()

        # Create order
        order_repo.save_reservation(
            biz_id=biz_id,
            wa_id=wa_id,
            details=details,
            priorite='Normale',
            montant=0,
            date_heure_debut=date_heure_debut,
            employee_id=agent_id,
            client_name_manual=client_name if not wa_id else None,
            statut='Planifié'
        )
        return jsonify({"success": True})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

# ==========================================
# GESTION DES AGENTS IA (PREMIUM)
# ==========================================
@dashboard_bp.route('/admin/<biz_id>/agents', methods=['GET', 'POST'])
def business_agents(biz_id):
    """GÃ¨re l'Ã©quipe d'agents IA (rÃ´les, permissions, instructions)."""
    if 'user_id' not in session or session['user_id'] != biz_id:
        return redirect(url_for('dashboard.login'))

    business = business_repo.get_by_id(biz_id)
    plan = business['plan_abonnement']
    if plan != 'SCALE':
        return redirect(url_for('dashboard.admin_dashboard', biz_id=biz_id))

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            name = request.form.get('name')
            role = request.form.get('role')
            system_prompt = request.form.get('system_prompt')
            intent_keywords = request.form.get('intent_keywords')
            
            permissions = {
                'can_propose_promo': request.form.get('can_propose_promo') == 'on',
                'can_escalate': request.form.get('can_escalate') == 'on',
                'max_tokens': int(request.form.get('max_tokens', 200)),
                'response_tone': request.form.get('response_tone', 'standard')
            }
            
            agent_repo.add(biz_id, name, role, system_prompt, intent_keywords, permissions)
            flash("Agent IA crÃ©Ã© avec succÃ¨s.", "success")
            
        elif action == 'edit':
            agent_id = request.form.get('agent_id')
            name = request.form.get('name')
            role = request.form.get('role')
            system_prompt = request.form.get('system_prompt')
            intent_keywords = request.form.get('intent_keywords')
            
            permissions = {
                'can_propose_promo': request.form.get('can_propose_promo') == 'on',
                'can_escalate': request.form.get('can_escalate') == 'on',
                'max_tokens': int(request.form.get('max_tokens', 200)),
                'response_tone': request.form.get('response_tone', 'standard')
            }
            
            agent_repo.update(agent_id, biz_id, name, role, system_prompt, intent_keywords, permissions)
            flash("Agent IA modifiÃ© avec succÃ¨s.", "success")
            
        elif action == 'delete':
            agent_id = request.form.get('agent_id')
            agent_repo.delete(agent_id)
            flash("Agent IA supprimé.", "success")
            
        elif action == 'toggle_agent':
            agent_id = request.form.get('agent_id')
            is_active = int(request.form.get('is_active', 1))
            agent_repo.toggle_active(agent_id, biz_id, is_active)
            status = "activé" if is_active else "désactivé"
            flash(f"Agent IA {status}.", "success")
            
        elif action == 'set_routing':
            routing_mode = request.form.get('routing_mode')
            allowed_modes = {'visible', 'invisible'}
            if routing_mode in allowed_modes:
                business_repo.update_routing_mode(biz_id, routing_mode)
                flash("Mode de routage mis à jour.", "success")
            else:
                flash("Mode de routage invalide.", "error")
            
        return redirect(url_for('dashboard.business_agents', biz_id=biz_id))

    agents = agent_repo.get_by_business(biz_id)
    stats = agent_repo.get_agent_stats(biz_id)
    
    # Pre-parse permissions pour l'affichage
    import json
    agents_list = []
    for a in agents:
        a_dict = dict(a)
        a_dict['settings'] = json.loads(a_dict.get('agent_settings_json', '{}'))
        a_dict['stats'] = stats.get(a_dict['id'], {'messages_handled': 0})
        agents_list.append(a_dict)
        
    # Templates par dÃ©faut
    default_templates = [
        {
            "name": "Alex - Vendeur Pro",
            "role": "Vente & Conseil",
            "intent_keywords": "prix, acheter, commande, menu, catalogue, combien, promo",
            "system_prompt": "Ton objectif principal est de convertir la discussion en vente. Sois trÃ¨s chaleureux, n'hÃ©site pas Ã  recommander nos meilleurs produits et Ã  pousser Ã  l'achat.",
            "can_propose_promo": True,
            "can_escalate": False
        },
        {
            "name": "Sarah - Support Doux",
            "role": "Support Client",
            "intent_keywords": "problÃ¨me, retard, plainte, erreur, remboursement, annuler",
            "system_prompt": "Ton objectif est de rassurer le client et rÃ©soudre son problÃ¨me. Sois trÃ¨s empathique, excuse-toi pour le dÃ©rangement.",
            "can_propose_promo": False,
            "can_escalate": True
        },
        {
            "name": "Sam - RÃ©servation",
            "role": "Gestionnaire de Rendez-vous",
            "intent_keywords": "rÃ©server, rdv, table, place, quand, dispo",
            "system_prompt": "Ton objectif est de prendre les dÃ©tails de la rÃ©servation de maniÃ¨re stricte: nom, date, heure, nombre de personnes.",
            "can_propose_promo": False,
            "can_escalate": False
        }
    ]

    return redirect(url_for('dashboard.business_settings', biz_id=biz_id) + '?tab=tab-agents')

@dashboard_bp.route('/admin/<biz_id>/send-campaign', methods=['POST'])
def send_campaign(biz_id):
    if 'user_id' not in session or session['user_id'] != biz_id:
        return redirect(url_for('dashboard.login'))

    business = business_repo.get_by_id(biz_id)
    target = request.form.get('target', 'all')
    title = request.form.get('title', 'Nouvelle Campagne')
    message_template = request.form.get('message', '')

    if not message_template.strip():
        return redirect(url_for('dashboard.business_marketing', biz_id=biz_id))

    plan = dict(business).get('plan_abonnement', 'FREE')
    from app.repositories import marketing_repo
    today_count = marketing_repo.get_today_campaigns_count(biz_id)
    
    if plan == 'BASIC' and today_count >= 1:
        return redirect(url_for('dashboard.business_marketing', biz_id=biz_id, error="Limite de 1 campagne par jour (BASIC)."))
    elif plan == 'PRO' and today_count >= 1:
        return redirect(url_for('dashboard.business_marketing', biz_id=biz_id, error="Limite de 1 campagne par jour (PRO)."))
    elif plan == 'PREMIUM' and today_count >= 3:
        return redirect(url_for('dashboard.business_marketing', biz_id=biz_id, error="Limite de 3 campagnes par jour (PREMIUM)."))

    if plan == 'BASIC':
        target = 'all'
    elif plan == 'PRO' and target == 'inactive':
        target = 'active'

    all_clients = conversation_repo.get_conversations_for_business(biz_id)
    import datetime
    clients_to_send = []

    if target == 'active':
        limit_date = datetime.datetime.now() - datetime.timedelta(days=7)
        for c in all_clients:
            try:
                ts = datetime.datetime.fromisoformat(c['last_timestamp'])
                if ts >= limit_date:
                    clients_to_send.append(c)
            except Exception:
                clients_to_send.append(c)
    elif target == 'inactive':
        limit_date = datetime.datetime.now() - datetime.timedelta(days=30)
        for c in all_clients:
            try:
                ts = datetime.datetime.fromisoformat(c['last_timestamp'])
                if ts < limit_date:
                    clients_to_send.append(c)
            except Exception:
                pass # S'il y a un souci, on ne spamme pas
    else:
        clients_to_send = all_clients

    max_clients = 100 if plan == 'BASIC' else (500 if plan == 'PRO' else len(clients_to_send))
    clients_to_send = clients_to_send[:max_clients]

    if clients_to_send:
        marketing_repo.enqueue_campaign(biz_id, clients_to_send, message_template, title, target)
        flash(f"La campagne a ete mise en file d'attente pour {len(clients_to_send)} clients !", "success")

    return redirect(url_for('dashboard.business_marketing', biz_id=biz_id))



@dashboard_bp.route('/admin/<biz_id>/payments')
def business_payments(biz_id):
    """Page Paiements (accÃ¨s rÃ©servÃ© au plan PREMIUM)."""
    if 'user_id' not in session or session['user_id'] != biz_id:
        return redirect(url_for('dashboard.login'))

    business = business_repo.get_by_id(biz_id)
    plan = dict(business).get('plan_abonnement', 'FREE') if business else 'BASIC'

    if plan != 'SCALE':
        return redirect(url_for('dashboard.admin_dashboard', biz_id=biz_id))

    biz_type = dict(business).get('business_type', 'restaurant') if business else 'restaurant'
    sector = sector_repo.get_by_id(biz_type)
    vocab = sector['vocab'] if sector else {}
    raw_reservations = order_repo.get_by_business(biz_id)
    reservations = []
    for r in raw_reservations:
        r_dict = dict(r)
        client = client_repo.get_or_create(biz_id, r['wa_id'])
        nom = client['nom'] if client else r['wa_id']
        if nom == "Client" and len(r['wa_id']) >= 4:
            nom = f"Client ...{r['wa_id'][-4:]}"
        r_dict['client_name'] = nom
        reservations.append(r_dict)


    return render_template('dashboard/payments.html',
                           biz_id=biz_id,
                           business=business,
                           vocab=vocab,
                           plan=plan,
                           reservations=reservations,
                           active_page='payments')


@dashboard_bp.route('/admin/<biz_id>/test-report', methods=['GET'])
def test_report(biz_id):
    if 'user_id' not in session or session['user_id'] != biz_id:
        return redirect(url_for('dashboard.login'))
    
    business = business_repo.get_by_id(biz_id)
    if not business or not business['owner_phone']:
        flash("Numero du gerant introuvable.", "error")
        return redirect(url_for('dashboard.business_settings', biz_id=biz_id))
    
    from app.services.report_service import generate_daily_report_for_business
    clean_phone = ''.join(c for c in business['owner_phone'] if c.isdigit())
    if clean_phone.startswith('00'):
        clean_phone = clean_phone[2:]
    if len(clean_phone) == 8:
        clean_phone = f"228{clean_phone}"
    
    try:
        generate_daily_report_for_business(biz_id, clean_phone, business['nom'], business['token_wa'], business['whatsapp_phone_id'])
        flash("Le rapport quotidien a ete genere et envoye sur WhatsApp !", "success")
    except Exception as e:
        flash(f"Erreur lors de l'envoi : {e}", "error")
        
    return redirect(url_for('dashboard.business_settings', biz_id=biz_id))

@dashboard_bp.route('/admin/<biz_id>/vitrine', methods=['GET', 'POST'])
def vitrine_settings(biz_id):
    """ParamÃ¨tres de la vitrine web."""
    if 'user_id' not in session or session['user_id'] != biz_id:
        return redirect(url_for('dashboard.login'))

    business = business_repo.get_by_id(biz_id)
    if not business:
        return redirect(url_for('dashboard.login'))

    biz_type = dict(business).get('business_type', 'restaurant')
    sector = sector_repo.get_by_id(biz_type)
    vocab = sector['vocab'] if sector else {}
    plan = dict(business).get('plan_abonnement', 'FREE')

    if request.method == 'POST':
        import os
        from werkzeug.utils import secure_filename
        from flask import current_app

        color = request.form.get('vitrine_color', '#5b6af0')
        logo_url = None
        cover_url = None
        description = None

        if 'logo' in request.files:
            file = request.files['logo']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                biz_upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'businesses', biz_id)
                os.makedirs(biz_upload_dir, exist_ok=True)
                filepath = os.path.join(biz_upload_dir, filename)
                file.save(filepath)
                logo_url = f'/static/uploads/businesses/{biz_id}/{filename}'
                
        if plan == 'SCALE':
            description = request.form.get('vitrine_description')
            if 'cover' in request.files:
                file = request.files['cover']
                if file and file.filename != '':
                    filename = secure_filename("cover_" + file.filename)
                    biz_upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'businesses', biz_id)
                    os.makedirs(biz_upload_dir, exist_ok=True)
                    filepath = os.path.join(biz_upload_dir, filename)
                    file.save(filepath)
                    cover_url = f'/static/uploads/businesses/{biz_id}/{filename}'

        business_repo.set_vitrine_settings(biz_id, color, logo_url, cover_url, description)
        flash('ParamÃ¨tres de la vitrine mis Ã  jour.', 'success')
        return redirect(url_for('dashboard.vitrine_settings', biz_id=biz_id))

    return render_template('dashboard/vitrine_settings.html',
                           biz_id=biz_id,
                           business=business,
                           vocab=vocab,
                           plan=plan,
                           active_page='vitrine')

@dashboard_bp.route('/sw.js')
def service_worker():
    """Sert le service worker à la racine pour avoir le scope global."""
    from flask import send_from_directory, current_app
    import os
    return send_from_directory(os.path.join(current_app.root_path, 'static', 'js'), 'sw.js', mimetype='application/javascript')

@dashboard_bp.route('/manifest/<biz_id>.json')
def dynamic_manifest(biz_id):
    """Génère le manifeste PWA dynamiquement pour un business."""
    from flask import jsonify
    business = business_repo.get_by_id(biz_id)
    if not business:
        return jsonify({"error": "Business not found"}), 404
        
    business_name = dict(business).get('nom', 'Catalogue')
    
    # Check for custom logo and color in vitrine settings
    vitrine_settings = None
    try:
        vitrine_settings = business_repo.get_vitrine_settings(biz_id)
    except Exception:
        pass
        
    business_logo = "/static/images/default-logo.png"
    theme_color = "#25D366"
    
    if vitrine_settings:
        if vitrine_settings.get('logo_url'):
            business_logo = vitrine_settings['logo_url']
        if vitrine_settings.get('color'):
            theme_color = vitrine_settings['color']
    
    # Fallback to business default logo if needed
    if business_logo == "/static/images/default-logo.png" and dict(business).get('logo_url'):
        business_logo = dict(business).get('logo_url')

    manifest = {
        "name": business_name,
        "short_name": business_name,
        "start_url": f"/v/{biz_id}",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": theme_color,
        "icons": [
            {
                "src": business_logo,
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": business_logo,
                "sizes": "512x512",
                "type": "image/png"
            }
        ]
    }
    
    return jsonify(manifest)

@dashboard_bp.route('/v/<biz_id>')
def public_vitrine(biz_id):
    """Route publique pour la vitrine du client."""
    business = business_repo.get_by_id(biz_id)
    if not business:
        return 'Vitrine introuvable', 404
        
    plan = dict(business).get('plan_abonnement', 'FREE')

    products = catalog_repo.get_by_business(biz_id, only_available=False)
    # Filtrer uniquement les produits visibles
    visible_products = [p for p in products if dict(p).get('is_visible', 1) == 1]

    grouped_products = {}
    for p in visible_products:
        cat = p['categorie'] or 'GÃ©nÃ©ral'
        if cat not in grouped_products:
            grouped_products[cat] = []
        grouped_products[cat].append(p)

    template_name = 'vitrine_premium.html' if plan == 'SCALE' else 'vitrine.html'

    is_open = False
    today_schedule_str = None
    horaires_str = dict(business).get('horaires_json')
    if horaires_str:
        import json
        from datetime import datetime
        try:
            horaires = json.loads(horaires_str)
            days = ['lun', 'mar', 'mer', 'jeu', 'ven', 'sam', 'dim']
            now = datetime.now()
            today_str = days[now.weekday()]
            today_horaire = horaires.get(today_str)
            if today_horaire:
                open_str = None
                close_str = None
                if isinstance(today_horaire, list) and len(today_horaire) >= 2:
                    open_str = today_horaire[0]
                    close_str = today_horaire[1]
                elif isinstance(today_horaire, dict):
                    open_str = today_horaire.get('open')
                    close_str = today_horaire.get('close')
                
                if open_str and close_str:
                    today_schedule_str = f"{open_str} - {close_str}"
                    open_time = datetime.strptime(open_str, '%H:%M').time()
                    close_time = datetime.strptime(close_str, '%H:%M').time()
                    if open_time <= now.time() <= close_time:
                        is_open = True
        except Exception:
            pass

    return render_template(template_name,
                           business=business,
                           plan=plan,
                           is_open=is_open,
                           today_schedule_str=today_schedule_str,
                           grouped_products=grouped_products)

@dashboard_bp.route('/admin/<biz_id>/catalog/edit/<int:product_id>', methods=['POST'])
def edit_catalog_product(biz_id, product_id):
    """API: Editer un produit du catalogue."""
    if 'user_id' not in session or session['user_id'] != biz_id:
        return redirect(url_for('dashboard.login'))

    import os
    from werkzeug.utils import secure_filename
    from flask import current_app

    nom = request.form.get('nom')
    categorie = request.form.get('categorie', 'GÃ©nÃ©ral')
    prix = request.form.get('prix', 0)
    description = request.form.get('description', '')
    is_visible = 1 if request.form.get('is_visible') == 'on' else 0
    duree_minutes = request.form.get('duree_minutes', 30)

    try:
        prix = int(prix)
    except ValueError:
        prix = 0

    try:
        duree_minutes = int(duree_minutes)
    except ValueError:
        duree_minutes = 30

    image_url = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            biz_upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'businesses', biz_id, 'products')
            os.makedirs(biz_upload_dir, exist_ok=True)
            filepath = os.path.join(biz_upload_dir, filename)
            file.save(filepath)
            # URL relative pour l'affichage
            image_url = f"/static/uploads/businesses/{biz_id}/products/{filename}"

    if nom:
        catalog_repo.update_product(product_id, biz_id, nom, prix, description, categorie, image_url, is_visible, duree_minutes)

    return redirect(url_for('dashboard.business_catalog', biz_id=biz_id))


@dashboard_bp.route('/admin/<biz_id>/tags', methods=['GET', 'POST'])
def tags(biz_id):
    if 'user_id' not in session or session['user_id'] != biz_id:
        flash("AccÃ¨s refusÃ©", "error")
        return redirect(url_for('dashboard.login'))

    biz = business_repo.get_by_id(biz_id)

    if request.method == 'POST':
        name = request.form.get('name')
        tag_type = request.form.get('type')
        color = request.form.get('color', '#3B82F6')
        description = request.form.get('description', '')

        if name and tag_type:
            tag_repo.create_tag(biz_id, name, tag_type, color, description)
            flash("Tag crÃ©Ã© avec succÃ¨s.", "success")
        else:
            flash("Nom et type obligatoires.", "error")
        return redirect(url_for('dashboard.tags', biz_id=biz_id))

    tags_list = tag_repo.get_business_tags(biz_id)
    return render_template('dashboard/tags.html', business=biz, tags=tags_list, page='tags', biz_id=biz_id, active_page='tags')

@dashboard_bp.route('/admin/<biz_id>/tags/delete/<int:tag_id>', methods=['POST'])
def delete_tag(biz_id, tag_id):
    if 'user_id' not in session or session['user_id'] != biz_id:
        return jsonify({"success": False}), 403

    tag_repo.delete_tag(tag_id, biz_id)
    flash("Tag supprimÃ©.", "success")
    return redirect(url_for('dashboard.tags', biz_id=biz_id))




@dashboard_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        if not email:
            return render_template('auth/forgot_password.html', error="Veuillez entrer votre adresse email.")
            
        business = business_repo.get_by_email(email)
        if business:
            try:
                from app.services.notification_master_service import create_master_notification
                create_master_notification('alerte', 'Mot de passe oublié', f"Mot de passe oublié: {business['nom']} ({email})", business['id'])
            except Exception:
                pass
                
        # On affiche toujours un message de succès pour ne pas révéler si l'email existe ou non (sécurité)
        return render_template('auth/forgot_password.html', success="Si cet email existe dans notre système, notre équipe vous contactera pour réinitialiser votre mot de passe.")
        
    return render_template('auth/forgot_password.html')


@dashboard_bp.route('/<biz_id>/orders/<int:order_id>/action', methods=['POST'])
def order_action(biz_id, order_id):
    if 'user_id' not in session or session['user_id'] != biz_id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    action = request.form.get('action')
    if action not in ['accept', 'reject']:
        return jsonify({'error': 'Invalid action'}), 400
        
    import sqlite3
    from app.models.schema import get_db_path
    
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM reservations WHERE id = ? AND business_id = ?", (order_id, biz_id))
    order = cursor.fetchone()
    
    if not order:
        conn.close()
        return jsonify({'error': 'Order not found'}), 404
        
    new_status = 'En préparation' if action == 'accept' else 'Refusée'
    cursor.execute("UPDATE reservations SET statut = ? WHERE id = ?", (new_status, order_id))
    conn.commit()
    conn.close()
    
    if action == 'reject':
        # Send WhatsApp message
        try:
            from app.services import whatsapp_service
            from app.repositories.business_repo import get_by_id
            biz = get_by_id(biz_id)
            phone_id = dict(biz).get('whatsapp_phone_id')
            token = dict(biz).get('whatsapp_token')
            if phone_id and token:
                msg = f"Bonjour, nous sommes désolés mais votre commande (Réf: #{order_id}) n'a pas pu être acceptée."
                whatsapp_service.send_text_message(phone_id, token, order['wa_id'], msg)
        except Exception as e:
            print(f"Failed to send rejection WhatsApp msg: {e}")
            
    flash(f"Commande {new_status.lower()} avec succès.", "success")
    return redirect(url_for('dashboard.admin_dashboard', biz_id=biz_id))

@dashboard_bp.route('/<biz_id>/analytics')
def business_analytics(biz_id):
    if 'user_id' not in session or session['user_id'] != biz_id:
        return redirect(url_for('auth.login'))
        
    from app.repositories import business_repo
    from app.repositories import sector_repo
    
    biz = business_repo.get_by_id(biz_id)
    if not biz:
        return redirect(url_for('auth.login'))
        
    biz_type = dict(biz).get('type', 'retail')
    sector = sector_repo.get_by_id(biz_type)
    vocab = sector['vocab'] if sector else {}
    
    plan = dict(biz).get('plan_abonnement', 'FREE')
    
    return render_template('dashboard/analytics.html', biz_id=biz_id, business=biz, vocab=vocab, plan=plan, active_page='analytics')


# ==========================================
# ==========================================
# VIRA CHAT (MANAGER)
# ==========================================

def get_session_or_403(session_id: str, business_id: str):
    from app.repositories import vira_chat_repo
    from werkzeug.exceptions import Forbidden, NotFound
    session_data = vira_chat_repo.get_session(session_id)
    if not session_data or session_data.get('business_id') != business_id:
        raise NotFound()
    return session_data

@dashboard_bp.route('/admin/<biz_id>/vira-chat', defaults={'session_id': None})
@dashboard_bp.route('/admin/<biz_id>/vira-chat/<session_id>')
def vira_chat(biz_id, session_id):
    if 'user_id' not in session or session['user_id'] != biz_id:
        return redirect(url_for('dashboard.login'))
        
    business = business_repo.get_by_id(biz_id)
    from app.repositories import vira_chat_repo
    
    current_session = None
    if session_id:
        from werkzeug.exceptions import NotFound
        try:
            current_session = get_session_or_403(session_id, biz_id)
        except NotFound:
            return redirect(url_for('dashboard.vira_chat', biz_id=biz_id))
    
    sessions = vira_chat_repo.get_sessions(biz_id, session['user_id'])
    
    history = []
    if session_id:
        history = vira_chat_repo.get_vira_history(business_id=biz_id, user_id=session['user_id'], session_id=session_id, limit=50)
    
    from app.repositories import sector_repo
    biz_type = dict(business).get('business_type', 'restaurant') if business else 'restaurant'
    sector = sector_repo.get_by_id(biz_type)
    vocab = sector['vocab'] if sector else {}
    
    import sqlite3
    from app.models.schema import get_db_path
    from datetime import datetime
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    date_cond = f"date(created_at) = '{today}'"
    history_date_cond = f"date(timestamp) = '{today}'"
    
    stats = {}
    
    cursor.execute(f"SELECT COUNT(*) FROM history WHERE business_id = ? AND role = 'user' AND {history_date_cond}", (biz_id,))
    stats['messages_recus'] = cursor.fetchone()[0] or 0
    
    cursor.execute(f"SELECT COUNT(*), SUM(montant) FROM reservations WHERE business_id = ? AND statut NOT LIKE 'Annul%' AND statut != 'Refusée' AND {date_cond}", (biz_id,))
    row = cursor.fetchone()
    stats['commandes'] = row[0] or 0
    stats['ca'] = row[1] or 0
    
    # Activités récentes
    cursor.execute('''
        SELECT h.content, h.timestamp, c.nom, c.platform 
        FROM history h 
        LEFT JOIN clients c ON h.wa_id = c.wa_id AND h.business_id = c.business_id
        WHERE h.business_id = ? AND h.role = 'user' 
        ORDER BY h.timestamp DESC 
        LIMIT 4
    ''', (biz_id,))
    rows = cursor.fetchall()
    
    recent_activities = []
    for r in rows:
        content = r[0]
        ts_str = r[1]
        name = r[2] or "Client Inconnu"
        platform = r[3] or "whatsapp"
        
        try:
            ts = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
            diff = datetime.now() - ts
            if diff.total_seconds() < 60:
                time_ago = "À l'instant"
            elif diff.total_seconds() < 3600:
                time_ago = f"Il y a {int(diff.total_seconds() / 60)} min"
            elif diff.total_seconds() < 86400:
                time_ago = f"Il y a {int(diff.total_seconds() / 3600)} h"
            else:
                time_ago = f"Il y a {int(diff.total_seconds() / 86400)} j"
        except:
            time_ago = ts_str
            
        recent_activities.append({
            'name': name,
            'content': content[:40] + '...' if len(content) > 40 else content,
            'time_ago': time_ago,
            'platform': platform
        })
        
    conn.close()
    
    return render_template('dashboard/vira_chat.html', biz_id=biz_id, business=business, active_page='vira-chat', chat_history=history, stats=stats, vocab=vocab, sessions=sessions, current_session=current_session, recent_activities=recent_activities)

@dashboard_bp.route('/api/vira-chat/message/<biz_id>', methods=['POST'])
def api_vira_chat_message(biz_id):
    if 'user_id' not in session or session['user_id'] != biz_id:
        return jsonify({'success': False, 'error': 'Non autorisé'}), 403
        
    data = request.json
    message = data.get('message', '').strip()
    session_id = data.get('session_id')
    
    if not message:
        return jsonify({'success': False, 'error': 'Message vide'}), 400
        
    if session_id:
        from werkzeug.exceptions import NotFound
        try:
            get_session_or_403(session_id, biz_id)
        except NotFound:
            return jsonify({'success': False, 'error': 'Session introuvable'}), 404
        
    try:
        from app.services.vira_chat_service import get_vira_response
        reply, new_session_id = get_vira_response(business_id=biz_id, user_id=session['user_id'], session_id=session_id, message=message)
        return jsonify({'success': True, 'reply': reply, 'session_id': new_session_id})
    except Exception as e:
        return jsonify({'success': False, 'error': f"Erreur interne: {str(e)}"}), 500

@dashboard_bp.route('/api/vira-chat/sessions/<session_id>', methods=['DELETE'])
def api_delete_vira_session(session_id):
    biz_id = session.get('user_id')
    if not biz_id:
        return jsonify({'success': False, 'error': 'Non autorisé'}), 403
    
    from werkzeug.exceptions import NotFound
    try:
        get_session_or_403(session_id, biz_id)
    except NotFound:
        return jsonify({'success': False, 'error': 'Session introuvable'}), 404
        
    from app.repositories import vira_chat_repo
    success = vira_chat_repo.soft_delete_session(session_id, biz_id)
    return jsonify({'success': success})
