import re

html_path = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\templates\auth\register.html'
with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Ajouter le token CSRF dans le body pour JS
csrf_meta = '<meta name="csrf-token" content="{{ csrf_token() }}">'
if 'name="csrf-token"' not in content:
    content = content.replace('<head>', '<head>\n    ' + csrf_meta)

# Mettre à jour le Fetch call
old_fetch = """        try {
            const response = await fetch('/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });"""

new_fetch = """        try {
            const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
            const response = await fetch('/register', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(payload)
            });"""

content = content.replace(old_fetch, new_fetch)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Added CSRF token to JS fetch call")
