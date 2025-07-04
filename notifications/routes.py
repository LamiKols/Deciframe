"""
Notifications Blueprint Routes
Handles notification management UI and API endpoints
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from stateless_auth import get_current_user, redirect_with_auth
from extensions import db
from models import Notification, NotificationTemplate, NotificationEventEnum
from notifications.service import notification_service
from functools import wraps

def require_auth(f):
    """Decorator to require JWT authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            return redirect_with_auth('auth.login')
        return f(*args, **kwargs)
    return decorated_function

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')


@notifications_bp.route('/')
@require_auth
def index():
    """List user notifications with pagination"""
    current_user = get_current_user()
    
    # Get filter parameters
    show_unread_only = request.args.get('unread', 'false').lower() == 'true'
    page = int(request.args.get('page', 1))
    per_page = 20
    
    # Build query
    query = Notification.query.filter_by(user_id=current_user.id)
    
    if show_unread_only:
        query = query.filter_by(read_flag=False)
    
    # Paginate results
    notifications = query.order_by(Notification.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get unread count for badge
    unread_count = Notification.query.filter_by(
        user_id=current_user.id, 
        read_flag=False
    ).count()
    
    return render_template('notifications/index.html',
                         notifications=notifications,
                         unread_count=unread_count,
                         show_unread_only=show_unread_only,
                         current_user=current_user)


@notifications_bp.route('/mark-read/<int:notification_id>', methods=['POST'])
@require_auth
def mark_read(notification_id):
    """Mark a specific notification as read"""
    current_user = get_current_user()
    
    success = notification_service.mark_notification_read(notification_id, current_user.id)
    
    if request.headers.get('Content-Type') == 'application/json':
        return jsonify({'success': success})
    
    if success:
        flash('Notification marked as read', 'success')
    else:
        flash('Failed to mark notification as read', 'error')
    
    return redirect(url_for('notifications.index'))


@notifications_bp.route('/mark-all-read', methods=['POST'])
@require_auth
def mark_all_read():
    """Mark all notifications as read for current user"""
    current_user = get_current_user()
    
    success = notification_service.mark_all_read(current_user.id)
    
    if request.headers.get('Content-Type') == 'application/json':
        return jsonify({'success': success})
    
    if success:
        flash('All notifications marked as read', 'success')
    else:
        flash('Failed to mark notifications as read', 'error')
    
    return redirect(url_for('notifications.index'))


@notifications_bp.route('/api/unread-count')
@require_auth
def api_unread_count():
    """API endpoint to get unread notification count"""
    current_user = get_current_user()
    
    unread_count = Notification.query.filter_by(
        user_id=current_user.id, 
        read_flag=False
    ).count()
    
    return jsonify({'unread_count': unread_count})


@notifications_bp.route('/api/recent')
@require_auth
def api_recent():
    """API endpoint to get recent notifications"""
    current_user = get_current_user()
    limit = int(request.args.get('limit', 5))
    
    notifications = notification_service.get_user_notifications(
        current_user.id, 
        unread_only=False, 
        limit=limit
    )
    
    notification_data = []
    for notification in notifications:
        notification_data.append({
            'id': notification.id,
            'message': notification.message,
            'link': notification.link,
            'read_flag': notification.read_flag,
            'event_type': notification.event_type.value,
            'created_at': notification.created_at.isoformat(),
            'time_ago': _time_ago(notification.created_at)
        })
    
    return jsonify({'notifications': notification_data})


# Admin routes for notification template management
@notifications_bp.route('/admin')
@require_auth
def admin_index():
    """Admin interface for notification templates"""
    current_user = get_current_user()
    
    # Check if user has admin privileges
    if current_user.role.value not in ['Admin', 'Director', 'CEO']:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('notifications.index'))
    
    templates = NotificationTemplate.query.all()
    
    return render_template('notifications/admin.html',
                         templates=templates,
                         current_user=current_user)


@notifications_bp.route('/admin/template/<int:template_id>')
@require_auth
def admin_edit_template(template_id):
    """Edit notification template"""
    current_user = get_current_user()
    
    # Check admin privileges
    if current_user.role.value not in ['Admin', 'Director', 'CEO']:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('notifications.index'))
    
    template = NotificationTemplate.query.get_or_404(template_id)
    
    if request.method == 'POST':
        template.subject = request.form['subject']
        template.body = request.form['body']
        template.email_enabled = 'email_enabled' in request.form
        template.in_app_enabled = 'in_app_enabled' in request.form
        
        try:
            db.session.commit()
            flash('Template updated successfully', 'success')
            return redirect(url_for('notifications.admin_index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Failed to update template: {e}', 'error')
    
    return render_template('notifications/admin_edit.html',
                         template=template,
                         current_user=current_user)


@notifications_bp.route('/admin/test/<int:template_id>', methods=['POST'])
@require_auth
def admin_test_template(template_id):
    """Test notification template by sending to current user"""
    current_user = get_current_user()
    
    # Check admin privileges
    if current_user.role.value not in ['Admin', 'Director', 'CEO']:
        return jsonify({'success': False, 'error': 'Access denied'})
    
    template = NotificationTemplate.query.get_or_404(template_id)
    
    # Create test context data
    test_context = {
        'business_case_code': 'C0001',
        'business_case_title': 'Test Business Case',
        'budget': 50000.0,
        'roi': 150.0,
        'problem_code': 'P0001',
        'problem_title': 'Test Problem',
        'problem_description': 'This is a test problem description.',
        'priority': 'High',
        'department_name': 'Test Department',
        'reporter_name': 'Test User',
        'milestone_name': 'Test Milestone',
        'milestone_description': 'Test milestone description',
        'project_code': 'PRJ0001',
        'project_name': 'Test Project',
        'due_date': '2025-07-01',
        'start_date': '2025-06-01',
        'end_date': '2025-12-31',
        'link': url_for('notifications.index', _external=True)
    }
    
    try:
        success = notification_service.send_notification(
            template.event,
            current_user.id,
            test_context
        )
        
        return jsonify({
            'success': success,
            'message': 'Test notification sent successfully' if success else 'Failed to send test notification'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


def _time_ago(dt):
    """Helper function to format time ago"""
    from datetime import datetime, timezone
    
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    diff = now - dt
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"