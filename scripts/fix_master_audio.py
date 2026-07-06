import re

filepath = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\templates\master\dashboard.html'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Expression pour trouver l'ancien bloc playBeep et initAudio
old_audio_pattern = r'function playBeep\(\) \{.*?(?=socket\.on\(\'connect\')'

new_audio_block = """let globalAudioCtx = null;

    function initAudioContext() {
        if (!globalAudioCtx) {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            globalAudioCtx = new AudioContext();
        }
        if (globalAudioCtx.state === 'suspended') {
            globalAudioCtx.resume();
        }
    }

    // Autoriser le navigateur à jouer du son lors du moindre clic sur le Dashboard
    document.addEventListener('click', initAudioContext);
    document.addEventListener('keydown', initAudioContext);

    function playBeep() {
        if (!globalAudioCtx) return;
        if (globalAudioCtx.state === 'suspended') globalAudioCtx.resume();

        try {
            const osc = globalAudioCtx.createOscillator();
            const gainNode = globalAudioCtx.createGain();
            
            osc.connect(gainNode);
            gainNode.connect(globalAudioCtx.destination);
            
            osc.type = 'sine';
            osc.frequency.setValueAtTime(880, globalAudioCtx.currentTime); 
            osc.frequency.setValueAtTime(1108.73, globalAudioCtx.currentTime + 0.1); 
            
            gainNode.gain.setValueAtTime(0, globalAudioCtx.currentTime);
            gainNode.gain.linearRampToValueAtTime(0.5, globalAudioCtx.currentTime + 0.05);
            gainNode.gain.linearRampToValueAtTime(0, globalAudioCtx.currentTime + 0.1);
            gainNode.gain.linearRampToValueAtTime(0.5, globalAudioCtx.currentTime + 0.15);
            gainNode.gain.linearRampToValueAtTime(0, globalAudioCtx.currentTime + 0.25);
            
            osc.start(globalAudioCtx.currentTime);
            osc.stop(globalAudioCtx.currentTime + 0.3);
        } catch(e) {
            console.log('Audio error:', e);
        }
    }

    """

content = re.sub(old_audio_pattern, new_audio_block, content, flags=re.DOTALL)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
