import re

# 1. Mise à jour de business_repo.py
repo_path = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\repositories\business_repo.py'
with open(repo_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_func_def = """def create_business_registration(
    biz_id: str,
    email: str,
    password: str,
    nom: str,
    owner_name: str,
    owner_phone: str,
    requested_bot_phone: str,
    business_type: str,
    devise: str
) -> None:"""

new_func_def = """def create_business_registration(
    biz_id: str,
    email: str,
    password: str,
    nom: str,
    owner_name: str,
    owner_phone: str,
    requested_bot_phone: str,
    business_type: str,
    devise: str,
    prompt: str = ""
) -> None:"""

old_insert = """        \"\"\"INSERT INTO businesses
           (id, email, password, nom, owner_name, owner_phone, requested_bot_phone, business_type, devise, is_approved, is_active, plan_abonnement, prompt, msg_confirm, msg_cancel, msg_ready)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 1, 'BASIC', '', '', '', '')\"\"\",
        (biz_id, email, password, nom, owner_name, owner_phone, requested_bot_phone, business_type, devise),"""

new_insert = """        \"\"\"INSERT INTO businesses
           (id, email, password, nom, owner_name, owner_phone, requested_bot_phone, business_type, devise, is_approved, is_active, plan_abonnement, prompt, msg_confirm, msg_cancel, msg_ready)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 1, 'BASIC', ?, '', '', '')\"\"\",
        (biz_id, email, password, nom, owner_name, owner_phone, requested_bot_phone, business_type, devise, prompt),"""

if "prompt: str = \"\"" not in content:
    content = content.replace(old_func_def, new_func_def)
    content = content.replace(old_insert, new_insert)
    with open(repo_path, 'w', encoding='utf-8') as f:
        f.write(content)


# 2. Mise à jour de api/auth.py
api_auth_path = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\api\auth.py'
with open(api_auth_path, 'r', encoding='utf-8') as f:
    api_content = f.read()

old_req = "required_fields = ['email', 'password', 'nom', 'owner_name', 'owner_phone', 'business_type', 'devise', 'requested_bot_phone']"
new_req = "required_fields = ['email', 'password', 'nom', 'owner_name', 'owner_phone', 'business_type', 'devise', 'requested_bot_phone', 'description']"

old_create = """        business_repo.create_business_registration(
            biz_id,
            email,
            password_hash,
            data['nom'].strip(),
            data['owner_name'].strip(),
            data['owner_phone'].strip(),
            data['requested_bot_phone'].strip(),
            data['business_type'].strip(),
            data['devise'].strip()
        )"""

new_create = """        business_repo.create_business_registration(
            biz_id,
            email,
            password_hash,
            data['nom'].strip(),
            data['owner_name'].strip(),
            data['owner_phone'].strip(),
            data['requested_bot_phone'].strip(),
            data['business_type'].strip(),
            data['devise'].strip(),
            prompt=data['description'].strip()
        )"""

if "'description'" not in api_content:
    api_content = api_content.replace(old_req, new_req)
    api_content = api_content.replace(old_create, new_create)
    with open(api_auth_path, 'w', encoding='utf-8') as f:
        f.write(api_content)


# 3. Mise à jour de dashboard/routes.py
dash_routes_path = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\dashboard\routes.py'
with open(dash_routes_path, 'r', encoding='utf-8') as f:
    dash_content = f.read()

old_register_block = """        nom = request.form.get('nom')
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password')
        owner_phone = request.form.get('owner_phone')
        prompt = request.form.get('prompt')

        if not (nom and email and password and owner_phone and prompt):
            return render_template('auth/register.html', error="Veuillez remplir tous les champs.")

        # VǸrifier email existant
        if business_repo.get_by_email(email):
            return render_template('auth/register.html', error="Cet email est dǸj utilisǸ.")

        biz_id = str(uuid.uuid4())
        hashed = generate_password_hash(password)

        business_repo.create_business_registration(
            biz_id, email, hashed, nom, nom, owner_phone, owner_phone, 'restaurant', 'FCFA'
        )"""

new_register_block = """        nom = request.form.get('nom')
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password')
        owner_name = request.form.get('owner_name')
        owner_phone = request.form.get('owner_phone')
        business_type = request.form.get('business_type')
        devise = request.form.get('devise')
        requested_bot_phone = request.form.get('requested_bot_phone')
        description = request.form.get('description')

        if not (nom and email and password and owner_name and owner_phone and business_type and devise and requested_bot_phone and description):
            return render_template('auth/register.html', error="Veuillez remplir tous les champs.")

        # VǸrifier email existant
        if business_repo.get_by_email(email):
            return render_template('auth/register.html', error="Cet email est dǸj utilisǸ.")

        biz_id = str(uuid.uuid4())
        hashed = generate_password_hash(password)

        business_repo.create_business_registration(
            biz_id, email, hashed, nom, owner_name, owner_phone, requested_bot_phone, business_type, devise, prompt=description
        )"""

if "request.form.get('description')" not in dash_content:
    dash_content = dash_content.replace(old_register_block, new_register_block)
    with open(dash_routes_path, 'w', encoding='utf-8') as f:
        f.write(dash_content)


# 4. Mise à jour de register.html
html_path = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\templates\auth\register.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html_content = f.read()

old_form = """<form method="POST">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                
                <div class="input-group">
                    <i class="fas fa-building"></i>
                    <input type="text" name="nom" placeholder="Nom de votre entreprise" required>
                </div>

                <div class="input-group">
                    <i class="fas fa-envelope"></i>
                    <input type="email" name="email" placeholder="Adresse Email" required>
                </div>

                <div class="input-group">
                    <i class="fas fa-lock"></i>
                    <input type="password" name="password" placeholder="Mot de passe" required>
                </div>

                <div class="input-group">
                    <i class="fas fa-phone"></i>
                    <input type="text" name="owner_phone" placeholder="Numéro de Téléphone" required>
                </div>

                <div class="input-group">
                    <i class="fas fa-robot"></i>
                    <textarea name="prompt" rows="3" placeholder="Description de l'entreprise pour l'IA (ex: Restaurant rapide à Lomé, propose burgers et pizzas...)" required style="width:100%; border:none; background:transparent; color:var(--text); font-family:inherit; outline:none; resize:vertical;"></textarea>
                </div>

                <button type="submit" class="btn-primary">Créer mon compte</button>
            </form>"""

new_form = """<form method="POST">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:16px;">
                    <div class="input-group" style="margin-bottom:0;">
                        <i class="fas fa-building"></i>
                        <input type="text" name="nom" placeholder="Nom de l'entreprise" required>
                    </div>
                    <div class="input-group" style="margin-bottom:0;">
                        <i class="fas fa-user"></i>
                        <input type="text" name="owner_name" placeholder="Votre nom (Gérant)" required>
                    </div>
                </div>

                <div class="input-group">
                    <i class="fas fa-envelope"></i>
                    <input type="email" name="email" placeholder="Adresse Email" required>
                </div>

                <div class="input-group">
                    <i class="fas fa-lock"></i>
                    <input type="password" name="password" placeholder="Mot de passe" required>
                </div>

                <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:16px;">
                    <div class="input-group" style="margin-bottom:0;">
                        <i class="fas fa-phone"></i>
                        <input type="text" name="owner_phone" placeholder="Votre téléphone" required>
                    </div>
                    <div class="input-group" style="margin-bottom:0;">
                        <i class="fab fa-whatsapp"></i>
                        <input type="text" name="requested_bot_phone" placeholder="Numéro pour le Bot" required>
                    </div>
                </div>
                
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:16px;">
                    <div class="input-group" style="margin-bottom:0;">
                        <i class="fas fa-store"></i>
                        <select name="business_type" required style="width:100%; border:none; background:transparent; color:var(--text); outline:none;">
                            <option value="restaurant">Restaurant / Fast-Food</option>
                            <option value="boutique">Boutique / E-commerce</option>
                            <option value="service">Services (Coiffure, etc.)</option>
                            <option value="clinique">Clinique / Santé</option>
                            <option value="autre">Autre</option>
                        </select>
                    </div>
                    <div class="input-group" style="margin-bottom:0;">
                        <i class="fas fa-coins"></i>
                        <select name="devise" required style="width:100%; border:none; background:transparent; color:var(--text); outline:none;">
                            <option value="FCFA">FCFA</option>
                            <option value="EUR">Euro (€)</option>
                            <option value="USD">Dollar ($)</option>
                        </select>
                    </div>
                </div>

                <div class="input-group" style="flex-direction:column; align-items:flex-start; padding:16px;">
                    <div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
                        <i class="fas fa-robot" style="color:var(--muted); position:static; transform:none;"></i>
                        <label style="font-weight:600; font-size:13px; color:var(--text);">Description du business pour l'IA</label>
                    </div>
                    <p style="font-size:11px; color:var(--muted); margin:0 0 12px 0; line-height:1.4;">Décrivez exactement ce que fait votre entreprise. L'Assistant IA utilisera ce texte comme "prompt" pour comprendre vos produits, vos tarifs, vos règles et savoir comment répondre à vos clients.</p>
                    <textarea name="description" rows="4" placeholder="Ex: Restaurant rapide à Lomé. Nous vendons des burgers (2000F) et pizzas (3000F). La livraison coûte 1000F. Soyez très accueillant et direct..." required style="width:100%; border:1px solid var(--border); border-radius:8px; padding:12px; background:var(--bg); color:var(--text); font-family:inherit; outline:none; resize:vertical;"></textarea>
                </div>

                <button type="submit" class="btn-primary">Créer mon compte</button>
            </form>"""

if 'name="description"' not in html_content:
    html_content = html_content.replace(old_form, new_form)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

print("Unified registration forms successfully.")
