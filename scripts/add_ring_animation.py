import re

filepath = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\templates\master\dashboard.html'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

ring_keyframe = """
@keyframes ring {
    0% { transform: rotate(0); }
    5% { transform: rotate(15deg); }
    10% { transform: rotate(-10deg); }
    15% { transform: rotate(5deg); }
    20% { transform: rotate(-5deg); }
    25% { transform: rotate(0); }
    100% { transform: rotate(0); }
}
"""

if "@keyframes ring" not in content:
    content = content.replace("<style>", "<style>\n" + ring_keyframe)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
