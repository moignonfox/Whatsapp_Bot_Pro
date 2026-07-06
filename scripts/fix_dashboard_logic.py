import sys

file_path = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\templates\master\dashboard.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Computed status
old_tr = '{% for b in businesses %}\n                      <tr class="business-row" data-status="{{ b.status|default(\'active\') }}">'
new_tr = """{% for b in businesses %}
                      {% set computed_status = b.status|default('active') %}
                      {% if dict(b).get('is_active') == 0 and dict(b).get('deletion_scheduled_at') %}
                          {% set computed_status = 'deleted' %}
                      {% endif %}
                      <tr class="business-row" data-status="{{ computed_status }}">"""
content = content.replace(old_tr, new_tr)

# 2. Utiliser computed_status pour les boutons
old_actions_block = """{% if b.status == 'archived' %}
                                  <a href="javascript:void(0)" onclick="openStatusModal('{{ b.id }}', 'active')" class="action-link" style="color:#25D366;"><i class="fas fa-undo"></i> Restaurer</a> &nbsp;|&nbsp;
                                  <a href="javascript:void(0)" onclick="openStatusModal('{{ b.id }}', 'deleted')" class="action-link" style="color:#ef4444;"><i class="fas fa-trash"></i> Supprimer</a>
                              {% elif b.status == 'deleted' %}
                                  <a href="javascript:void(0)" onclick="openStatusModal('{{ b.id }}', 'active')" class="action-link" style="color:#25D366;"><i class="fas fa-undo"></i> Restaurer</a> &nbsp;|&nbsp;
                                  <a href="javascript:void(0)" onclick="deleteImmediate('{{ b.id }}')" class="action-link" style="color:#ef4444;" title="Purger immédiatement"><i class="fas fa-times-circle"></i> Purger</a>
                                  <br><span style="font-size: 10px; color: #ef4444; font-weight: bold; margin-top: 4px; display:inline-block;"><i class="fas fa-clock"></i> Sup. le {{ (b.deletion_scheduled_at|string)[:10] if b.deletion_scheduled_at else '???' }}</span>
                              {% else %}
                                  <a href="javascript:void(0)" onclick="openStatusModal('{{ b.id }}', 'archived')" class="action-link" style="color:#F0B429;"><i class="fas fa-archive"></i> Archiver</a> &nbsp;|&nbsp;
                                  <a href="javascript:void(0)" onclick="openStatusModal('{{ b.id }}', 'deleted')" class="action-link" style="color:#ef4444;"><i class="fas fa-trash"></i> Supprimer</a>
                              {% endif %}"""

new_actions_block = """{% if computed_status == 'archived' %}
                                  <a href="javascript:void(0)" onclick="openStatusModal('{{ b.id }}', 'active')" class="action-link" style="color:#25D366;"><i class="fas fa-undo"></i> Restaurer</a> &nbsp;|&nbsp;
                                  <a href="javascript:void(0)" onclick="openStatusModal('{{ b.id }}', 'deleted')" class="action-link" style="color:#ef4444;"><i class="fas fa-trash"></i> Supprimer</a>
                              {% elif computed_status == 'deleted' %}
                                  <a href="javascript:void(0)" onclick="openStatusModal('{{ b.id }}', 'active')" class="action-link" style="color:#25D366;"><i class="fas fa-undo"></i> Restaurer</a> &nbsp;|&nbsp;
                                  <a href="javascript:void(0)" onclick="deleteImmediate('{{ b.id }}')" class="action-link" style="color:#ef4444;" title="Purger immédiatement"><i class="fas fa-times-circle"></i> Purger</a>
                                  <br><span style="font-size: 10px; color: #ef4444; font-weight: bold; margin-top: 4px; display:inline-block;"><i class="fas fa-clock"></i> Sup. le {{ (b.deletion_scheduled_at|string)[:10] if b.deletion_scheduled_at else '???' }}</span>
                              {% else %}
                                  <a href="javascript:void(0)" onclick="openStatusModal('{{ b.id }}', 'archived')" class="action-link" style="color:#F0B429;"><i class="fas fa-archive"></i> Archiver</a> &nbsp;|&nbsp;
                                  <a href="javascript:void(0)" onclick="openStatusModal('{{ b.id }}', 'deleted')" class="action-link" style="color:#ef4444;"><i class="fas fa-trash"></i> Supprimer</a>
                              {% endif %}"""
content = content.replace(old_actions_block, new_actions_block)


# 3. Injecter le CSRF Token et header
old_fetch_post = """        const r = await fetch(`/master/business/${currentBizId}/change_status`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({master_password: pwd, status: currentTargetStatus})
        });"""

new_fetch_post = """        const csrfToken = "{{ csrf_token() }}";
        const r = await fetch(`/master/business/${currentBizId}/change_status`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({master_password: pwd, status: currentTargetStatus})
        });"""
content = content.replace(old_fetch_post, new_fetch_post)

old_fetch_del = """        const r = await fetch(`/master/business/${bizId}?immediate=true`, { method: 'DELETE' });"""
new_fetch_del = """        const csrfToken = "{{ csrf_token() }}";
        const r = await fetch(`/master/business/${bizId}?immediate=true`, { 
            method: 'DELETE',
            headers: {'X-CSRFToken': csrfToken}
        });"""
content = content.replace(old_fetch_del, new_fetch_del)


with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
