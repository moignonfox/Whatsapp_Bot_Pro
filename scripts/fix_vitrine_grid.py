import re

with open('app/templates/vitrine.html', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = r'<!-- GRID -->.*?<!-- INFO STRIP -->'
replacement = r'''<!-- GRID -->
<div class="grid-wrap">
  <div class="grid" id="product-grid">
  {% for cat, items in grouped_products.items() %}
    {% for p in items %}
      <div class="card" data-cat="{{ cat }}" data-name="{{ p.nom }}" data-price="{{ p.prix }}" data-emoji="📦">
        <div class="card-img-wrap">
          {% if p.image_url %}
            <img src="{{ p.image_url }}" alt="{{ p.nom }}" class="card-img" style="width:100%; height:100%; object-fit:cover;">
          {% else %}
            <div class="card-img-placeholder">📦</div>
          {% endif %}
        </div>
        <div class="card-info">
          <span class="card-cat">{{ p.categorie }}</span>
          <h3 class="card-name">{{ p.nom }}</h3>
          <p class="card-desc">{{ p.description if p.description else '' }}</p>
          <div class="card-bottom">
            <span class="card-price">{{ "{:,.0f}".format(p.prix).replace(',', ' ') }} FCFA</span>
            <button class="add-btn" title="Ajouter au panier">+</button>
          </div>
        </div>
      </div>
    {% endfor %}
  {% endfor %}
  </div>
</div>

<!-- INFO STRIP -->'''

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('app/templates/vitrine.html', 'w', encoding='utf-8') as f:
    f.write(content)
