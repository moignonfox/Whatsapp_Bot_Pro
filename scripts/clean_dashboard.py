import re

file_path = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\templates\master\dashboard.html'
with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Remplacements typiques de corruption UTF-8 / CP1252
replacements = {
    'Ã©': 'é',
    'Ã¨': 'è',
    'Ã ': 'à',
    'Ã¢': 'â',
    'Ãª': 'ê',
    'Ã´': 'ô',
    'Ã§': 'ç',
    'â€”': '—',
    'â€™': "'",
    'TÃ©l GÃ©rant': 'Tél Gérant',
    'Bot DemandÃ©': 'Bot Demandé',
    'ArchivǸs': 'Archivés',
    'SupprimǸs': 'Supprimés',
    'ActivitǸ': 'Activité',
    'SociǸtǸs': 'Sociétés',
    'immǸdiatement': 'immédiatement',
    'CrǸer': 'Créer',
    'paramtres': 'paramètres',
    'Y>?': '🛡️',
    'Y"?': '🛡️',
    'sT?': '⚙️',
    'Y"': '🏢',
    'Y?': '🏢',
    'Paramtres': 'Paramètres',
    'Accs': 'Accès'
}

for bad, good in replacements.items():
    content = content.replace(bad, good)

# Nettoyer les '' isolés restants
content = content.replace('', '')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
