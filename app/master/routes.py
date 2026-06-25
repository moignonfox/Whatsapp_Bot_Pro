"""Routes Master Admin — Gestion des businesses par le super-administrateur."""
from flask import Blueprint, request, render_template, redirect, url_for, session, current_app, jsonify, make_response
from werkzeug.security import generate_password_hash
from app.repositories import business_repo, sector_repo, employee_repo
from app import limiter
import json

master_bp = Blueprint('master', __name__, url_prefix='/master')


@master_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def master_login():
    """Connexion du super-administrateur."""
    if request.method == 'POST':
        password = request.form.get('password')
        from werkzeug.security import check_password_hash
        if check_password_hash(current_app.config['MASTER_PASSWORD_HASH'], password):
            session['is_master'] = True
            return redirect(url_for('master.master_dashboard'))
        return render_template('auth/login.html', error="Accès Maître refusé")
    return render_template('auth/login.html', is_master=True)


@master_bp.route('/')
@master_bp.route('/dashboard')
def master_dashboard():
    """Panneau de contrôle global : liste les businesses et les secteurs."""
    if not session.get('is_master'):
        return redirect(url_for('master.master_login'))
        
    businesses = business_repo.get_all_businesses()
    sectors = sector_repo.get_all_sectors()
    
    # Calculate metrics
    metrics = {
        'total_businesses': len(businesses),
        'total_sectors': len(sectors),
        'plan_basic': sum(1 for b in businesses if dict(b).get('plan_abonnement', 'BASIC') == 'BASIC'),
        'plan_pro': sum(1 for b in businesses if dict(b).get('plan_abonnement') == 'PRO'),
        'plan_premium': sum(1 for b in businesses if dict(b).get('plan_abonnement') == 'PREMIUM'),
    }
    from app.repositories import settings_repo, conversation_repo
    global_settings = settings_repo.get_all_settings()
    
    # Calculer l'usage pour chaque entreprise
    businesses_list = []
    for b in businesses:
        biz_dict = dict(b)
        plan = biz_dict.get('plan_abonnement', 'BASIC')
        if plan == 'PREMIUM':
            quota_str = global_settings.get('quota_messages_premium', '10000')
        elif plan == 'PRO':
            quota_str = global_settings.get('quota_messages_pro', '2000')
        else:
            quota_str = global_settings.get('quota_messages_basic', '500')
            
        try:
            quota = int(quota_str)
        except:
            quota = 500
            
        usage = conversation_repo.get_monthly_ai_message_count(biz_dict['id'])
        biz_dict['ai_usage'] = usage
        biz_dict['ai_quota'] = quota
        biz_dict['ai_usage_pct'] = round((usage / quota * 100) if quota > 0 else 0)
        
        businesses_list.append(biz_dict)
    
    response = make_response(render_template('master/dashboard.html', businesses=businesses_list, sectors=sectors, metrics=metrics, global_settings=global_settings))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@master_bp.route('/save-limits', methods=['POST'])
def save_limits():
    """Enregistre les limites globales par abonnement."""
    if not session.get('is_master'):
        return "Action non autorisée", 403

    from app.repositories import settings_repo
    
    settings_repo.set_setting('max_input_basic', request.form.get('max_input_basic', '500'))
    settings_repo.set_setting('max_input_pro', request.form.get('max_input_pro', '1000'))
    settings_repo.set_setting('max_input_premium', request.form.get('max_input_premium', '3000'))
    
    settings_repo.set_setting('quota_messages_basic', request.form.get('quota_messages_basic', '500'))
    settings_repo.set_setting('quota_messages_pro', request.form.get('quota_messages_pro', '2000'))
    settings_repo.set_setting('quota_messages_premium', request.form.get('quota_messages_premium', '10000'))
    settings_repo.set_setting('overage_behavior', request.form.get('overage_behavior', 'FALLBACK'))

    return redirect(url_for('master.master_dashboard'))
@master_bp.route('/add-business')
def view_add_business():
    """Affichage du formulaire de création d'un nouveau business."""
    if not session.get('is_master'):
        return redirect(url_for('master.master_login'))
        
    sectors = sector_repo.get_all_sectors()
    return render_template('master/create_business.html', sectors=sectors)


@master_bp.route('/edit-business/<biz_id>')
def view_edit_business(biz_id):
    """Affichage du formulaire de modification d'un business existant."""
    if not session.get('is_master'):
        return redirect(url_for('master.master_login'))
        
    business = business_repo.get_by_id(biz_id)
    if not business:
        return "Business introuvable", 404
        
    sectors = sector_repo.get_all_sectors()
    employees = employee_repo.get_by_business(biz_id)
    return render_template('master/create_business.html', business=business, sectors=sectors, employees=employees)


@master_bp.route('/save-business', methods=['POST'])
def save_new_business():
    """Enregistrement d'un nouveau business ou mise à jour en base."""
    if not session.get('is_master'):
        return "Action non autorisée", 403

    biz_id = request.form.get('biz_id')
    nom = request.form.get('nom')
    phone_id = request.form.get('phone_id')
    token = request.form.get('token')
    password = request.form.get('password')
    prompt = request.form.get('prompt')
    msg_confirm = request.form.get('msg_confirm')
    msg_cancel = request.form.get('msg_cancel')
    msg_ready = request.form.get('msg_ready')
    business_type = request.form.get('business_type', 'restaurant')
    plan_abonnement = request.form.get('plan_abonnement', 'BASIC')

    if not biz_id or not phone_id:
        return "Erreur : L'ID et le Phone ID sont obligatoires.", 400

    existing = business_repo.get_by_id(biz_id)
    
    if password:
        hashed_password = generate_password_hash(password)
    else:
        hashed_password = existing['password'] if existing else ""

    # Préserver les champs existants qui ne sont pas dans le formulaire Master
    owner_phone = existing['owner_phone'] if existing else None
    drip_j3_enabled = existing['drip_j3_enabled'] if existing else 0
    drip_j3_msg = existing['drip_j3_msg'] if existing else None
    debounce_delay = existing['debounce_delay'] if existing else 3

    business_repo.add_or_update(biz_id, nom, phone_id, token, hashed_password, prompt,
                                msg_confirm, msg_cancel, msg_ready, business_type, plan_abonnement,
                                dict(existing).get('is_active', 1) if existing else 1,
                                owner_phone, drip_j3_enabled, drip_j3_msg, debounce_delay)

    return redirect(url_for('master.master_dashboard'))


@master_bp.route('/add-sector')
def view_add_sector():
    """Formulaire de création d'un nouveau secteur."""
    if not session.get('is_master'):
        return redirect(url_for('master.master_login'))
    return render_template('master/create_sector.html')


@master_bp.route('/edit-sector/<sector_id>')
def view_edit_sector(sector_id):
    """Formulaire de modification d'un secteur existant."""
    if not session.get('is_master'):
        return redirect(url_for('master.master_login'))
        
    sector = sector_repo.get_by_id(sector_id)
    if not sector:
        return "Secteur introuvable", 404
        
    return render_template('master/create_sector.html', sector=sector)


@master_bp.route('/save-sector', methods=['POST'])
def save_sector():
    """Enregistrement ou mise à jour d'un secteur et de son vocabulaire."""
    if not session.get('is_master'):
        return "Action non autorisée", 403

    sector_id = request.form.get('id')
    name = request.form.get('name')
    
    vocab = {
        'title_dashboard': request.form.get('title_dashboard'),
        'nav_orders': request.form.get('nav_orders'),
        'col_details': request.form.get('col_details'),
        'status_ready': request.form.get('status_ready'),
        'btn_ready': request.form.get('btn_ready')
    }

    if not sector_id or not name:
        return "Erreur : L'ID et le nom sont obligatoires.", 400

    sector_repo.add_or_update(sector_id, name, vocab)

    return redirect(url_for('master.master_dashboard'))


@master_bp.route('/toggle-business/<biz_id>', methods=['POST'])
def toggle_business(biz_id):
    """Active ou désactive un business."""
    if not session.get('is_master'):
        return jsonify({'success': False, 'error': 'Non autorisé'}), 403

    data = request.get_json()
    is_active = int(data.get('is_active', 1))
    
    try:
        business_repo.toggle_active(biz_id, is_active)
        return jsonify({'success': True, 'is_active': is_active})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ──────────────────────────────────────────────────────────────────────────────
# Gestion des Employés (Multi-Employés — offre PREMIUM)
# ──────────────────────────────────────────────────────────────────────────────

@master_bp.route('/business/<biz_id>/add-employee', methods=['POST'])
def add_employee(biz_id):
    """Ajoute un employé à un business (réservé au Master Admin)."""
    if not session.get('is_master'):
        return "Action non autorisée", 403

    nom = request.form.get('emp_nom', '').strip()
    poste = request.form.get('emp_poste', '').strip()

    if nom:
        employee_repo.add(biz_id, nom, poste)

    return redirect(url_for('master.view_edit_business', biz_id=biz_id))


@master_bp.route('/business/<biz_id>/delete-employee/<int:emp_id>', methods=['POST'])
def delete_employee(biz_id, emp_id):
    """Supprime un employé d'un business (réservé au Master Admin)."""
    if not session.get('is_master'):
        return "Action non autorisée", 403

    employee_repo.delete(emp_id)
    return redirect(url_for('master.view_edit_business', biz_id=biz_id))
