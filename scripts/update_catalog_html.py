import re

with open('app/templates/dashboard/catalog.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Add edit-btn class to CSS
css_pattern = r'\.delete-btn \{'
css_replacement = r'''.edit-btn {
            color: var(--brand, #5b6af0);
            background: rgba(91,106,240,0.1);
            border: none;
            width: 32px;
            height: 32px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: 0.2s;
            text-decoration: none;
        }
        .edit-btn:hover {
            background: var(--brand, #5b6af0);
            color: white;
        }
        
        .delete-btn {'''
content = re.sub(css_pattern, css_replacement, content)

# Add Edit button in product footer
btn_pattern = r'<a href="\{\{ url_for\(\'dashboard.delete_catalog_product\', biz_id=biz_id, product_id=product.id\) \}\}" \s*class="delete-btn" \s*onclick="return confirm\(\'Supprimer définitivement ce produit \?\'\)"\s*title="Supprimer">\s*<i class="fas fa-trash"></i>\s*</a>'

btn_replacement = r'''<div style="display: flex; gap: 8px;">
                                <button class="edit-btn" 
                                   onclick="openEditModal('{{ product.id }}', '{{ product.nom|replace('\'', '\\\'') }}', '{{ product.categorie|replace('\'', '\\\'') }}', '{{ product.prix }}', '{{ product.description|replace('\n', '\\n')|replace('\'', '\\\'') if product.description else '' }}', {{ 'true' if product.is_visible else 'false' }})"
                                   title="Éditer">
                                    <i class="fas fa-pen"></i>
                                </button>
                                <a href="{{ url_for('dashboard.delete_catalog_product', biz_id=biz_id, product_id=product.id) }}" 
                                   class="delete-btn" 
                                   onclick="return confirm('Supprimer définitivement ce produit ?')"
                                   title="Supprimer">
                                    <i class="fas fa-trash"></i>
                                </a>
                            </div>'''

content = re.sub(btn_pattern, btn_replacement, content)

# Add Edit Modal and JS
modal_pattern = r'<script src="\{\{ url_for\(\'static\', filename=\'js/theme.js\'\) \}\}">.*'
modal_replacement = r'''<!-- Modal Edition Produit -->
<div id="editModal" class="modal">
    <div class="modal-content">
        <div class="modal-title">Éditer Produit</div>
        <form id="editForm" method="POST" enctype="multipart/form-data">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
            
            <div class="form-group">
                <label>Nom du produit / service</label>
                <input type="text" name="nom" id="edit_nom" required>
            </div>
            
            <div class="form-group" style="display: flex; gap: 15px;">
                <div style="flex: 1;">
                    <label>Catégorie</label>
                    <input type="text" name="categorie" id="edit_categorie" list="category-list">
                </div>
                <div style="flex: 1;">
                    <label>Prix (FCFA)</label>
                    <input type="number" name="prix" id="edit_prix" required>
                </div>
            </div>

            <div class="form-group">
                <label>Description pour l'IA</label>
                <textarea name="description" id="edit_description" rows="3"></textarea>
            </div>
            
            <div class="form-group" style="display: flex; gap: 15px; align-items: center; margin-top: 10px;">
                <div style="flex: 1;">
                    <label>Photo du produit (Optionnel)</label>
                    <input type="file" name="image" accept="image/*" style="padding: 6px;">
                </div>
                <div style="flex: 1; display: flex; align-items: center; gap: 8px;">
                    <input type="checkbox" name="is_visible" id="edit_is_visible" style="width:auto; transform: scale(1.2);">
                    <label for="edit_is_visible" style="margin:0; cursor:pointer;">Visible sur la vitrine Web</label>
                </div>
            </div>
            
            <div class="modal-actions">
                <button type="button" class="btn-cancel" onclick="document.getElementById('editModal').style.display='none'">Annuler</button>
                <button type="submit" class="btn-submit">Sauvegarder</button>
            </div>
        </form>
    </div>
</div>

<script>
function openEditModal(id, nom, categorie, prix, description, is_visible) {
    document.getElementById('edit_nom').value = nom;
    document.getElementById('edit_categorie').value = categorie;
    document.getElementById('edit_prix').value = prix;
    document.getElementById('edit_description').value = description;
    document.getElementById('edit_is_visible').checked = is_visible;
    
    // Set form action
    document.getElementById('editForm').action = "/admin/{{ biz_id }}/catalog/edit/" + id;
    
    document.getElementById('editModal').style.display = 'flex';
}
</script>
<script src="{{ url_for('static', filename='js/theme.js') }}"></script>
</body>
</html>
'''

content = re.sub(modal_pattern, modal_replacement, content, flags=re.DOTALL)

with open('app/templates/dashboard/catalog.html', 'w', encoding='utf-8') as f:
    f.write(content)
