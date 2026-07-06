import re

filepath = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\templates\master\dashboard.html'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. FIX THE BELL ICON IN TOPBAR
bell_pattern = r'<div class="topbar-right">.*?Accès Master</span>\s*</div>'
new_bell = """<div class="topbar-right">
            <div style="position: relative; cursor: pointer; margin-right: 15px; display: flex; align-items: center; justify-content: center; width: 32px; height: 32px;" onclick="toggleMasterNotifPanel()" title="Notifications">
                <i class="fas fa-bell" style="font-size: 20px; color: var(--text); {% if master_pending_count and master_pending_count > 0 %}animation: ring 2s infinite;{% endif %}"></i>
                {% if master_pending_count and master_pending_count > 0 %}
                <span id="notif-badge" style="position: absolute; top: -4px; right: -4px; background: #ef4444; color: white; font-size: 10px; font-weight: 700; padding: 2px 5px; border-radius: 10px; line-height: 1; border: 2px solid var(--bg); min-width: 14px; text-align: center;">{{ master_pending_count }}</span>
                {% endif %}
            </div>
            <span style="font-size:11px;font-weight:600;background:rgba(248,81,73,0.10);border:1px solid rgba(248,81,73,0.28);color:#F85149;padding:4px 12px;border-radius:20px;">🛡️ Accès Master</span>
        </div>"""
content = re.sub(bell_pattern, new_bell, content, flags=re.DOTALL)


# 2. REPLACE THE PANEL UI
panel_pattern = r'<div id="master-notif-overlay".*?</div>\s*</div>\s*<div id="statusModal"'
new_panel = """<div id="master-notif-overlay" onclick="closeMasterNotifPanel()" style="display:none;position:fixed;inset:0;z-index:9998;background:rgba(0,0,0,0.5); backdrop-filter: blur(4px); transition: opacity 0.3s;"></div>
<div id="master-notif-panel" style="display:none; position:fixed; top:0; right:0; height:100vh; width:400px; max-width:100vw; background:var(--surface); border-left:1px solid var(--border); z-index:9999; flex-direction:column; box-shadow:-8px 0 40px rgba(0,0,0,0.4); transform: translateX(100%); transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);">
    <div style="padding:20px 24px; border-bottom:1px solid var(--border); display:flex; justify-content:space-between; align-items:center; background:var(--bg);">
        <h3 style="margin:0; font-size:18px; font-weight:700; color:var(--text); display:flex; align-items:center; gap:10px;">
            <i class="fas fa-bell" style="color:#58A6FF;"></i> Notifications
        </h3>
        <div style="display:flex; gap:12px;">
            <button onclick="clearAllNotifications()" style="background:rgba(248,81,73,0.1); border:1px solid rgba(248,81,73,0.3); color:#F85149; cursor:pointer; font-size:12px; font-weight:600; padding:6px 12px; border-radius:6px; transition:0.2s;" onmouseover="this.style.background='rgba(248,81,73,0.2)'" onmouseout="this.style.background='rgba(248,81,73,0.1)'">Tout effacer</button>
            <button onclick="closeMasterNotifPanel()" style="background:var(--card); border:1px solid var(--border); color:var(--muted); cursor:pointer; font-size:14px; width:30px; height:30px; border-radius:50%; display:flex; align-items:center; justify-content:center; transition:0.2s;" onmouseover="this.style.color='var(--text)'" onmouseout="this.style.color='var(--muted)'"><i class="fas fa-times"></i></button>
        </div>
    </div>
    <div id="notif-list-container" style="padding:24px; flex:1; overflow-y:auto; display:flex; flex-direction:column; gap:16px; background:var(--bg);">
        {% if master_notifications and master_notifications|length > 0 %}
            {% for notif in master_notifications %}
            <div id="notif-{{ notif.id }}" class="notif-card" style="padding:16px; background:var(--card); border:1px solid var(--border); border-radius:12px; box-shadow:0 4px 12px rgba(0,0,0,0.1); transition: 0.2s; position: relative; overflow: hidden; {% if not notif.is_read %}border-left:4px solid #58A6FF;{% endif %}" onmouseover="this.style.transform='translateY(-2px)'; this.querySelector('.notif-delete-btn').style.opacity='1';" onmouseout="this.style.transform='translateY(0)'; this.querySelector('.notif-delete-btn').style.opacity='0';">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom: 8px;">
                    <div style="display:flex; align-items:center; gap:8px;">
                        {% if notif.type == 'alerte' %}
                            <div style="width:28px; height:28px; border-radius:50%; background:rgba(248,81,73,0.1); color:#F85149; display:flex; align-items:center; justify-content:center; font-size:12px;"><i class="fas fa-exclamation-triangle"></i></div>
                        {% elif notif.type == 'inscription' %}
                            <div style="width:28px; height:28px; border-radius:50%; background:rgba(37,211,102,0.1); color:#25D366; display:flex; align-items:center; justify-content:center; font-size:12px;"><i class="fas fa-user-plus"></i></div>
                        {% else %}
                            <div style="width:28px; height:28px; border-radius:50%; background:rgba(88,166,255,0.1); color:#58A6FF; display:flex; align-items:center; justify-content:center; font-size:12px;"><i class="fas fa-info"></i></div>
                        {% endif %}
                        <h4 style="margin:0; font-size:15px; font-weight:600; color:var(--text);">{{ notif.title }}</h4>
                    </div>
                    <button class="notif-delete-btn" onclick="deleteNotification({{ notif.id }})" style="opacity:0; background:transparent; border:none; color:var(--muted); cursor:pointer; padding:4px; transition:0.2s;" onmouseover="this.style.color='#F85149'" onmouseout="this.style.color='var(--muted)'"><i class="fas fa-trash"></i></button>
                </div>
                <p style="margin:0 0 8px 36px; font-size:13px; color:var(--muted); line-height:1.5;">{{ notif.message }}</p>
                <div style="margin-left: 36px; font-size:11px; color:var(--border); font-weight:500;">
                    <i class="far fa-clock" style="margin-right:4px;"></i> {{ notif.created_at|truncate(16, true, '') }}
                </div>
            </div>
            {% endfor %}
        {% else %}
            <div id="no-notif-text" style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; color:var(--muted); gap:16px;">
                <i class="far fa-bell-slash" style="font-size:32px; opacity:0.5;"></i>
                <p style="font-size:14px; font-weight:500;">Aucune notification pour le moment.</p>
            </div>
        {% endif %}
    </div>
</div>

<div id="statusModal" """
content = re.sub(panel_pattern, new_panel, content, flags=re.DOTALL)


# 3. REPLACE THE JS LOGIC
js_pattern = r'function toggleMasterNotifPanel\(\) \{.*?</script>'
new_js = """function toggleMasterNotifPanel() {
    let p = document.getElementById('master-notif-panel');
    let o = document.getElementById('master-notif-overlay');
    if(p.style.display === 'none' || p.style.display === '') {
        p.style.display = 'flex';
        o.style.display = 'block';
        setTimeout(() => { p.style.transform = 'translateX(0)'; }, 10);
        
        fetch('/master/notifications/mark-read', {
            method: 'POST',
            headers: {'X-CSRFToken': '{{ csrf_token() }}'}
        }).then(() => {
            let badge = document.getElementById('notif-badge');
            if (badge) badge.remove();
            document.querySelector('.fa-bell').style.animation = 'none';
            document.querySelectorAll('.notif-card').forEach(el => el.style.borderLeft = '1px solid var(--border)');
        });
    } else {
        closeMasterNotifPanel();
    }
}
function closeMasterNotifPanel() {
    let p = document.getElementById('master-notif-panel');
    let o = document.getElementById('master-notif-overlay');
    p.style.transform = 'translateX(100%)';
    setTimeout(() => {
        p.style.display = 'none';
        o.style.display = 'none';
    }, 300);
}

async function deleteNotification(id) {
    if(!confirm("Effacer cette notification ?")) return;
    try {
        const r = await fetch(`/master/notifications/${id}`, {
            method: 'DELETE',
            headers: {'X-CSRFToken': '{{ csrf_token() }}'}
        });
        if(r.ok) {
            let card = document.getElementById(`notif-${id}`);
            card.style.transform = 'translateX(100%)';
            card.style.opacity = '0';
            setTimeout(() => card.remove(), 300);
        }
    } catch(e) { console.error(e); }
}

async function clearAllNotifications() {
    if(!confirm("Effacer toutes les notifications ?")) return;
    try {
        const r = await fetch(`/master/notifications/clear-all`, {
            method: 'DELETE',
            headers: {'X-CSRFToken': '{{ csrf_token() }}'}
        });
        if(r.ok) {
            document.getElementById('notif-list-container').innerHTML = `
            <div id="no-notif-text" style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; color:var(--muted); gap:16px;">
                <i class="far fa-bell-slash" style="font-size:32px; opacity:0.5;"></i>
                <p style="font-size:14px; font-weight:500;">Aucune notification pour le moment.</p>
            </div>`;
        }
    } catch(e) { console.error(e); }
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
            container.insertAdjacentHTML('beforeend', '<span id="notif-badge" style="position: absolute; top: -4px; right: -4px; background: #ef4444; color: white; font-size: 10px; font-weight: 700; padding: 2px 5px; border-radius: 10px; line-height: 1; border: 2px solid var(--bg); min-width: 14px; text-align: center;">1</span>');
        } else {
            badge.innerText = parseInt(badge.innerText) + 1;
        }

        const notifContainer = document.getElementById('notif-list-container');
        const noNotif = document.getElementById('no-notif-text');
        if (noNotif) noNotif.remove();

        const d = new Date();
        const timeStr = d.toISOString().substring(0, 16).replace('T', ' ');
        
        let iconHtml = `<div style="width:28px; height:28px; border-radius:50%; background:rgba(88,166,255,0.1); color:#58A6FF; display:flex; align-items:center; justify-content:center; font-size:12px;"><i class="fas fa-info"></i></div>`;
        if(data.type === 'alerte') {
            iconHtml = `<div style="width:28px; height:28px; border-radius:50%; background:rgba(248,81,73,0.1); color:#F85149; display:flex; align-items:center; justify-content:center; font-size:12px;"><i class="fas fa-exclamation-triangle"></i></div>`;
        } else if (data.type === 'inscription') {
            iconHtml = `<div style="width:28px; height:28px; border-radius:50%; background:rgba(37,211,102,0.1); color:#25D366; display:flex; align-items:center; justify-content:center; font-size:12px;"><i class="fas fa-user-plus"></i></div>`;
        }

        const newNotifHTML = `
            <div id="notif-${data.id}" class="notif-card" style="padding:16px; background:var(--card); border:1px solid var(--border); border-radius:12px; box-shadow:0 4px 12px rgba(0,0,0,0.1); transition: 0.2s; position: relative; overflow: hidden; border-left:4px solid #58A6FF;" onmouseover="this.style.transform='translateY(-2px)'; this.querySelector('.notif-delete-btn').style.opacity='1';" onmouseout="this.style.transform='translateY(0)'; this.querySelector('.notif-delete-btn').style.opacity='0';">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom: 8px;">
                    <div style="display:flex; align-items:center; gap:8px;">
                        ${iconHtml}
                        <h4 style="margin:0; font-size:15px; font-weight:600; color:var(--text);">${data.title || data.type}</h4>
                    </div>
                    <button class="notif-delete-btn" onclick="deleteNotification(${data.id})" style="opacity:0; background:transparent; border:none; color:var(--muted); cursor:pointer; padding:4px; transition:0.2s;" onmouseover="this.style.color='#F85149'" onmouseout="this.style.color='var(--muted)'"><i class="fas fa-trash"></i></button>
                </div>
                <p style="margin:0 0 8px 36px; font-size:13px; color:var(--muted); line-height:1.5;">${data.message}</p>
                <div style="margin-left: 36px; font-size:11px; color:var(--border); font-weight:500;">
                    <i class="far fa-clock" style="margin-right:4px;"></i> ${timeStr}
                </div>
            </div>
        `;
        notifContainer.insertAdjacentHTML('afterbegin', newNotifHTML);
    });
</script>"""
content = re.sub(js_pattern, new_js, content, flags=re.DOTALL)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
