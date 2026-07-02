import re

with open('app/templates/vitrine.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace hardcoded brand color with dynamic one
content = re.sub(
    r'--brand:\s*#5b6af0;',
    r"--brand:      {{ business.vitrine_color or '#5b6af0' }};",
    content
)

# Replace logo
content = re.sub(
    r'<span class="nav-logo">MyBoutique</span>',
    r'''{% if business.vitrine_logo_url %}
      <img src="{{ business.vitrine_logo_url }}" alt="{{ business.nom }}" style="height:30px; object-fit:contain;">
    {% else %}
      <span class="nav-logo">{{ business.nom }}</span>
    {% endif %}''',
    content
)

# Replace title
content = re.sub(
    r'<title>Boutique — Catalogue</title>',
    r'<title>{{ business.nom }} — Catalogue</title>',
    content
)

# Filter buttons logic: inject categories
filter_pattern = r'<div class="filters">.*?</div>'
filter_replacement = r'''<div class="filters">
      <button class="filter-btn active" data-cat="all">Tout</button>
      {% for cat in grouped_products.keys() %}
      <button class="filter-btn" data-cat="{{ cat }}">{{ cat }}</button>
      {% endfor %}
    </div>'''
content = re.sub(filter_pattern, filter_replacement, content, flags=re.DOTALL)

# Products Grid
pattern = r'<!-- PRODUCTS GRID -->(.*?)<!-- INFO STRIP -->'
replacement = r'''<!-- PRODUCTS GRID -->
<div class="grid">
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

<!-- INFO STRIP -->'''
content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Replace the whatsapp number
content = re.sub(
    r"const WA_NUMBER = '22890000000';",
    r"const WA_NUMBER = '{{ business.owner_phone|replace('+', '') if business.owner_phone else '' }}';",
    content
)

with open('app/templates/vitrine.html', 'w', encoding='utf-8') as f:
    f.write(content)
