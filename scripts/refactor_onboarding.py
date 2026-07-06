import re
import os

# 1. Ajouter generate_bot_prompt_from_answers dans ai_service.py
ai_service_path = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\services\ai_service.py'
with open(ai_service_path, 'r', encoding='utf-8') as f:
    ai_content = f.read()

prompt_generator_code = """
def generate_bot_prompt_from_answers(nom: str, business_type: str, location: str, bot_tasks: list, tone: str, business_info: str) -> str:
    \"\"\"Génère un system_prompt initial de qualité à partir des réponses d'onboarding.\"\"\"
    tasks_text = "\\n".join([f"- {t}" for t in bot_tasks]) if isinstance(bot_tasks, list) else bot_tasks
    
    template = f\"\"\"Tu es l'assistant virtuel de {nom}, un(e) {business_type} situé(e) à {location}.

Ton rôle principal est de :
{tasks_text}

Tu t'adresses aux clients avec un ton {tone}.

Informations importantes sur l'établissement :
{business_info}

Règles importantes :
- Tu réponds uniquement en rapport avec {nom}
- Si tu ne connais pas la réponse, tu invites le client à contacter directement l'établissement
- Tu ne donnes jamais d'informations sur d'autres établissements
\"\"\"
    return template
"""
if "generate_bot_prompt_from_answers" not in ai_content:
    ai_content += "\n" + prompt_generator_code
    with open(ai_service_path, 'w', encoding='utf-8') as f:
        f.write(ai_content)

# 2. Mise à jour de app/api/auth.py
api_auth_path = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\api\auth.py'
with open(api_auth_path, 'r', encoding='utf-8') as f:
    api_content = f.read()

# Remplacer les champs requis et la création
old_register_block = re.search(r"def register\(\):.*?business_repo\.create_business_registration.*?\)", api_content, re.DOTALL)
if old_register_block:
    new_register_block = """def register():
    data = request.get_json() or {}

    # Nouveaux champs d'onboarding IA
    required_fields = ['email', 'password', 'nom', 'owner_name', 'owner_phone', 'business_type', 'devise', 'requested_bot_phone', 'ville', 'bot_tasks', 'tone', 'business_info']
    for field in required_fields:
        if not data.get(field):
            return jsonify({"success": False, "error": f"Champ requis manquant : {field}"}), 400

    email = data['email'].strip().lower()

    # VǸrifier si l'email est dǸj utilisǸ
    if business_repo.get_by_email(email):
        return jsonify({"success": False, "error": "Cet email est dǸj utilisǸ"}), 400

    biz_id = str(uuid.uuid4())
    password_hash = generate_password_hash(data['password'])
    
    # Générer le prompt avec l'IA Service
    from app.services.ai_service import generate_bot_prompt_from_answers
    generated_prompt = generate_bot_prompt_from_answers(
        data['nom'].strip(),
        data['business_type'].strip(),
        data['ville'].strip(),
        data['bot_tasks'], # list
        data['tone'].strip(),
        data['business_info'].strip()
    )

    try:
        business_repo.create_business_registration(
            biz_id,
            email,
            password_hash,
            data['nom'].strip(),
            data['owner_name'].strip(),
            data['owner_phone'].strip(),
            data['requested_bot_phone'].strip(),
            data['business_type'].strip(),
            data['devise'].strip(),
            prompt=generated_prompt
        )"""
    api_content = api_content.replace(old_register_block.group(0), new_register_block)
    with open(api_auth_path, 'w', encoding='utf-8') as f:
        f.write(api_content)


# 3. Mise à jour de app/dashboard/routes.py
dash_routes_path = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\dashboard\routes.py'
with open(dash_routes_path, 'r', encoding='utf-8') as f:
    dash_content = f.read()

# Remplacer le bloc register
old_dash_register = re.search(r"def register\(\):.*?business_repo\.create_business_registration.*?\)", dash_content, re.DOTALL)
if old_dash_register:
    new_dash_register = """def register():
    \"\"\"Inscription autonome d'un nouveau partenaire business (Wizard Onboarding).\"\"\"
    if request.method == 'POST':
        # On peut recevoir du JSON (API/Ajax via fetch dans le JS du Wizard) ou du Form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
            # Bot tasks est une liste, request.form.getlist
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
        
        # Nouveaux champs
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

        biz_id = str(uuid.uuid4())
        hashed = generate_password_hash(password)
        
        # Generation du prompt
        from app.services.ai_service import generate_bot_prompt_from_answers
        generated_prompt = generate_bot_prompt_from_answers(
            nom.strip(), business_type.strip(), ville.strip(), bot_tasks, tone.strip(), business_info.strip() if business_info else ""
        )

        business_repo.create_business_registration(
            biz_id, email, hashed, nom, owner_name, owner_phone, requested_bot_phone, business_type, devise, prompt=generated_prompt
        )"""
    dash_content = dash_content.replace(old_dash_register.group(0), new_dash_register)
    
    # Remplacer également les return render_template par des jsonify si json
    dash_content = dash_content.replace("        return redirect(url_for('dashboard.login'))", 
        "        if request.is_json: return jsonify({'success': True, 'message': 'Inscription rǸussie.'})\n        return redirect(url_for('dashboard.login'))")
        
    with open(dash_routes_path, 'w', encoding='utf-8') as f:
        f.write(dash_content)

print("Python backend refactored for new onboarding logic.")
