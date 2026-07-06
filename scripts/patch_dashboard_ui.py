import re

file_path = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\templates\master\dashboard.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. CSS additionnel
css_addition = """
        .tab-btn {
            background: transparent; border: none; padding: 6px 12px; border-radius: 6px;
            color: var(--muted); font-size: 13px; font-weight: 600; cursor: pointer; transition: 0.2s;
        }
        .tab-btn:hover { color: var(--text); }
        .tab-btn.active { background: var(--border); color: var(--text); }
        .business-row { transition: opacity 0.3s; }
        .status-modal {
            display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.5); align-items: center; justify-content: center; z-index: 1000;
        }
        .status-modal-content {
            background: var(--card); padding: 24px; border-radius: 12px; border: 1px solid var(--border);
            width: 90%; max-width: 400px; box-shadow: var(--shadow);
        }
"""
if ".tab-btn {" not in content:
    content = content.replace('</style>', css_addition + '    </style>')

# 2. Remplacer h2 Clients
h2_old = r'<h2 id="clients-section">.*?Clients \(Businesses\).*?</h2>'
h2_new = """<div style="display: flex; gap: 10px; align-items: center;">
    <h2 id="clients-section">Y? Clients (Businesses)</h2>
    <div style="display: flex; background: var(--surface); padding: 4px; border-radius: 8px; border: 1px solid var(--border); margin-left: 15px;">
        <button class="tab-btn active" onclick="filterBusinesses('active', this)">Actifs</button>
        <button class="tab-btn" onclick="filterBusinesses('archived', this)">Archivǟs</button>
        <button class="tab-btn" onclick="filterBusinesses('deleted', this)">Supprimǟs</button>
    </div>
</div>"""
content = re.sub(h2_old, h2_new, content)

# 3. Remplacer tr pour les businesses
tr_pattern = r'({%\s*for b in businesses\s*%}\s*)<tr>'
content = re.sub(tr_pattern, r'\1<tr class="business-row" data-status="{{ b.status|default(\'active\') }}">', content)

# 4. Ajouter les actions
actions_old = """<a href="{{ url_for('dashboard.admin_dashboard', biz_id=b.id) }}" class="action-link" style="color:var(--muted);">Dashboard '</a>"""
actions_new = """<a href="{{ url_for('dashboard.admin_dashboard', biz_id=b.id) }}" class="action-link" style="color:var(--muted);">Dashboard '</a>
                              <div style="margin-top: 8px; padding-top: 8px; border-top: 1px dashed var(--border);">
                              {% if b.status == 'archived' %}
                                  <a href="#" onclick="openStatusModal('{{ b.id }}', 'active')" class="action-link" style="color:#25D366;"><i class="fas fa-undo"></i> Restaurer</a> &nbsp;|&nbsp;
                                  <a href="#" onclick="openStatusModal('{{ b.id }}', 'deleted')" class="action-link" style="color:#ef4444;"><i class="fas fa-trash"></i> Supprimer</a>
                              {% elif b.status == 'deleted' %}
                                  <a href="#" onclick="openStatusModal('{{ b.id }}', 'active')" class="action-link" style="color:#25D366;"><i class="fas fa-undo"></i> Restaurer</a> &nbsp;|&nbsp;
                                  <a href="#" onclick="deleteImmediate('{{ b.id }}')" class="action-link" style="color:#ef4444;" title="Purger immǟdiatement"><i class="fas fa-times-circle"></i> Purger</a>
                                  <br><span style="font-size: 10px; color: #ef4444; font-weight: bold; margin-top: 4px; display:inline-block;"><i class="fas fa-clock"></i> Sup. le {{ (b.deletion_scheduled_at|string)[:10] if b.deletion_scheduled_at else '???' }}</span>
                              {% else %}
                                  <a href="#" onclick="openStatusModal('{{ b.id }}', 'archived')" class="action-link" style="color:#F0B429;"><i class="fas fa-archive"></i> Archiver</a> &nbsp;|&nbsp;
                                  <a href="#" onclick="openStatusModal('{{ b.id }}', 'deleted')" class="action-link" style="color:#ef4444;"><i class="fas fa-trash"></i> Supprimer</a>
                              {% endif %}
                              </div>"""
if 'openStatusModal(' not in content:
    content = content.replace(actions_old, actions_new)

# 5. Ajouter modal et JS en bas
js_addition = """
<div id="statusModal" class="status-modal">
    <div class="status-modal-content">
        <h3 style="margin-top:0; color:var(--text); font-size:16px;">Vǟrification de sǟcuritǟ</h3>
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
    btn.classList.add('active');
    
    document.querySelectorAll('.business-row').forEach(row => {
        if(row.getAttribute('data-status') === status) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}
// Initial run
document.addEventListener('DOMContentLoaded', () => {
    let firstBtn = document.querySelector('.tab-btn.active');
    if(firstBtn) filterBusinesses('active', firstBtn);
});

function openStatusModal(bizId, targetStatus) {
    currentBizId = bizId;
    currentTargetStatus = targetStatus;
    
    let actionName = targetStatus === 'archived' ? 'l\'archivage' : (targetStatus === 'deleted' ? 'la suppression (dǟlai 7 jours)' : 'la restauration');
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
        alert("Erreur rǟseau.");
    }
}

async function deleteImmediate(bizId) {
    if(!confirm("Êtes-vous sǖr de vouloir purger immǟdiatement ce compte de test ? Cette action est irrǟversible et ne requiert pas le mot de passe Master pour les tests.")) return;
    
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
        alert("Erreur rǟseau.");
    }
}
</script>
"""
if 'status-modal' not in content:
    content = content.replace('</body>', js_addition + '\n</body>')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
