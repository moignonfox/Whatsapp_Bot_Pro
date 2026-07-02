from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.api import api_bp
from app.repositories import order_repo, client_repo, business_repo, tag_repo
from app.services import whatsapp_service

@api_bp.route('/orders', methods=['GET'])
@jwt_required()
def get_orders():
    company_id = get_jwt_identity()
    
    status = request.args.get('status', 'all')
    period = request.args.get('period', 'today')
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
    except ValueError:
        page = 1
        limit = 20

    raw_reservations = order_repo.get_by_business(company_id, period=period)
    
    # Filter by status if not all
    if status != 'all':
        raw_reservations = [r for r in raw_reservations if status.lower() in str(dict(r).get('statut', '')).lower()]
        
    # Pagination
    total = len(raw_reservations)
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_reservations = raw_reservations[start_idx:end_idx]

    reservations = []
    for r in paginated_reservations:
        r_dict = dict(r)
        client = client_repo.get_or_create(company_id, r['wa_id'])
        r_dict['client_name'] = client['nom'] if client else r['wa_id']

        # Fetch tags
        order_tags = tag_repo.get_tags_for_order(r['id'])
        r_dict['tags'] = [dict(t) for t in order_tags]

        reservations.append(r_dict)

    return jsonify({
        "success": True,
        "page": page,
        "limit": limit,
        "total": total,
        "orders": reservations
    }), 200


def _emit_statut_commande(biz_id, res_id, statut):
    """Helper interne — diffuse le changement de statut d'une commande via SocketIO."""
    try:
        from app import socketio
        socketio.emit('statut_commande', {
            'business_id': biz_id,
            'res_id': res_id,
            'statut': statut,
        }, room=biz_id)
    except Exception as e:
        pass


@api_bp.route('/orders/<int:order_id>/status', methods=['PUT'])
@jwt_required()
def update_order_status(order_id):
    company_id = get_jwt_identity()
    data = request.get_json() or {}
    
    new_status = data.get('status')
    if not new_status:
        return jsonify({"success": False, "error": "Le champ 'status' est requis"}), 400

    res = order_repo.get_res_info(order_id)
    if not res or res['business_id'] != company_id:
        return jsonify({"success": False, "error": "Commande introuvable ou accès refusé"}), 404

    # Mapper les statuts API vers les statuts base de données (si nécessaire)
    db_status = new_status
    msg_to_send = None

    if new_status in ["Confirmé ✅", "confirmed"]:
        db_status = "Confirmé ✅"
        msg_to_send = res['msg_confirm'] if res['msg_confirm'] else "Votre demande est confirmée !"
    elif new_status in ["Annulé ❌", "cancelled"]:
        db_status = "Annulé ❌"
        msg_to_send = res['msg_cancel'] if res['msg_cancel'] else "Désolé, nous ne pouvons pas confirmer..."
    elif new_status in ["Prêt ✅", "ready"]:
        db_status = "Prêt ✅"
        msg_to_send = res['msg_ready'] if res['msg_ready'] else "C'est prêt !"

    # Mettre à jour en base
    order_repo.update_status(order_id, db_status)
    
    # Envoyer notification WhatsApp si le statut a un message associé
    if msg_to_send:
        whatsapp_service.send_message(res['wa_id'], msg_to_send, res['whatsapp_phone_id'], res['token_wa'])

    # Emettre l'event SocketIO
    _emit_statut_commande(company_id, order_id, db_status)
    
    # TODO Phase 3: Firebase push notifications for specific events

    return jsonify({
        "success": True, 
        "order_id": order_id, 
        "status": db_status
    }), 200
