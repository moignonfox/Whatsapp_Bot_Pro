import re

filepath = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\templates\master\dashboard.html'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Ajouter les styles d'animation si absents
style_keyframes = """
<style>
@keyframes slideInGlobalToast {
    0% { transform: translateY(100px); opacity: 0; }
    100% { transform: translateY(0); opacity: 1; }
}
</style>
"""
if "slideInGlobalToast" not in content:
    content = content.replace("</head>", style_keyframes + "</head>")

# Le bloc final du javascript
final_script = """
<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
<script>
    var socket = io();
    
    function playBeep() {
        try {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            const ctx = new AudioContext();
            const osc = ctx.createOscillator();
            const gainNode = ctx.createGain();
            
            osc.connect(gainNode);
            gainNode.connect(ctx.destination);
            
            osc.type = 'sine';
            osc.frequency.setValueAtTime(880, ctx.currentTime); 
            osc.frequency.setValueAtTime(1108.73, ctx.currentTime + 0.1); 
            
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

    document.addEventListener('click', () => {
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            ctx.resume();
        } catch(e){}
    }, { once: true });

    socket.on('connect', function() {
        socket.emit('rejoindre_room', {room: 'master'});
    });

    function showToastMaster(data) {
        const existing = document.getElementById('global-notif-toast');
        if (existing) existing.remove();

        let color = '#58A6FF';
        let iconClass = 'fa-info';
        if(data.type === 'alerte') { color = '#F85149'; iconClass = 'fa-exclamation-triangle'; }
        else if (data.type === 'inscription') { color = '#25D366'; iconClass = 'fa-user-plus'; }

        const title = data.title || data.type;
        const body = data.message || '';

        const toast = document.createElement('div');
        toast.id = 'global-notif-toast';
        toast.style.cssText = [
            'position:fixed','bottom:24px','right:24px','z-index:99999',
            'background:var(--surface,#1a2233)',`border:1.5px solid ${color}`,
            'border-radius:14px','padding:14px 16px','max-width:340px','min-width:260px',
            'box-shadow:0 10px 40px rgba(0,0,0,0.5)',
            'cursor:pointer','display:flex','align-items:flex-start','gap:12px',
            'animation:slideInGlobalToast 0.35s cubic-bezier(.22,.68,0,1.2)'
        ].join(';');
        
        toast.innerHTML = `
            <div style="width:40px;height:40px;border-radius:50%;background:${color}22;display:flex;align-items:center;justify-content:center;flex-shrink:0;border:1.5px solid ${color};">
                <i class="fas ${iconClass}" style="color:${color};font-size:16px;"></i>
            </div>
            <div style="flex:1;min-width:0;">
                <div style="font-size:13px;font-weight:700;color:var(--text,#e0e6f0);margin-bottom:3px;">${title}</div>
                <div style="font-size:12px;color:var(--muted,#8892a4);overflow:hidden;white-space:nowrap;text-overflow:ellipsis;">${body}</div>
                <div style="font-size:11px;color:${color};margin-top:6px;font-weight:600;">
                    <i class="fas fa-arrow-right" style="font-size:9px;margin-right:3px;"></i>Ouvrir le panneau
                </div>
            </div>
            <button id="global-notif-toast-close" style="background:none;border:none;color:var(--muted,#8892a4);cursor:pointer;font-size:18px;padding:0;line-height:1;flex-shrink:0;">&times;</button>
        `;
        toast.addEventListener('click', function(e) {
            if (e.target.id === 'global-notif-toast-close') { toast.remove(); return; }
            toast.remove();
            toggleMasterNotifPanel();
        });
        document.body.appendChild(toast);
        setTimeout(() => toast && toast.remove(), 8000);
    }

    socket.on('master_notification', function(data) {
        playBeep();
        showToastMaster(data);
        
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

# Replace the existing script block with the updated one
script_pattern = r'<script src="https://cdnjs\.cloudflare\.com/ajax/libs/socket\.io/4\.0\.1/socket\.io\.js"></script>.*?</html>'
content = re.sub(script_pattern, final_script, content, flags=re.DOTALL)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
