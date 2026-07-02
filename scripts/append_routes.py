
@dashboard_bp.route('/admin/<biz_id>/vitrine', methods=['GET', 'POST'])
def vitrine_settings(biz_id):
    """Paramètres de la vitrine web."""
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
        flash('Paramètres de la vitrine mis à jour.', 'success')
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

    products = catalog_repo.get_by_business(biz_id, only_available=False)
    # Filtrer uniquement les produits visibles
    visible_products = [p for p in products if dict(p).get('is_visible', 1) == 1]

    grouped_products = {}
    for p in visible_products:
        cat = p['categorie'] or 'Général'
        if cat not in grouped_products:
            grouped_products[cat] = []
        grouped_products[cat].append(p)

    return render_template('vitrine.html',
                           business=business,
                           grouped_products=grouped_products)
