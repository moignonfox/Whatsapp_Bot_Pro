from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.api import api_bp
from app.repositories import conversation_repo, business_repo, client_repo
from app.services import whatsapp_service

@api_bp.route('/conversations', methods=['GET'])
@jwt_required()
def get_conversations():
    company_id = get_jwt_identity()

    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
    except ValueError:
        page = 1
        limit = 20

    raw_conversations = conversation_repo.get_conversations_for_business(company_id)
    unread_counts = conversation_repo.get_unread_message_counts_by_client(company_id)

    total = len(raw_conversations)
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_conversations = raw_conversations[start_idx:end_idx]

    conversations = []
    for c in paginated_conversations:
        wa_id = c['wa_id']
        client = client_repo.get_or_create(company_id, wa_id)
        
        client_dict = dict(client) if client else {}
        display_name = client_dict.get('display_name')
        real_name = client_dict.get('nom')
        final_name = display_name if display_name else (real_name if real_name else wa_id)
        
        conversations.append({
            "wa_id": wa_id,
            "client_name": final_name,
            "client_real_name": real_name,
            "client_display_name": display_name,
            "last_message": c['last_message'],
            "last_timestamp": c['last_timestamp'],
            "unread_count": unread_counts.get(wa_id, 0),
            "is_human_mode": business_repo.is_human_mode(company_id, wa_id)
        })

    return jsonify({
        "success": True,
        "page": page,
        "limit": limit,
        "total": total,
        "conversations": conversations
    }), 200


@api_bp.route('/conversations/<wa_id>/messages', methods=['GET'])
@jwt_required()
def get_messages(wa_id):
    company_id = get_jwt_identity()
    
    try:
        limit = int(request.args.get('limit', 50))
    except ValueError:
        limit = 50

    # Marquer comme lu
    conversation_repo.mark_conversation_as_read(wa_id, company_id)

    messages = conversation_repo.get_full_history(wa_id, company_id, limit=limit)
    is_human = business_repo.is_human_mode(company_id, wa_id)
    
    msg_list = []
    for m in messages:
        msg_list.append({
            "id": m['id'],
            "role": m['role'],
            "content": m['content'],
            "timestamp": m['timestamp']
        })

    return jsonify({
        "success": True,
        "wa_id": wa_id,
        "is_human_mode": is_human,
        "messages": msg_list
    }), 200


@api_bp.route('/conversations/<wa_id>/send', methods=['POST'])
@jwt_required()
def send_message(wa_id):
    company_id = get_jwt_identity()
    
    data = request.get_json() or {}
    text = data.get('text')
    if not text:
        return jsonify({"success": False, "error": "Le champ 'text' est requis"}), 400

    business = business_repo.get_by_id(company_id)
    if not business:
        return jsonify({"success": False, "error": "Business introuvable"}), 404

    # Envoi via l'API WhatsApp
    status_code = whatsapp_service.send_message(wa_id, text, business['whatsapp_phone_id'], business['token_wa'])

    if status_code not in (200, 201):
        return jsonify({"success": False, "error": "Erreur lors de l'envoi du message via WhatsApp."}), 500
    
    # Si on est en mode humain, on réinitialise le timer à cet instant précis
    if business_repo.is_human_mode(company_id, wa_id):
        business_repo.set_human_mode(company_id, wa_id, True)

    # Sauvegarde en base avec role 'agent'
    conversation_repo.save_message(wa_id, 'agent', text, company_id)

    # Diffusion au Dashboard via SocketIO
    try:
        from app import socketio
        socketio.emit('nouveau_message', {
            'business_id': company_id,
            'wa_id': wa_id,
            'content': text,
            'role': 'agent',
            'timestamp': 'now'
        }, room=company_id)
    except Exception as e:
        pass

    return jsonify({"success": True}), 200


@api_bp.route('/conversations/<wa_id>/toggle-mode', methods=['PUT'])
@jwt_required()
def toggle_human_mode(wa_id):
    company_id = get_jwt_identity()
    
    data = request.get_json() or {}
    # activate peut être un booléen
    activate = data.get('activate', True)
    
    business_repo.set_human_mode(company_id, wa_id, activate)
    
    # Notifier SocketIO que le mode a changé
    try:
        from app import socketio
        socketio.emit('human_mode_toggled', {
            'business_id': company_id, 
            'wa_id': wa_id, 
            'state': activate
        }, room=company_id)
    except Exception as e:
        pass

    return jsonify({
        "success": True,
        "wa_id": wa_id,
        "is_human_mode": activate
    }), 200

@api_bp.route('/conversations/<wa_id>/client', methods=['PUT'])
@jwt_required()
def update_client_profile(wa_id):
    company_id = get_jwt_identity()
    
    data = request.get_json() or {}
    
    nom = data.get('nom', '').strip()
    display_name = data.get('display_name', '').strip()

    try:
        if nom:
            client_repo.update_name(company_id, wa_id, nom)
        if display_name is not None:
            client_repo.set_display_name(company_id, wa_id, display_name)
            
        return jsonify({"success": True, "message": "Profil mis à jour"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
