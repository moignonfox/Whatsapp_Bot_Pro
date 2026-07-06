import re

filepath = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\templates\master\dashboard.html'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remplacer le badge
badge_pattern = r'{% if master_pending_count and master_pending_count > 0 %}.*?{% endif %}'
new_badge = """{% if master_pending_count and master_pending_count > 0 %}
                <span id="notif-badge" style="position: absolute; top: -6px; right: -8px; background: #ef4444; color: white; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 10px;">{{ master_pending_count }}</span>
                {% endif %}"""
content = re.sub(badge_pattern, new_badge, content, flags=re.DOTALL, count=1)

# 2. Remplacer le panneau de notification html
notif_panel_pattern = r'<div id="master-notif-overlay".*?</div>\s*</div>'
new_panel = """<div id="master-notif-overlay" onclick="closeMasterNotifPanel()" style="display:none;position:fixed;inset:0;z-index:9998;background:rgba(0,0,0,0.35);"></div>
<div id="master-notif-panel" style="display:none; position:fixed; top:0; right:0; height:100vh; width:380px; max-width:95vw; background:var(--surface); border-left:1px solid var(--border); z-index:9999; flex-direction:column; box-shadow:-8px 0 40px rgba(0,0,0,0.4);">
    <div style="padding:20px; border-bottom:1px solid var(--border); display:flex; justify-content:space-between; align-items:center;">
        <h3 style="margin:0; font-size:16px; font-weight:600; color:var(--text);"><i class="fas fa-bell" style="color:var(--green); margin-right:8px;"></i> Notifications</h3>
        <button onclick="closeMasterNotifPanel()" style="background:none; border:none; color:var(--muted); cursor:pointer; font-size:16px;"><i class="fas fa-times"></i></button>
    </div>
    <div id="notif-list-container" style="padding:20px; flex:1; overflow-y:auto; display:flex; flex-direction:column; gap:16px;">
        {% if master_notifications and master_notifications|length > 0 %}
            {% for notif in master_notifications %}
            <div class="notif-card" style="padding:16px; background:var(--card); border:1px solid var(--border); border-radius:12px; {% if not notif.is_read %}border-left:4px solid var(--green);{% endif %}">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <h4 style="margin:0 0 4px 0; font-size:14px; font-weight:600; color:var(--text);">{{ notif.title }}</h4>
                    <span style="font-size:11px; color:var(--muted);">{{ notif.created_at|truncate(16, true, '') }}</span>
                </div>
                <p style="margin:0; font-size:13px; color:var(--muted);">{{ notif.message }}</p>
            </div>
            {% endfor %}
        {% else %}
            <p id="no-notif-text" style="font-size:13px; color:var(--muted); text-align:center; margin-top:40px;">Aucune notification pour le moment.</p>
        {% endif %}
    </div>
</div>"""
content = re.sub(notif_panel_pattern, new_panel, content, flags=re.DOTALL)

# 3. Remplacer le JS de toggle pour inclure le mark as read, et rajouter socket.io/audio
js_pattern = r'function toggleMasterNotifPanel\(\) \{.*?\n</script>'
new_js = """function toggleMasterNotifPanel() {
    let p = document.getElementById('master-notif-panel');
    let o = document.getElementById('master-notif-overlay');
    if(p.style.display === 'none' || p.style.display === '') {
        p.style.display = 'flex';
        o.style.display = 'block';
        
        fetch('/master/notifications/mark-read', {
            method: 'POST',
            headers: {'X-CSRFToken': '{{ csrf_token() }}'}
        }).then(() => {
            let badge = document.getElementById('notif-badge');
            if (badge) badge.remove();
            document.querySelector('.fa-bell').style.animation = 'none';
            // Supprimer la bordure verte
            document.querySelectorAll('.notif-card').forEach(el => el.style.borderLeft = '1px solid var(--border)');
        });
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
    if(firstBtn) filterBusinesses('all', firstBtn);
});
</script>

<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
<script>
    var socket = io();
    var audioCtx = null;
    
    function initAudio() {
        if (!audioCtx) {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        if (audioCtx.state === 'suspended') {
            audioCtx.resume();
        }
    }

    document.addEventListener('click', initAudio, { once: true });

    function playBeep() {
        if (!audioCtx) return;
        const oscillator = audioCtx.createOscillator();
        const gainNode = audioCtx.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioCtx.destination);
        
        oscillator.frequency.value = 880;
        oscillator.type = 'sine';
        gainNode.gain.setValueAtTime(0.3, audioCtx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.5);
        
        oscillator.start(audioCtx.currentTime);
        oscillator.stop(audioCtx.currentTime + 0.5);
    }

    socket.on('connect', function() {
        socket.emit('rejoindre_room', {room: 'master'});
    });

    socket.on('master_notification', function(data) {
        playBeep();
        
        const bellIcon = document.querySelector('.fa-bell');
        let badge = document.getElementById('notif-badge');
        if (!badge) {
            bellIcon.style.animation = 'ring 2s infinite';
            const container = bellIcon.parentElement;
            container.insertAdjacentHTML('beforeend', '<span id="notif-badge" style="position: absolute; top: -6px; right: -8px; background: #ef4444; color: white; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 10px;">1</span>');
        } else {
            badge.innerText = parseInt(badge.innerText) + 1;
        }

        const notifContainer = document.getElementById('notif-list-container');
        const noNotif = document.getElementById('no-notif-text');
        if (noNotif) noNotif.remove();

        const d = new Date();
        const timeStr = d.toISOString().substring(0, 16).replace('T', ' ');

        const newNotifHTML = `
            <div class="notif-card" style="padding:16px; background:var(--card); border:1px solid var(--border); border-radius:12px; border-left:4px solid var(--green);">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <h4 style="margin:0 0 4px 0; font-size:14px; font-weight:600; color:var(--text);">${data.title || data.type}</h4>
                    <span style="font-size:11px; color:var(--muted);">${timeStr}</span>
                </div>
                <p style="margin:0; font-size:13px; color:var(--muted);">${data.message}</p>
            </div>
        `;
        notifContainer.insertAdjacentHTML('afterbegin', newNotifHTML);
    });
</script>"""
content = re.sub(js_pattern, new_js, content, flags=re.DOTALL)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
