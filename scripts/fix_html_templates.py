import re
import os

# 1. Modification de clients.html
clients_path = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\templates\dashboard\clients.html'
with open(clients_path, 'r', encoding='utf-8') as f:
    clients_content = f.read()

clients_old = """<div class="client-name">{{ c.client_name }}</div>"""
clients_new = """<div class="client-name" style="display:flex; flex-direction:column;">
                                        <span style="font-weight:600; color:var(--text);">{{ c.client_display_name or c.client_real_name or c.client_name }}</span>
                                        {% if c.client_display_name and c.client_real_name and c.client_display_name != c.client_real_name %}
                                        <span style="font-size:11px; font-weight:400; color:var(--muted); margin-top:2px;">{{ c.client_real_name }}</span>
                                        {% endif %}
                                    </div>"""
if "c.client_display_name or c.client_real_name" not in clients_content:
    clients_content = clients_content.replace(clients_old, clients_new)
    with open(clients_path, 'w', encoding='utf-8') as f:
        f.write(clients_content)

# 2. Modification de chat.html
chat_path = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\templates\dashboard\chat.html'
with open(chat_path, 'r', encoding='utf-8') as f:
    chat_content = f.read()

# Liste de gauche (côté serveur - jinja)
chat_left_old = """<span class="conv-item-name">{{ conv.client_name }}</span>"""
chat_left_new = """<div class="conv-item-name" style="display:flex; flex-direction:column; line-height:1.2;">
                              <span style="font-weight:600; color:var(--text);">{{ conv.client_display_name or conv.client_real_name or conv.client_name }}</span>
                              {% if conv.client_display_name and conv.client_real_name and conv.client_display_name != conv.client_real_name %}
                              <span style="font-size:11px; font-weight:400; color:var(--muted); margin-top:2px;">{{ conv.client_real_name }}</span>
                              {% endif %}
                          </div>"""
chat_content = chat_content.replace(chat_left_old, chat_left_new)

# L'en-tête de chat (côté HTML)
chat_header_old = """<div class="chat-header-text">
                        <h3 id="current-chat-name">Sélectionnez une conversation</h3>
                        <p id="current-chat-phone">---</p>
                    </div>"""
chat_header_new = """<div class="chat-header-text" style="display:flex; align-items:center; gap:8px;">
                        <div>
                            <div style="display:flex; align-items:center; gap:8px;">
                                <h3 id="current-chat-name" style="margin:0;">Sélectionnez une conversation</h3>
                                <button id="btn-edit-client" onclick="openEditClientModal()" style="display:none; background:none; border:none; color:var(--muted); cursor:pointer; font-size:12px; padding:4px;" title="Modifier le nom">
                                    <i class="fas fa-pen"></i>
                                </button>
                            </div>
                            <p id="current-chat-real-name" style="font-size:11px; color:var(--muted); margin:2px 0 0 0; display:none;"></p>
                            <p id="current-chat-phone" style="margin:2px 0 0 0;">---</p>
                        </div>
                    </div>"""
if 'btn-edit-client' not in chat_content:
    chat_content = chat_content.replace(chat_header_old, chat_header_new)

# Ajout de la modale d'édition dans chat.html (juste avant </body>)
modal_html = """
<!-- Modal Edition Client -->
<div id="editClientModal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.6); z-index:99999; align-items:center; justify-content:center;">
    <div style="background:var(--surface); width:400px; max-width:90%; border-radius:16px; padding:24px; box-shadow:var(--shadow);">
        <h3 style="margin-top:0; color:var(--text); margin-bottom:16px;">Modifier le profil client</h3>
        
        <div style="margin-bottom:16px;">
            <label style="display:block; font-size:12px; font-weight:600; color:var(--muted); margin-bottom:6px;">Nom d'usage / Surnom (Display Name)</label>
            <input type="text" id="edit-display-name" style="width:100%; padding:10px; background:var(--bg); border:1px solid var(--border); border-radius:8px; color:var(--text); font-family:inherit;">
            <p style="font-size:11px; color:var(--muted); margin-top:4px;">C'est ce nom que le bot utilisera dans les campagnes et l'affichage principal.</p>
        </div>
        
        <div style="margin-bottom:24px;">
            <label style="display:block; font-size:12px; font-weight:600; color:var(--muted); margin-bottom:6px;">Nom complet / Légal</label>
            <input type="text" id="edit-real-name" style="width:100%; padding:10px; background:var(--bg); border:1px solid var(--border); border-radius:8px; color:var(--text); font-family:inherit;">
            <p style="font-size:11px; color:var(--muted); margin-top:4px;">Le nom officiel pour la facturation ou la référence.</p>
        </div>

        <div style="display:flex; gap:12px; justify-content:flex-end;">
            <button onclick="closeEditClientModal()" style="padding:10px 16px; border-radius:8px; border:1px solid var(--border); background:var(--bg); color:var(--text); cursor:pointer;">Annuler</button>
            <button onclick="saveClientProfile()" style="padding:10px 16px; border-radius:8px; border:none; background:var(--green); color:#fff; font-weight:600; cursor:pointer;">Enregistrer</button>
        </div>
    </div>
</div>
"""
if "id=\"editClientModal\"" not in chat_content:
    chat_content = chat_content.replace("</body>", modal_html + "\n</body>")

# Modification de la fonction loadConversation pour injecter ces données
load_conv_old = """            document.getElementById('current-chat-name').textContent = data.client_name;
            document.getElementById('current-chat-phone').textContent = data.wa_id;"""
load_conv_new = """            document.getElementById('current-chat-name').textContent = data.client_name || data.wa_id;
            
            const realNameEl = document.getElementById('current-chat-real-name');
            if (data.client_display_name && data.client_real_name && data.client_display_name !== data.client_real_name) {
                realNameEl.textContent = data.client_real_name;
                realNameEl.style.display = 'block';
            } else {
                realNameEl.style.display = 'none';
                realNameEl.textContent = '';
            }
            
            document.getElementById('current-chat-phone').textContent = data.wa_id;
            
            // Préparer la modale
            document.getElementById('edit-display-name').value = data.client_display_name || '';
            document.getElementById('edit-real-name').value = data.client_real_name || '';
            document.getElementById('btn-edit-client').style.display = 'inline-block';"""

if "document.getElementById('btn-edit-client').style.display" not in chat_content:
    chat_content = chat_content.replace(load_conv_old, load_conv_new)

# Fonctions JS pour l'édition
js_functions = """
    function openEditClientModal() {
        document.getElementById('editClientModal').style.display = 'flex';
    }
    function closeEditClientModal() {
        document.getElementById('editClientModal').style.display = 'none';
    }
    async function saveClientProfile() {
        const disp = document.getElementById('edit-display-name').value;
        const real = document.getElementById('edit-real-name').value;
        
        try {
            const res = await fetch(`/admin/{{ biz_id }}/chat/${currentWaId}/profile`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': '{{ csrf_token() }}'
                },
                body: JSON.stringify({ display_name: disp, nom: real })
            });
            const data = await res.json();
            if(data.success) {
                closeEditClientModal();
                // Reload client info softly by triggering loadConversation again
                loadConversation(currentWaId);
            } else {
                alert("Erreur: " + data.error);
            }
        } catch(e) {
            alert("Erreur réseau");
        }
    }
</script>"""
if "function openEditClientModal()" not in chat_content:
    chat_content = chat_content.replace("</script>", js_functions, 1) # Remplace la première balise de fin

with open(chat_path, 'w', encoding='utf-8') as f:
    f.write(chat_content)

print("chat.html and clients.html updated.")
