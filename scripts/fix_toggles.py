import re

# 1. Vitrine HTML : Ajouter la mention Épuisé
vitrine_path = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\templates\vitrine.html'

with open(vitrine_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remplacer la zone d'image pour inclure un badge Épuisé si p.disponible == 0
old_card_img = """<div class="card-img-wrap">
          {% if p.image_url %}
            <img src="{{ p.image_url }}" alt="{{ p.nom }}" class="card-img" style="width:100%; height:100%; object-fit:cover;">
          {% else %}
            <div class="card-img-placeholder">📦</div>
          {% endif %}
        </div>"""

new_card_img = """<div class="card-img-wrap" style="position:relative;">
          {% if p.image_url %}
            <img src="{{ p.image_url }}" alt="{{ p.nom }}" class="card-img" style="width:100%; height:100%; object-fit:cover; {% if not p.disponible %}filter: grayscale(100%); opacity: 0.6;{% endif %}">
          {% else %}
            <div class="card-img-placeholder" style="{% if not p.disponible %}opacity: 0.4;{% endif %}">📦</div>
          {% endif %}
          
          {% if not p.disponible %}
            <div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); background:rgba(0,0,0,0.75); color:#fff; font-weight:700; padding:6px 12px; border-radius:8px; font-size:14px; letter-spacing:1px; z-index:2;">ÉPUISÉ</div>
          {% endif %}
        </div>"""

if "ÉPUISÉ" not in content:
    content = content.replace(old_card_img, new_card_img)

# Remplacer le footer pour désactiver le bouton + si épuisé
old_card_footer = """<div class="card-footer">
            <span class="card-price">{{ "{:,.0f}".format(p.prix).replace(',', ' ') }} FCFA</span>
            {% if plan != 'BASIC' %}
              <button class="add-btn" title="Ajouter au panier">+</button>
            {% endif %}
          </div>"""

new_card_footer = """<div class="card-footer">
            <span class="card-price">{{ "{:,.0f}".format(p.prix).replace(',', ' ') }} FCFA</span>
            {% if plan != 'BASIC' %}
              {% if p.disponible %}
                <button class="add-btn" title="Ajouter au panier">+</button>
              {% else %}
                <button class="add-btn" disabled style="background:var(--border); color:var(--muted); cursor:not-allowed;" title="Produit épuisé">+</button>
              {% endif %}
            {% endif %}
          </div>"""

if "cursor:not-allowed" not in content:
    content = content.replace(old_card_footer, new_card_footer)

with open(vitrine_path, 'w', encoding='utf-8') as f:
    f.write(content)


# 2. Routes Dashboard : Autoriser GET pour les toggles (car appelés par un lien <a>)
routes_path = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\dashboard\routes.py'

with open(routes_path, 'r', encoding='utf-8') as f:
    routes_content = f.read()

# Le toggle product
old_toggle_product = """@dashboard_bp.route('/admin/<biz_id>/catalog/toggle/<int:product_id>', methods=['POST'])
def toggle_catalog_product(biz_id, product_id):"""

new_toggle_product = """@dashboard_bp.route('/admin/<biz_id>/catalog/toggle/<int:product_id>', methods=['GET', 'POST'])
def toggle_catalog_product(biz_id, product_id):"""

# Le toggle visibility
old_toggle_visibility = """@dashboard_bp.route('/admin/<biz_id>/catalog/toggle_visibility/<int:product_id>', methods=['POST'])
def toggle_catalog_visibility(biz_id, product_id):"""

new_toggle_visibility = """@dashboard_bp.route('/admin/<biz_id>/catalog/toggle_visibility/<int:product_id>', methods=['GET', 'POST'])
def toggle_catalog_visibility(biz_id, product_id):"""

routes_content = routes_content.replace(old_toggle_product, new_toggle_product)
routes_content = routes_content.replace(old_toggle_visibility, new_toggle_visibility)

# Mettre aussi à jour la fonction toggle pour rediriger le GET vers l'url du catalogue
# S'il y a un redirect déjà, c'est bon. Je vais vérifier si la route contient un redirect à la fin
import re
if "redirect(url_for('dashboard.catalog'" not in routes_content and "redirect(request.referrer" not in routes_content:
    # Je dois ajouter un redirect(request.referrer) à la fin de toggle_catalog_product et visibility
    routes_content = re.sub(
        r'catalog_repo\.toggle_availability\(product_id, biz_id\)',
        r"catalog_repo.toggle_availability(product_id, biz_id)\n    from flask import request\n    return redirect(request.referrer or url_for('dashboard.catalog', biz_id=biz_id))",
        routes_content
    )
    routes_content = re.sub(
        r'catalog_repo\.toggle_visibility\(product_id, biz_id\)',
        r"catalog_repo.toggle_visibility(product_id, biz_id)\n    from flask import request\n    return redirect(request.referrer or url_for('dashboard.catalog', biz_id=biz_id))",
        routes_content
    )


with open(routes_path, 'w', encoding='utf-8') as f:
    f.write(routes_content)

print("Vitrine updated for 'Épuisé' state and toggle routes fixed.")
