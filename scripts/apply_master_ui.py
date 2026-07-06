import sys

file_path = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\templates\master\dashboard.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. CSS
css = """
        .tab-btn { background: transparent; border: none; padding: 6px 12px; border-radius: 6px; color: var(--muted); font-size: 13px; font-weight: 600; cursor: pointer; transition: 0.2s; }
        .tab-btn:hover { color: var(--text); }
        .tab-btn.active { background: var(--border); color: var(--text); }
        .business-row { transition: opacity 0.3s; }
        .status-modal { display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); align-items: center; justify-content: center; z-index: 1000; }
        .status-modal-content { background: var(--card); padding: 24px; border-radius: 12px; border: 1px solid var(--border); width: 90%; max-width: 400px; box-shadow: var(--shadow); }
"""
if '.tab-btn {' not in content:
    content = content.replace('    </style>', css + '    </style>')

# 2. La cloche et le panel (dans la topbar-right)
topbar_right_start = content.find('<div class="topbar-right">')
topbar_right_end = content.find('</header>', topbar_right_start)
old_topbar_right = content[topbar_right_start:topbar_right_end]

new_topbar_right = """<div class="topbar-right">
            <div style="position: relative; cursor: pointer; margin-right: 15px;" onclick="toggleMasterNotifPanel()" title="Notifications">
                <i class="fas fa-bell" style="font-size: 20px; color: var(--text); {% if master_pending_count and master_pending_count > 0 %}animation: ring 2s infinite;{% endif %}"></i>
                {% if master_pending_count and master_pending_count > 0 %}
                <span style="position: absolute; top: -6px; right: -8px; background: #ef4444; color: white; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 10px;">{{ master_pending_count }}</span>
                {% endif %}
            </div>
            <span style="font-size:11px;font-weight:600;background:rgba(248,81,73,0.10);border:1px solid rgba(248,81,73,0.28);color:#F85149;padding:4px 12px;border-radius:20px;">🛡️ Accès Master</span>
        </div>
    """
content = content.replace(old_topbar_right, new_topbar_right)

# 3. Les onglets (Tabs)
h2_clients_start = content.find('<h2 id="clients-section">')
if h2_clients_start == -1: h2_clients_start = content.find('<h2>🏢 Clients (Businesses)</h2>')
h2_clients_end = content.find('</h2>', h2_clients_start) + 5
old_h2_clients = content[h2_clients_start:h2_clients_end]

new_h2_clients = """<div style="display: flex; gap: 10px; align-items: center;">
                  <h2 id="clients-section">🏢 Clients (Businesses)</h2>
                  <div style="display: flex; background: var(--surface); padding: 4px; border-radius: 8px; border: 1px solid var(--border); margin-left: 15px;">
                      <button class="tab-btn active" onclick="filterBusinesses('active', this)">Actifs</button>
                      <button class="tab-btn" onclick="filterBusinesses('archived', this)">Archivés</button>
                      <button class="tab-btn" onclick="filterBusinesses('deleted', this)">Supprimés</button>
                  </div>
              </div>"""
content = content.replace(old_h2_clients, new_h2_clients)

# 4. Le status sur la ligne (tr)
content = content.replace('{% for b in businesses %}\n                      <tr>', '{% for b in businesses %}\n                      <tr class="business-row" data-status="{{ b.status|default(\'active\') }}">')

# 5. Les Actions (Archiver, Supprimer, Restaurer)
old_actions = """<a href="{{ url_for('master.view_edit_business', biz_id=b.id) }}" class="action-link">Modifier</a>
                              &nbsp;|&nbsp;
                              <a href="{{ url_for('dashboard.admin_dashboard', biz_id=b.id) }}" class="action-link" style="color:var(--muted);">Dashboard ↗</a>
                          </td>"""
new_actions = """<a href="{{ url_for('master.view_edit_business', biz_id=b.id) }}" class="action-link">Modifier</a>
                              &nbsp;|&nbsp;
                              <a href="{{ url_for('dashboard.admin_dashboard', biz_id=b.id) }}" class="action-link" style="color:var(--muted);">Dashboard ↗</a>
                              
                              <div style="margin-top: 8px; padding-top: 8px; border-top: 1px dashed var(--border);">
                              {% if b.status == 'archived' %}
                                  <a href="javascript:void(0)" onclick="openStatusModal('{{ b.id }}', 'active')" class="action-link" style="color:#25D366;"><i class="fas fa-undo"></i> Restaurer</a> &nbsp;|&nbsp;
                                  <a href="javascript:void(0)" onclick="openStatusModal('{{ b.id }}', 'deleted')" class="action-link" style="color:#ef4444;"><i class="fas fa-trash"></i> Supprimer</a>
                              {% elif b.status == 'deleted' %}
                                  <a href="javascript:void(0)" onclick="openStatusModal('{{ b.id }}', 'active')" class="action-link" style="color:#25D366;"><i class="fas fa-undo"></i> Restaurer</a> &nbsp;|&nbsp;
                                  <a href="javascript:void(0)" onclick="deleteImmediate('{{ b.id }}')" class="action-link" style="color:#ef4444;" title="Purger immédiatement"><i class="fas fa-times-circle"></i> Purger</a>
                                  <br><span style="font-size: 10px; color: #ef4444; font-weight: bold; margin-top: 4px; display:inline-block;"><i class="fas fa-clock"></i> Sup. le {{ (b.deletion_scheduled_at|string)[:10] if b.deletion_scheduled_at else '???' }}</span>
                              {% else %}
                                  <a href="javascript:void(0)" onclick="openStatusModal('{{ b.id }}', 'archived')" class="action-link" style="color:#F0B429;"><i class="fas fa-archive"></i> Archiver</a> &nbsp;|&nbsp;
                                  <a href="javascript:void(0)" onclick="openStatusModal('{{ b.id }}', 'deleted')" class="action-link" style="color:#ef4444;"><i class="fas fa-trash"></i> Supprimer</a>
                              {% endif %}
                              </div>
                          </td>"""
content = content.replace(old_actions, new_actions)

# 6. Injection Modal, Panel JS et JS logic
js_and_modals = """
<div id="master-notif-overlay" onclick="closeMasterNotifPanel()" style="display:none;position:fixed;inset:0;z-index:9998;background:rgba(0,0,0,0.35);"></div>
<div id="master-notif-panel" style="display:none; position:fixed; top:0; right:0; height:100vh; width:380px; max-width:95vw; background:var(--surface); border-left:1px solid var(--border); z-index:9999; flex-direction:column; box-shadow:-8px 0 40px rgba(0,0,0,0.4);">
    <div style="padding:20px; border-bottom:1px solid var(--border); display:flex; justify-content:space-between; align-items:center;">
        <h3 style="margin:0; font-size:16px; font-weight:600; color:var(--text);"><i class="fas fa-bell" style="color:var(--green); margin-right:8px;"></i> Notifications</h3>
        <button onclick="closeMasterNotifPanel()" style="background:none; border:none; color:var(--muted); cursor:pointer; font-size:16px;"><i class="fas fa-times"></i></button>
    </div>
    <div style="padding:20px; flex:1; overflow-y:auto; display:flex; flex-direction:column; gap:16px;">
        {% set pending_found = false %}
        {% for b in businesses %}
            {% if b.is_approved == 0 %}
                {% set pending_found = true %}
                <div style="padding:16px; background:var(--card); border:1px solid var(--border); border-radius:12px; cursor:pointer;" onclick="document.getElementById('clients-section').scrollIntoView({behavior: 'smooth'}); closeMasterNotifPanel();">
                    <h4 style="margin:0 0 4px 0; font-size:14px; font-weight:600; color:var(--text);">Demande: {{ b.nom }}</h4>
                    <p style="margin:0; font-size:12px; color:var(--muted);">Nouveau compte en attente de validation.</p>
                </div>
            {% endif %}
        {% endfor %}
        {% if not pending_found %}
        <p style="font-size:13px; color:var(--muted); text-align:center; margin-top:40px;">Aucune nouvelle notification.</p>
        {% endif %}
    </div>
</div>

<div id="statusModal" class="status-modal">
    <div class="status-modal-content">
        <h3 style="margin-top:0; color:var(--text); font-size:16px;">Vérification de sécurité</h3>
        <p style="font-size:13px; color:var(--muted); margin-bottom:16px;" id="statusModalText">Veuillez entrer votre mot de passe Master pour confirmer l'action.</p>
        <input type="password" id="masterPasswordInput" placeholder="Mot de passe Master" style="width:100%; padding:10px; border-radius:8px; border:1px solid var(--border); background:var(--surface); color:var(--text); margin-bottom:16px;">
        <div style="display:flex; gap:10px; justify-content:flex-end;">
            <button onclick="closeStatusModal()" style="padding:8px 16px; border-radius:6px; border:1px solid var(--border); background:transparent; color:var(--text); cursor:pointer;">Annuler</button>
            <button onclick="confirmStatusChange()" style="padding:8px 16px; border-radius:6px; border:none; background:var(--green); color:white; cursor:pointer; font-weight:bold;">Confirmer</button>
        </div>
    </div>
</div>

<script>
let currentBizId = null;
let currentTargetStatus = null;

function filterBusinesses(status, btn) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    if(btn) btn.classList.add('active');
    
    document.querySelectorAll('.business-row').forEach(row => {
        if(row.getAttribute('data-status') === status) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

function openStatusModal(bizId, targetStatus) {
    currentBizId = bizId;
    currentTargetStatus = targetStatus;
    let actionName = targetStatus === 'archived' ? "l'archivage" : (targetStatus === 'deleted' ? "la suppression (délai 7 jours)" : "la restauration");
    document.getElementById('statusModalText').innerText = `Veuillez entrer votre mot de passe Master pour confirmer ${actionName}.`;
    document.getElementById('masterPasswordInput').value = '';
    document.getElementById('statusModal').style.display = 'flex';
}

function closeStatusModal() {
    document.getElementById('statusModal').style.display = 'none';
    currentBizId = null;
    currentTargetStatus = null;
}

async function confirmStatusChange() {
    const pwd = document.getElementById('masterPasswordInput').value;
    if(!pwd) return alert('Mot de passe requis');
    try {
        const r = await fetch(`/master/business/${currentBizId}/change_status`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({master_password: pwd, status: currentTargetStatus})
        });
        const data = await r.json();
        if(data.success) {
            alert(data.message);
            window.location.reload();
        } else {
            alert("Erreur: " + data.error);
        }
    } catch(e) {
        alert("Erreur réseau.");
    }
}

async function deleteImmediate(bizId) {
    if(!confirm("Êtes-vous sûr de vouloir purger immédiatement ce compte de test ? Cette action est irréversible et ne requiert pas le mot de passe Master pour les tests.")) return;
    try {
        const r = await fetch(`/master/business/${bizId}?immediate=true`, { method: 'DELETE' });
        const data = await r.json();
        if(data.success) {
            alert(data.message);
            window.location.reload();
        } else {
            alert("Erreur: " + data.error);
        }
    } catch(e) {
        alert("Erreur réseau.");
    }
}

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

document.addEventListener('DOMContentLoaded', () => {
    let firstBtn = document.querySelector('.tab-btn.active');
    if(firstBtn) filterBusinesses('active', firstBtn);
});
</script>
"""

if 'master-notif-panel' not in content:
    content = content.replace('</body>', js_and_modals + '\n</body>')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
