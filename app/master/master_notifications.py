"""Routes API pour les notifications Master."""
from flask import Blueprint, jsonify, session
from app.services import notification_master_service

master_notifications_bp = Blueprint('master_notifications', __name__, url_prefix='/master/notifications')

@master_notifications_bp.before_request
def check_master_auth():
    if not session.get('is_master'):
        return jsonify({'error': 'Accès non autorisé'}), 403

@master_notifications_bp.route('', methods=['GET'])
def get_notifications():
    """Récupère les notifications non lues."""
    notifs = notification_master_service.get_unread_notifications(limit=20)
    return jsonify({'notifications': notifs})

@master_notifications_bp.route('/<int:notif_id>/read', methods=['PUT'])
def mark_read(notif_id):
    """Marque une notification comme lue."""
    notification_master_service.mark_as_read(notif_id)
    return jsonify({'success': True})

@master_notifications_bp.route('/read-all', methods=['PUT'])
def mark_all_read():
    """Marque toutes les notifications comme lues."""
    notification_master_service.mark_all_as_read()
    return jsonify({'success': True})
