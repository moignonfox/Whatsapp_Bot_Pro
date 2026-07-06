import re

file_path = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\templates\master\dashboard.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remplacer la topbar-right pour le bouton notif
topbar_right_pattern = r'<div class="topbar-right">.*?</div>\s*</header>'

new_topbar_right = """<div class="topbar-right">
            <div style="position: relative; cursor: pointer; margin-right: 15px;" onclick="toggleMasterNotifPanel()" title="Notifications">
                <i class="fas fa-bell" style="font-size: 20px; color: var(--text); {% if master_pending_count and master_pending_count > 0 %}animation: ring 2s infinite;{% endif %}"></i>
                {% if master_pending_count and master_pending_count > 0 %}
                <span style="position: absolute; top: -6px; right: -8px; background: #ef4444; color: white; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 10px;">{{ master_pending_count }}</span>
                {% endif %}
            </div>
            <span style="font-size:11px;font-weight:600;background:rgba(248,81,73,0.10);border:1px solid rgba(248,81,73,0.28);color:#F85149;padding:4px 12px;border-radius:20px;">🛡️ Accès Master</span>
        </div>
    </header>"""

# remplacement avec DOTALL pour matcher plusieurs lignes
content = re.sub(topbar_right_pattern, new_topbar_right, content, flags=re.DOTALL)


# 2. Injecter le Notif Panel et le Script  la fin du body
panel_html = """
<div id="master-notif-overlay" onclick="closeMasterNotifPanel()" style="display:none;position:fixed;inset:0;z-index:9998;background:rgba(0,0,0,0.35);"></div>
<div id="master-notif-panel" style="display:none; position:fixed; top:0; right:0; height:100vh; width:380px; max-width:95vw; background:var(--surface); border-left:1px solid var(--border); z-index:9999; flex-direction:column; box-shadow:-8px 0 40px rgba(0,0,0,0.4);">
    <div style="padding:20px; border-bottom:1px solid var(--border); display:flex; justify-content:space-between; align-items:center;">
        <h3 style="margin:0; font-size:16px; font-weight:600; color:var(--text);"><i class="fas fa-bell" style="color:var(--green); margin-right:8px;"></i> Notifications</h3>
        <button onclick="closeMasterNotifPanel()" style="background:none; border:none; color:var(--muted); cursor:pointer; font-size:16px;"><i class="fas fa-times"></i></button>
    </div>
    <div style="padding:20px; flex:1; overflow-y:auto; display:flex; flex-direction:column; gap:16px;">
        {% set pending_found = false %}
        {% for b in businesses if dict(b).get('is_approved', 1) == 0 %}
        {% set pending_found = true %}
        <div style="padding:16px; background:var(--card); border:1px solid var(--border); border-radius:12px; cursor:pointer;" onclick="document.getElementById('clients-section').scrollIntoView({behavior: 'smooth'}); closeMasterNotifPanel();">
            <h4 style="margin:0 0 4px 0; font-size:14px; font-weight:600; color:var(--text);">Demande: {{ b.nom }}</h4>
            <p style="margin:0; font-size:12px; color:var(--muted);">Nouveau compte en attente de validation.</p>
        </div>
        {% endfor %}
        {% if not pending_found %}
        <p style="font-size:13px; color:var(--muted); text-align:center; margin-top:40px;">Aucune nouvelle notification.</p>
        {% endif %}
    </div>
</div>

<script>
function toggleMasterNotifPanel() {
    let p = document.getElementById('master-notif-panel');
    let o = document.getElementById('master-notif-overlay');
    if(p.style.display === 'none' || p.style.display === '') {
        p.style.display = 'flex';
        o.style.display = 'block';
    } else {
        closeMasterNotifPanel();
    }
}
function closeMasterNotifPanel() {
    document.getElementById('master-notif-panel').style.display = 'none';
    document.getElementById('master-notif-overlay').style.display = 'none';
}
</script>
"""

if 'master-notif-overlay' not in content:
    content = content.replace('</body>', panel_html + '\n</body>')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
