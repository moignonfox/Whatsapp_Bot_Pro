import re

filepath = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\templates\master\dashboard.html'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Delete all socket.io script blocks from the bottom
idx = content.find('<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>')
if idx != -1:
    content = content[:idx]

# Let's ensure no other duplicate socket stuff exists
content = re.sub(r'<script src="https://cdnjs\.cloudflare\.com/ajax/libs/socket\.io/.*?</script>', '', content, flags=re.DOTALL)
content = re.sub(r'var socket = io\(\);.*?</script>', '', content, flags=re.DOTALL)

# Add the final, clean script block
final_script = """
<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
<script>
    var socket = io();
    
    // We use a small synthesized double-beep that sounds very "notification-like" and professional
    function playBeep() {
        try {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            const ctx = new AudioContext();
            const osc = ctx.createOscillator();
            const gainNode = ctx.createGain();
            
            osc.connect(gainNode);
            gainNode.connect(ctx.destination);
            
            osc.type = 'sine';
            osc.frequency.setValueAtTime(880, ctx.currentTime); // A5
            osc.frequency.setValueAtTime(1108.73, ctx.currentTime + 0.1); // C#6
            
            gainNode.gain.setValueAtTime(0, ctx.currentTime);
            gainNode.gain.linearRampToValueAtTime(0.5, ctx.currentTime + 0.05);
            gainNode.gain.linearRampToValueAtTime(0, ctx.currentTime + 0.1);
            gainNode.gain.linearRampToValueAtTime(0.5, ctx.currentTime + 0.15);
            gainNode.gain.linearRampToValueAtTime(0, ctx.currentTime + 0.25);
            
            osc.start(ctx.currentTime);
            osc.stop(ctx.currentTime + 0.3);
        } catch(e) {
            console.log('Audio disabled or blocked', e);
        }
    }

    // Try to init audio context on first user interaction to bypass browser autoplay policy
    document.addEventListener('click', () => {
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            ctx.resume();
        } catch(e){}
    }, { once: true });

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
        
        let iconHtml = `<div style="min-width:32px; height:32px; border-radius:50%; background:rgba(88,166,255,0.1); color:#58A6FF; display:flex; align-items:center; justify-content:center; font-size:14px;"><i class="fas fa-info"></i></div>`;
        if(data.type === 'alerte') {
            iconHtml = `<div style="min-width:32px; height:32px; border-radius:50%; background:rgba(248,81,73,0.1); color:#F85149; display:flex; align-items:center; justify-content:center; font-size:14px;"><i class="fas fa-exclamation-triangle"></i></div>`;
        } else if (data.type === 'inscription') {
            iconHtml = `<div style="min-width:32px; height:32px; border-radius:50%; background:rgba(37,211,102,0.1); color:#25D366; display:flex; align-items:center; justify-content:center; font-size:14px;"><i class="fas fa-user-plus"></i></div>`;
        }

        const newNotifHTML = `
            <div id="notif-${data.id}" class="notif-card" style="padding:16px; background:var(--card); border:1px solid var(--border); border-radius:12px; box-shadow:0 4px 12px rgba(0,0,0,0.05); transition: 0.2s; position: relative; display:flex; gap:12px; border-left:4px solid #58A6FF;">
                ${iconHtml}
                <div style="flex:1;">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                        <h4 style="margin:0 0 6px 0; font-size:15px; font-weight:600; color:var(--text);">${data.title || data.type}</h4>
                        <button class="notif-delete-btn" onclick="deleteNotification(${data.id})" style="background:rgba(248,81,73,0.1); border:1px solid rgba(248,81,73,0.2); color:#F85149; cursor:pointer; padding:6px; border-radius:6px; transition:0.2s; display:flex; align-items:center; justify-content:center;" title="Supprimer"><i class="fas fa-trash" style="font-size:12px;"></i></button>
                    </div>
                    <p style="margin:0 0 8px 0; font-size:14px; color:var(--text); line-height:1.5;">${data.message}</p>
                    <div style="font-size:11px; color:var(--muted); font-weight:500;">
                        <i class="far fa-clock" style="margin-right:4px;"></i> ${timeStr}
                    </div>
                </div>
            </div>
        `;
        notifContainer.insertAdjacentHTML('afterbegin', newNotifHTML);
    });
</script>
</body>
</html>
"""

# Replace the closing body html with final_script
content = content.replace("</body>", final_script)
content = content.replace("</html>", "") # Just in case

# Fix the server-side generated cards to match the new layout
old_card_pattern = r'<div id="notif-{{ notif.id }}".*?<div style="margin-left: 36px; font-size:11px; color:var\(--border\); font-weight:500;">.*?</div>\s*</div>'
new_card = """<div id="notif-{{ notif.id }}" class="notif-card" style="padding:16px; background:var(--card); border:1px solid var(--border); border-radius:12px; box-shadow:0 4px 12px rgba(0,0,0,0.05); transition: 0.2s; position: relative; display:flex; gap:12px; {% if not notif.is_read %}border-left:4px solid #58A6FF;{% endif %}">
                {% if notif.type == 'alerte' %}
                    <div style="min-width:32px; height:32px; border-radius:50%; background:rgba(248,81,73,0.1); color:#F85149; display:flex; align-items:center; justify-content:center; font-size:14px;"><i class="fas fa-exclamation-triangle"></i></div>
                {% elif notif.type == 'inscription' %}
                    <div style="min-width:32px; height:32px; border-radius:50%; background:rgba(37,211,102,0.1); color:#25D366; display:flex; align-items:center; justify-content:center; font-size:14px;"><i class="fas fa-user-plus"></i></div>
                {% else %}
                    <div style="min-width:32px; height:32px; border-radius:50%; background:rgba(88,166,255,0.1); color:#58A6FF; display:flex; align-items:center; justify-content:center; font-size:14px;"><i class="fas fa-info"></i></div>
                {% endif %}
                <div style="flex:1;">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                        <h4 style="margin:0 0 6px 0; font-size:15px; font-weight:600; color:var(--text);">{{ notif.title }}</h4>
                        <button class="notif-delete-btn" onclick="deleteNotification({{ notif.id }})" style="background:rgba(248,81,73,0.1); border:1px solid rgba(248,81,73,0.2); color:#F85149; cursor:pointer; padding:6px; border-radius:6px; transition:0.2s; display:flex; align-items:center; justify-content:center;" title="Supprimer"><i class="fas fa-trash" style="font-size:12px;"></i></button>
                    </div>
                    <p style="margin:0 0 8px 0; font-size:14px; color:var(--text); line-height:1.5;">{{ notif.message }}</p>
                    <div style="font-size:11px; color:var(--muted); font-weight:500;">
                        <i class="far fa-clock" style="margin-right:4px;"></i> {{ notif.created_at|truncate(16, true, '') }}
                    </div>
                </div>
            </div>"""
content = re.sub(old_card_pattern, new_card, content, flags=re.DOTALL)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
