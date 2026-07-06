import re

routes_path = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\dashboard\routes.py'

with open(routes_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Je cherche le bloc de def register() jusqu'à la prochaine route ou la fin
match = re.search(r"@dashboard_bp\.route\('/register', methods=\['GET', 'POST'\]\)\ndef register\(\):.*?return render_template\('auth/register\.html'\)", content, re.DOTALL)

if not match:
    # Alternative match
    match = re.search(r"@dashboard_bp\.route\('/register', methods=\['GET', 'POST'\]\)\ndef register\(\):.*?(?:@dashboard_bp|return render_template)", content, re.DOTALL)

new_register = """@dashboard_bp.route('/register', methods=['GET', 'POST'])
def register():
    \"\"\"Inscription autonome d'un nouveau partenaire business (Wizard Onboarding).\"\"\"
    if request.method == 'POST':
        # On peut recevoir du JSON (API/Ajax via fetch dans le JS du Wizard) ou du Form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
            if hasattr(request, 'form') and 'bot_tasks[]' in request.form:
                data['bot_tasks'] = request.form.getlist('bot_tasks[]')
            elif 'bot_tasks' in data and isinstance(data['bot_tasks'], str):
                data['bot_tasks'] = [data['bot_tasks']]
                
        nom = data.get('nom')
        email = data.get('email', '').strip().lower()
        password = data.get('password')
        owner_name = data.get('owner_name')
        owner_phone = data.get('owner_phone')
        business_type = data.get('business_type')
        devise = data.get('devise', 'FCFA')
        requested_bot_phone = data.get('requested_bot_phone')
        
        ville = data.get('ville')
        bot_tasks = data.get('bot_tasks', [])
        tone = data.get('tone')
        business_info = data.get('business_info')

        if not (nom and email and password and owner_name and owner_phone and business_type and ville and tone):
            if request.is_json: return jsonify({"success": False, "error": "Champs manquants."})
            return render_template('auth/register.html', error="Veuillez remplir tous les champs.")

        if business_repo.get_by_email(email):
            if request.is_json: return jsonify({"success": False, "error": "Email dǸj utilisǸ."})
            return render_template('auth/register.html', error="Cet email est dǸj utilisǸ.")

        import uuid
        biz_id = str(uuid.uuid4())
        hashed = generate_password_hash(password)
        
        # Generation du prompt
        from app.services.ai_service import generate_bot_prompt_from_answers
        generated_prompt = generate_bot_prompt_from_answers(
            nom.strip(), business_type.strip(), ville.strip(), bot_tasks, tone.strip(), business_info.strip() if business_info else ""
        )

        business_repo.create_business_registration(
            biz_id, email, hashed, nom, owner_name, owner_phone, requested_bot_phone, business_type, devise, prompt=generated_prompt
        )
        
        if request.is_json:
            return jsonify({'success': True, 'message': 'Inscription rǸussie.'})
        return redirect(url_for('dashboard.login'))

    return render_template('auth/register.html')"""

if match:
    content = content.replace(match.group(0), new_register)
else:
    print("WARNING: Regex match failed in fix_register_route.py")
    
with open(routes_path, 'w', encoding='utf-8') as f:
    f.write(content)

# Changer le nom du bouton dans register.html
html_path = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\templates\auth\register.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html_content = f.read()

html_content = html_content.replace('Lancer mon Bot 🚀', 'Soumettre ma demande')

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print("Backend and Frontend fixed")
