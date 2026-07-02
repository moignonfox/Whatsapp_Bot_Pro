
@dashboard_bp.route('/admin/<biz_id>/catalog/edit/<int:product_id>', methods=['POST'])
def edit_catalog_product(biz_id, product_id):
    """API: Editer un produit du catalogue."""
    if 'user_id' not in session or session['user_id'] != biz_id:
        return redirect(url_for('dashboard.login'))

    import os
    from werkzeug.utils import secure_filename
    from flask import current_app

    nom = request.form.get('nom')
    categorie = request.form.get('categorie', 'Général')
    prix = request.form.get('prix', 0)
    description = request.form.get('description', '')
    is_visible = 1 if request.form.get('is_visible') == 'on' else 0

    try:
        prix = int(prix)
    except ValueError:
        prix = 0

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
        catalog_repo.update_product(product_id, biz_id, nom, prix, description, categorie, image_url, is_visible)

    return redirect(url_for('dashboard.business_catalog', biz_id=biz_id))
