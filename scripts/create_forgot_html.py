import re
import os

login_path = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\templates\auth\login.html'
forgot_path = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\templates\auth\forgot_password.html'

with open(login_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remplacer le titre
content = re.sub(
    r'<h2 class="form-title">.*?</h2>',
    '<h2 class="form-title">Mot de passe oublié</h2>',
    content,
    flags=re.DOTALL
)

# Changer l'action du form
content = content.replace('action="{{ url_for(\'dashboard.login\') }}"', 'action="{{ url_for(\'dashboard.forgot_password\') }}"')
content = content.replace('action="{{ url_for(\'master.master_login\') }}"', 'action="{{ url_for(\'dashboard.forgot_password\') }}"')

# Retirer le bloc du password et bouton submit et lien oublié
form_pattern = r'<div class="field">.*?<label for="password">Mot de passe</label>.*?</button>'
new_form_content = """<button type="submit" class="btn-submit">
                    Envoyer la demande \u2192
                </button>"""
content = re.sub(form_pattern, new_form_content, content, flags=re.DOTALL)

# Remplacer les boutons social login et le footer (on veut un lien retour vers le login)
social_pattern = r'<!-- Social Login.*?</div>'
content = re.sub(social_pattern, '', content, flags=re.DOTALL)

footer_pattern = r'<div class="form-footer">.*?</div>'
new_footer = """<div class="form-footer">
                <a href="{{ url_for('dashboard.login') }}">\u2190 Retour \u00e0 la connexion</a>
            </div>"""
content = re.sub(footer_pattern, new_footer, content, flags=re.DOTALL)

# G\u00e9rer le bloc {% if success %} qui n'existe pas dans login.html
error_block = r'{% if error %}.*?{% endif %}'
new_flash_blocks = """{% if error %}
            <div class="error-msg">
                <i class="fas fa-exclamation-circle"></i> {{ error }}
            </div>
            {% endif %}
            
            {% if success %}
            <div class="error-msg" style="background: rgba(37,211,102,0.08); border-color: rgba(37,211,102,0.30); color: var(--green);">
                <i class="fas fa-check-circle"></i> {{ success }}
            </div>
            {% endif %}"""
content = re.sub(error_block, new_flash_blocks, content, flags=re.DOTALL)

# Et enlever le bloc is_master du d\u00e9but car c'est pour le dashboard uniquement
content = re.sub(r'{% if is_master %}.*?{% else %}', '', content, flags=re.DOTALL)
content = content.replace('{% endif %}', '', 1) # Retirer le endif du if is_master

with open(forgot_path, 'w', encoding='utf-8') as f:
    f.write(content)
