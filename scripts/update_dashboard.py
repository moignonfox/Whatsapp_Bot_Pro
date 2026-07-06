import sys
import re

file_path = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\templates\master\dashboard.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Ajouter animation CSS
css_animation = """
        @keyframes ring {
            0% { transform: rotate(0); }
            10% { transform: rotate(15deg); }
            20% { transform: rotate(-10deg); }
            30% { transform: rotate(5deg); }
            40% { transform: rotate(-5deg); }
            50% { transform: rotate(0); }
            100% { transform: rotate(0); }
        }
"""
if "@keyframes ring" not in content:
    content = content.replace('</style>', css_animation + '    </style>')

# 2. Remplacer la topbar-right
topbar_right_old = """<div class="topbar-right">
            <span style="font-size:11px;font-weight:600;background:rgba(248,81,73,0.10);border:1px solid rgba(248,81,73,0.28);color:#F85149;padding:4px 12px;border-radius:20px;">🛡️ Accès Master</span>
        </div>"""

topbar_right_new = """<div class="topbar-right">
            {% if master_pending_count and master_pending_count > 0 %}
            <div style="position: relative; cursor: pointer; margin-right: 15px;" onclick="document.getElementById('clients-section').scrollIntoView({behavior: 'smooth'})" title="Demandes d'inscription en attente">
                <i class="fas fa-bell" style="font-size: 20px; color: var(--text); animation: ring 2s infinite;"></i>
                <span style="position: absolute; top: -6px; right: -8px; background: #ef4444; color: white; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 10px;">{{ master_pending_count }}</span>
            </div>
            {% endif %}
            <span style="font-size:11px;font-weight:600;background:rgba(248,81,73,0.10);border:1px solid rgba(248,81,73,0.28);color:#F85149;padding:4px 12px;border-radius:20px;">🛡️ Accès Master</span>
        </div>"""

# Parfois l'emoji ou l'encodage peut causer des mismatch. Utilisons regex.
topbar_pattern = r'<div class="topbar-right">\s*<span[^>]*>.*Accès Master.*</span>\s*</div>'
content = re.sub(topbar_pattern, topbar_right_new, content)

# 3. Ajouter l'ID
content = content.replace('<h2>🏢 Clients (Businesses)</h2>', '<h2 id="clients-section">🏢 Clients (Businesses)</h2>')
content = content.replace('<h2>&#127970; Clients (Businesses)</h2>', '<h2 id="clients-section">&#127970; Clients (Businesses)</h2>')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
