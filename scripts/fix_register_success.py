import re

# 1. Ajouter la notification Master dans dashboard/routes.py
routes_path = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\dashboard\routes.py'
with open(routes_path, 'r', encoding='utf-8') as f:
    routes_content = f.read()

old_insert = """        business_repo.create_business_registration(
            biz_id, email, hashed, nom, owner_name, owner_phone, requested_bot_phone, business_type, devise, prompt=generated_prompt
        )"""

new_insert = """        business_repo.create_business_registration(
            biz_id, email, hashed, nom, owner_name, owner_phone, requested_bot_phone, business_type, devise, prompt=generated_prompt
        )
        
        # M-14 Notification au Master
        try:
            from app.services.notification_master_service import create_master_notification
            create_master_notification('inscription', 'Nouvelle Inscription Web', f"Nouveau Business (Web) : {nom}", biz_id)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to notify master: {e}")"""

if "create_master_notification('inscription'" not in routes_content.split("def register():")[1]:
    routes_content = routes_content.replace(old_insert, new_insert)
    with open(routes_path, 'w', encoding='utf-8') as f:
        f.write(routes_content)


# 2. Remplacer la redirection directe par une page d'attente de succès dans register.html
html_path = r'c:\Users\moign\Daily Projekt\Whatsapp_Bot_Pro\app\templates\auth\register.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html_content = f.read()

old_success = """            if(data.success) {
                window.location.href = '/login';
            }"""

new_success = """            if(data.success) {
                document.querySelector('.wizard-container').innerHTML = `
                    <div style="text-align:center; padding: 40px 20px; animation: fadeIn 0.5s ease;">
                        <i class="fas fa-check-circle" style="font-size:60px; color:var(--success); margin-bottom:20px;"></i>
                        <h2 style="margin:0 0 15px 0; color:var(--text);">Demande soumise !</h2>
                        <p style="color:var(--muted); line-height:1.6; font-size:15px; margin-bottom:30px;">
                            Votre bot a été généré et votre demande est en cours d'analyse.<br>
                            Vous pourrez vous connecter dès que l'administrateur aura validé votre accès.
                        </p>
                        <a href="/login" class="btn btn-primary" style="text-decoration:none; display:inline-block;">Retour à la connexion</a>
                    </div>
                `;
            }"""

html_content = html_content.replace(old_success, new_success)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print("Fixed notifications and success waiting page.")
