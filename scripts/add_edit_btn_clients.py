import re

filepath = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\templates\dashboard\clients.html'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Ajouter le bouton "Éditer" dans la table HTML
old_btn_chat = """<a href="{{ url_for('dashboard.chat_inbox', biz_id=biz_id) }}?wa_id={{ c.wa_id }}" 
class="btn-chat">
                                <i class="fas fa-comment-dots"></i> Chatter
                            </a>"""

new_btn_chat = """<div style="display:flex; gap:8px;">
                                <button onclick="openEditClientModal('{{ c.wa_id }}', '{{ c.client_display_name or '' }}', '{{ c.client_real_name or '' }}')" class="btn-chat" style="background:var(--surface); color:var(--text); border:1px solid var(--border);">
                                    <i class="fas fa-pen"></i> Modifier
                                </button>
                                <a href="{{ url_for('dashboard.chat_inbox', biz_id=biz_id) }}?wa_id={{ c.wa_id }}" class="btn-chat">
                                    <i class="fas fa-comment-dots"></i> Chatter
                                </a>
                            </div>"""

if "openEditClientModal" not in content:
    # Remplacer (en gérant les retours à la ligne / blancs avec une regex)
    content = re.sub(r'<a href="\{\{ url_for\(\'dashboard\.chat_inbox\', biz_id=biz_id\) \}\}\?wa_id=\{\{ c\.wa_id \}\}"\s*class="btn-chat">\s*<i class="fas fa-comment-dots"></i> Chatter\s*</a>', new_btn_chat, content, flags=re.DOTALL)


# 2. Ajouter la modale (si pas déjà là) et le JS
modal_html = """
<!-- Modal Edition Client -->
<div id="editClientModal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.6); z-index:99999; align-items:center; justify-content:center;">
    <div style="background:var(--surface); width:400px; max-width:90%; border-radius:16px; padding:24px; box-shadow:var(--shadow);">
        <h3 style="margin-top:0; color:var(--text); margin-bottom:16px;">Modifier le profil client</h3>
        
        <input type="hidden" id="edit-wa-id">
        
        <div style="margin-bottom:16px;">
            <label style="display:block; font-size:12px; font-weight:600; color:var(--muted); margin-bottom:6px;">Nom d'usage / Surnom (Display Name)</label>
            <input type="text" id="edit-display-name" style="width:100%; padding:10px; background:var(--bg); border:1px solid var(--border); border-radius:8px; color:var(--text); font-family:inherit;">
            <p style="font-size:11px; color:var(--muted); margin-top:4px;">Ce nom sera utilisé par le bot (campagnes, chat).</p>
        </div>
        
        <div style="margin-bottom:24px;">
            <label style="display:block; font-size:12px; font-weight:600; color:var(--muted); margin-bottom:6px;">Nom complet / Légal</label>
            <input type="text" id="edit-real-name" style="width:100%; padding:10px; background:var(--bg); border:1px solid var(--border); border-radius:8px; color:var(--text); font-family:inherit;">
        </div>

        <div style="display:flex; gap:12px; justify-content:flex-end;">
            <button onclick="closeEditClientModal()" style="padding:10px 16px; border-radius:8px; border:1px solid var(--border); background:var(--bg); color:var(--text); cursor:pointer;">Annuler</button>
            <button onclick="saveClientProfile()" style="padding:10px 16px; border-radius:8px; border:none; background:var(--green); color:#fff; font-weight:600; cursor:pointer;">Enregistrer</button>
        </div>
    </div>
</div>

<script>
    function openEditClientModal(waId, displayName, realName) {
        document.getElementById('edit-wa-id').value = waId;
        document.getElementById('edit-display-name').value = displayName;
        document.getElementById('edit-real-name').value = realName;
        document.getElementById('editClientModal').style.display = 'flex';
    }
    
    function closeEditClientModal() {
        document.getElementById('editClientModal').style.display = 'none';
    }
    
    async function saveClientProfile() {
        const waId = document.getElementById('edit-wa-id').value;
        const disp = document.getElementById('edit-display-name').value;
        const real = document.getElementById('edit-real-name').value;
        
        try {
            const res = await fetch(`/admin/{{ biz_id }}/chat/${waId}/profile`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': '{{ csrf_token() }}'
                },
                body: JSON.stringify({ display_name: disp, nom: real })
            });
            const data = await res.json();
            if(data.success) {
                window.location.reload();
            } else {
                alert("Erreur: " + data.error);
            }
        } catch(e) {
            alert("Erreur réseau");
        }
    }
</script>
"""

if "id=\"editClientModal\"" not in content:
    content = content.replace("</body>", modal_html + "\n</body>")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
