import re

with open('app/dashboard/routes.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_route = '''@dashboard_bp.route('/admin/<biz_id>/generate-campaign-copy', methods=['POST'])
def generate_campaign_copy(biz_id):
    if 'user_id' not in session or session['user_id'] != biz_id:
        return jsonify({"error": "Non autorisé"}), 403

    instruction = request.json.get('instruction', '')
    if not instruction.strip():
        return jsonify({"error": "Instruction vide"}), 400

    from app.services.ai_service import generate_marketing_copy
    try:
        generated_text = generate_marketing_copy(instruction)
        return jsonify({"copy": generated_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@dashboard_bp.route'''

content = re.sub(r'@dashboard_bp\.route\(\'/admin/<biz_id>/send-campaign.*?@dashboard_bp\.route', lambda m: m.group(0).replace('@dashboard_bp.route', new_route), content, count=1, flags=re.DOTALL)

with open('app/dashboard/routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Added generate_campaign_copy route to routes.py')
