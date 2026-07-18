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
    ctx = {'global_unread_count': 0, 'plan': 'BASIC'}
    if user_id:
        business = business_repo.get_by_id(user_id)
        if business:
            ctx['plan'] = dict(business).get('plan_abonnement', 'BASIC')
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
                dict(business).get('plan_abonnement', 'BASIC'),
                dict(business).get('is_active', 1),
                owner_phone,
                dict(business).get('drip_j3_enabled', 0),
                dict(business).get('drip_j3_msg'),
                dict(business).get('debounce_delay', 3)
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

    plan = dict(business).get('plan_abonnement', 'BASIC') if business else 'BASIC'
    employees = employee_repo.get_by_business(biz_id) if plan == 'PREMIUM' else []

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

        # Si un nouveau mot de passe est saisi, on le hache, sinon on garde l'ancien (dÃ©jÃ  hachÃ©)
        final_password = business['password']
        if password:
            final_password = generate_password_hash(password)

        current_plan = dict(business).get('plan_abonnement', 'BASIC') if business else 'BASIC'
        
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
            buffer_minutes
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
    plan = dict(business).get('plan_abonnement', 'BASIC') if business else 'BASIC'

    return render_template('dashboard/settings.html', business=business, vocab=vocab, biz_id=biz_id, plan=plan, active_page='settings')


@dashboard_bp.route('/admin/<biz_id>/marketing-settings', methods=['POST'])
def marketing_settings(biz_id):
    """Sauvegarde les paramÃ¨tres de marketing automatisÃ© (Relance J+3)."""
    if 'user_id' not in session or session['user_id'] != biz_id:
        return redirect(url_for('dashboard.login'))

    business = business_repo.get_by_id(biz_id)
    plan = dict(business).get('plan_abonnement', 'BASIC') if business else 'BASIC'

    if plan == 'PREMIUM':
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
            drip_j3_msg
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
    plan = dict(business).get('plan_abonnement', 'BASIC')

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
    plan = dict(business).get('plan_abonnement', 'BASIC')

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

    plan = dict(business).get('plan_abonnement', 'BASIC') if business else 'BASIC'

    return render_template('dashboard/chat.html',
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

    return jsonify({
        'messages': messages,
        'is_human_mode': is_human,
        'client_name': c_main,
        'client_real_name': c_nom,
        'client_display_name': c_disp,
        'wa_id': wa_id
    })



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
    plan = dict(business).get('plan_abonnement', 'BASIC') if business else 'BASIC'

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
    plan = dict(business).get('plan_abonnement', 'BASIC') if business else 'BASIC'

    if plan not in ('PRO', 'PREMIUM'):
        return redirect(url_for('dashboard.admin_dashboard', biz_id=biz_id))

    biz_type = dict(business).get('business_type', 'restaurant') if business else 'restaurant'
    sector = sector_repo.get_by_id(biz_type)
    vocab = sector['vocab'] if sector else {}
    clients = conversation_repo.get_conversations_for_business(biz_id)

    return render_template('dashboard/marketing.html',
                           biz_id=biz_id,
                           business=business,
                           vocab=vocab,
                           plan=plan,
                           clients=clients,
                           active_page='marketing')


@dashboard_bp.route('/admin/<biz_id>/generate-campaign-copy', methods=['POST'])
def generate_campaign_copy(biz_id):
    if 'user_id' not in session or session['user_id'] != biz_id:
        return jsonify({"error": "Non autorisÃ©"}), 403

    business = business_repo.get_by_id(biz_id)
    if not business:
        return jsonify({"error": "Business introuvable"}), 404

    message = request.json.get('message', '').strip()
    if not message:
        return jsonify({"error": "Message vide"}), 400

    from app.services.ai_service import improve_marketing_message
    
    try:
        improved = improve_marketing_message(message)
        return jsonify({"copy": improved})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================================
# GESTION DES EMPLOYÃ‰S (Ã‰QUIPE)
# ==========================================
@dashboard_bp.route('/admin/<biz_id>/employees', methods=['GET', 'POST'])
def business_employees(biz_id):
    """GÃ¨re l'Ã©quipe (employÃ©s et leurs horaires)."""
    if 'user_id' not in session or session['user_id'] != biz_id:
        return redirect(url_for('dashboard.login'))

    business = business_repo.get_by_id(biz_id)
    plan = dict(business).get('plan_abonnement', 'BASIC')

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

    return render_template('dashboard/employees.html',
                           biz_id=biz_id,
                           business=business,
                           employees=employees,
                           vocab=vocab,
                           plan=plan,
                           active_page='employees')

# ==========================================
# AGENDA (FULLCALENDAR)
# ==========================================
@dashboard_bp.route('/admin/<biz_id>/agenda')
def business_agenda(biz_id):
    """Affiche l'agenda visuel des rÃ©servations."""
    if 'user_id' not in session or session['user_id'] != biz_id:
        return redirect(url_for('dashboard.login'))

    business = business_repo.get_by_id(biz_id)
    plan = dict(business).get('plan_abonnement', 'BASIC')
    employees = employee_repo.get_by_business(biz_id)
    
    return render_template('dashboard/agenda.html',
                           biz_id=biz_id,
                           business=business,
                           plan=plan,
                           employees=employees,
                           active_page='agenda')

@dashboard_bp.route('/api/agenda/events/<biz_id>')
def api_agenda_events(biz_id):
    """Retourne les rÃ©servations (orders) au format FullCalendar."""
    if 'user_id' not in session or session['user_id'] != biz_id:
        return jsonify([])

    orders = order_repo.get_by_business(biz_id)
    events = []
    for order in orders:
        if order['date_heure_debut']:
            title_name = order['client_name'] if order['client_name'] else f"+{order['wa_id']}"
            # Replace space with T to make it ISO 8601 compliant (fixes iOS Safari bug where events don't show)
            start_iso = order['date_heure_debut'].replace(' ', 'T')
            events.append({
                "id": order['id'],
                "title": f"{title_name} ({order['details']})",
                "start": start_iso,
                # "end": sera calculÃ© si nÃ©cessaire (date_heure_debut + duree)
                "extendedProps": {
                    "statut": order['statut'],
                    "employee_id": order['employee_id']
                }
            })
    return jsonify(events)

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
    if plan != 'PREMIUM':
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
            agent_repo.deactivate(agent_id, biz_id)
            flash("Agent IA dÃ©sactivÃ©.", "success")
            
        elif action == 'set_routing':
            routing_mode = request.form.get('routing_mode')
            allowed_modes = {'visible', 'invisible'}
            if routing_mode in allowed_modes:
                business_repo.update_routing_mode(biz_id, routing_mode)
                flash("Mode de routage mis Ã  jour.", "success")
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

    return render_template(
        'dashboard/agents.html',
        biz_id=biz_id,
        business=business,
        plan=plan,
        agents=agents_list,
        default_templates=default_templates,
        active_page='agents'
    )

@dashboard_bp.route('/admin/<biz_id>/send-campaign', methods=['POST'])
def send_campaign(biz_id):
    if 'user_id' not in session or session['user_id'] != biz_id:
        return redirect(url_for('dashboard.login'))

    business = business_repo.get_by_id(biz_id)
    target = request.form.get('target', 'all')
    message_template = request.form.get('message', '')

    if not message_template.strip():
        return redirect(url_for('dashboard.business_marketing', biz_id=biz_id))

    plan = dict(business).get('plan_abonnement', 'BASIC')
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
        marketing_repo.enqueue_campaign(biz_id, clients_to_send, message_template)
        flash(f"La campagne a ete mise en file d'attente pour {len(clients_to_send)} clients !", "success")

    return redirect(url_for('dashboard.business_marketing', biz_id=biz_id))



@dashboard_bp.route('/admin/<biz_id>/payments')
def business_payments(biz_id):
    """Page Paiements (accÃ¨s rÃ©servÃ© au plan PREMIUM)."""
    if 'user_id' not in session or session['user_id'] != biz_id:
        return redirect(url_for('dashboard.login'))

    business = business_repo.get_by_id(biz_id)
    plan = dict(business).get('plan_abonnement', 'BASIC') if business else 'BASIC'

    if plan != 'PREMIUM':
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
    plan = dict(business).get('plan_abonnement', 'BASIC')

    if request.method == 'POST':
        import os
        from werkzeug.utils import secure_filename
        from flask import current_app

        color = request.form.get('vitrine_color', '#5b6af0')
        logo_url = None

        if 'logo' in request.files:
            file = request.files['logo']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                biz_upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'businesses', biz_id)
                os.makedirs(biz_upload_dir, exist_ok=True)
                filepath = os.path.join(biz_upload_dir, filename)
                file.save(filepath)
                logo_url = f'/static/uploads/businesses/{biz_id}/{filename}'

        business_repo.set_vitrine_settings(biz_id, color, logo_url)
        flash('ParamÃ¨tres de la vitrine mis Ã  jour.', 'success')
        return redirect(url_for('dashboard.vitrine_settings', biz_id=biz_id))

    return render_template('dashboard/vitrine_settings.html',
                           biz_id=biz_id,
                           business=business,
                           vocab=vocab,
                           plan=plan,
                           active_page='vitrine')

@dashboard_bp.route('/v/<biz_id>')
def public_vitrine(biz_id):
    """Route publique pour la vitrine du client."""
    business = business_repo.get_by_id(biz_id)
    if not business:
        return 'Vitrine introuvable', 404
        
    plan = dict(business).get('plan_abonnement', 'BASIC')

    products = catalog_repo.get_by_business(biz_id, only_available=False)
    # Filtrer uniquement les produits visibles
    visible_products = [p for p in products if dict(p).get('is_visible', 1) == 1]

    grouped_products = {}
    for p in visible_products:
        cat = p['categorie'] or 'GÃ©nÃ©ral'
        if cat not in grouped_products:
            grouped_products[cat] = []
        grouped_products[cat].append(p)

    return render_template('vitrine.html',
                           business=business,
                           plan=plan,
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
