"""Routes API pour le marketing (Application Mobile)."""
import os
import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from google import genai

from app.api import api_bp
from app.repositories import business_repo, conversation_repo, marketing_repo

@api_bp.route('/marketing/send-campaign', methods=['POST'])
@jwt_required()
def send_campaign():
    biz_id = get_jwt_identity()
    business = business_repo.get_by_id(biz_id)
    if not business:
        return jsonify({"success": False, "error": "Business introuvable"}), 404

    plan = dict(business).get('plan_abonnement', 'BASIC')
    
    data = request.get_json() or {}
    message_text = data.get('message', '').strip()
    template_name = data.get('template_name', '').strip()
    variables = data.get('variables', [])
    target = data.get('target', 'all')
    
    if template_name:
        import json
        message_template = json.dumps({
            "template_name": template_name,
            "variables": variables
        }, ensure_ascii=False)
    elif message_text:
        message_template = message_text
    else:
        return jsonify({"success": False, "error": "Le message ou le template est vide"}), 400

    # 1. Vérification de la fréquence (1/3 jours BASIC, 1/jour PRO, 3/jour PREMIUM)
    today_count = marketing_repo.get_today_campaigns_count(biz_id)
    if plan == 'BASIC':
        if today_count >= 1: # Simplification: on limite à 1 par jour au lieu de 1/3 jours pour éviter une requête SQL complexe
            return jsonify({"success": False, "error": "Plan BASIC : Limite de 1 campagne par jour atteinte."}), 403
    elif plan == 'PRO':
        if today_count >= 1:
            return jsonify({"success": False, "error": "Plan PRO : Limite de 1 campagne par jour atteinte."}), 403
    else: # PREMIUM
        if today_count >= 3:
            return jsonify({"success": False, "error": "Plan PREMIUM : Limite de 3 campagnes par jour atteinte."}), 403

    # 2. Vérification des cibles selon le plan
    if plan == 'BASIC':
        target = 'all'
    elif plan == 'PRO' and target == 'inactive':
        target = 'active' # PRO n'a pas accès à inactive (30j)

    all_clients = conversation_repo.get_conversations_for_business(biz_id)
    clients_to_send = []

    if target == 'active':
        limit_date = datetime.datetime.now() - datetime.timedelta(days=7)
        for c in all_clients:
            try:
                ts = datetime.datetime.fromisoformat(c['last_timestamp'])
                if ts >= limit_date:
                    clients_to_send.append(c)
            except Exception:
                clients_to_send.append(c)
    elif target == 'inactive':
        limit_date = datetime.datetime.now() - datetime.timedelta(days=30)
        for c in all_clients:
            try:
                ts = datetime.datetime.fromisoformat(c['last_timestamp'])
                if ts < limit_date:
                    clients_to_send.append(c)
            except Exception:
                pass
    else:
        clients_to_send = all_clients

    # 3. Vérification de la limite de clients par plan
    max_clients = 100 if plan == 'BASIC' else (500 if plan == 'PRO' else len(clients_to_send))
    clients_to_send = clients_to_send[:max_clients]

    if not clients_to_send:
        return jsonify({"success": False, "error": "Aucun client ne correspond au ciblage."}), 400

    # 4. Envoi en file d'attente
    count = marketing_repo.enqueue_campaign(biz_id, clients_to_send, message_template)

    return jsonify({
        "success": True,
        "message": f"Campagne mise en attente pour {count} clients !",
        "count": count
    }), 200

@api_bp.route('/marketing/estimate', methods=['POST'])
@jwt_required()
def estimate_campaign():
    biz_id = get_jwt_identity()
    business = business_repo.get_by_id(biz_id)
    if not business:
        return jsonify({"success": False, "error": "Business introuvable"}), 404

    plan = dict(business).get('plan_abonnement', 'BASIC')
    data = request.get_json() or {}
    target = data.get('target', 'all')
    
    today_count = marketing_repo.get_today_campaigns_count(biz_id)
    if plan == 'BASIC' and today_count >= 1:
        return jsonify({"success": False, "error": "Plan BASIC : Limite de 1 campagne par jour atteinte."}), 403
    elif plan == 'PRO' and today_count >= 1:
        return jsonify({"success": False, "error": "Plan PRO : Limite de 1 campagne par jour atteinte."}), 403
    elif plan == 'PREMIUM' and today_count >= 3:
        return jsonify({"success": False, "error": "Plan PREMIUM : Limite de 3 campagnes par jour atteinte."}), 403

    if plan == 'BASIC':
        target = 'all'
    elif plan == 'PRO' and target == 'inactive':
        target = 'active'

    all_clients = conversation_repo.get_conversations_for_business(biz_id)
    clients_to_send = []

    if target == 'active':
        limit_date = datetime.datetime.now() - datetime.timedelta(days=7)
        for c in all_clients:
            try:
                ts = datetime.datetime.fromisoformat(c['last_timestamp'])
                if ts >= limit_date:
                    clients_to_send.append(c)
            except Exception:
                clients_to_send.append(c)
    elif target == 'inactive':
        limit_date = datetime.datetime.now() - datetime.timedelta(days=30)
        for c in all_clients:
            try:
                ts = datetime.datetime.fromisoformat(c['last_timestamp'])
                if ts < limit_date:
                    clients_to_send.append(c)
            except Exception:
                pass
    else:
        clients_to_send = all_clients

    max_clients = 100 if plan == 'BASIC' else (500 if plan == 'PRO' else len(clients_to_send))
    count = min(len(clients_to_send), max_clients)

    return jsonify({"success": True, "count": count}), 200


@api_bp.route('/marketing/improve-ai', methods=['POST'])
@jwt_required()
def improve_message_with_ai():
    """Améliore un message de campagne avec l'IA (Gemini ou Groq)."""
    biz_id = get_jwt_identity()
    business = business_repo.get_by_id(biz_id)
    if not business:
        return jsonify({"success": False, "error": "Business introuvable"}), 404

    data = request.get_json() or {}
    message = data.get('message', '').strip()
    if not message:
        return jsonify({"success": False, "error": "Message vide"}), 400

    from app.services.ai_service import improve_marketing_message
    
    try:
        improved = improve_marketing_message(message)
        return jsonify({"success": True, "improved_message": improved}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
