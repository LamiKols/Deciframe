"""
Notifications blueprint routes
"""

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
import logging

# Create the blueprint (matches __init__.py)
notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')

logger = logging.getLogger(__name__)


@notifications_bp.route('/')
@login_required
def index():
    """Display notifications list for the current user."""
    try:
        # Import here to avoid circular imports
        from models import Notification
        
        notifications = Notification.query.filter_by(
            user_id=current_user.id,
            organization_id=current_user.organization_id
        ).order_by(Notification.created_at.desc()).limit(50).all()
        
        unread_count = Notification.query.filter_by(
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            read=False
        ).count()
        
        return render_template('notifications/index.html', 
                             notifications=notifications,
                             unread_count=unread_count)
    except Exception as e:
        logger.error(f"Error in notifications index: {e}")
        # Return empty list with error message
        return render_template('notifications/index.html', 
                             notifications=[], 
                             unread_count=0,
                             error="Unable to load notifications")


@notifications_bp.route('/mark-read', methods=['POST'])
@login_required
def mark_read():
    """Mark specific notifications as read."""
    try:
        from models import Notification, db
        
        data = request.get_json() or {}
        notification_ids = data.get('ids', [])
        
        if not notification_ids:
            return jsonify({'error': 'No notification IDs provided'}), 400
            
        # Ensure IDs are integers
        try:
            notification_ids = [int(id) for id in notification_ids]
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid notification IDs'}), 400
        
        # Update notifications for the current user only
        updated = Notification.query.filter(
            Notification.id.in_(notification_ids),
            Notification.user_id == current_user.id,
            Notification.organization_id == current_user.organization_id
        ).update({'read': True}, synchronize_session=False)
        
        db.session.commit()
        
        return jsonify({
            'marked': notification_ids,
            'updated_count': updated
        }), 200
        
    except Exception as e:
        logger.error(f"Error marking notifications as read: {e}")
        return jsonify({'error': 'Failed to mark notifications as read'}), 500


@notifications_bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    """Mark all notifications as read for the current user."""
    try:
        from models import Notification, db
        
        updated = Notification.query.filter_by(
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            read=False
        ).update({'read': True}, synchronize_session=False)
        
        db.session.commit()
        
        return jsonify({
            'marked': 'all',
            'updated_count': updated
        }), 200
        
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {e}")
        return jsonify({'error': 'Failed to mark all notifications as read'}), 500


@notifications_bp.route('/api/count')
@login_required
def notification_count():
    """Get unread notification count for the current user."""
    try:
        from models import Notification
        
        count = Notification.query.filter_by(
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            read=False
        ).count()
        
        return jsonify({'unread_count': count})
        
    except Exception as e:
        logger.error(f"Error getting notification count: {e}")
        return jsonify({'unread_count': 0})