"""
Notifications Routes
User notification management endpoints
"""

from flask import render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime

from . import notifications_bp
from models import db, Notification, User


@notifications_bp.route('/')
@login_required
def index():
    """Main notifications page showing user's notifications"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get user's notifications
    notifications_query = Notification.query.filter_by(
        user_id=current_user.id,
        organization_id=current_user.organization_id
    ).order_by(Notification.created_at.desc())
    
    notifications = notifications_query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    # Count unread notifications
    unread_count = Notification.query.filter_by(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        read=False
    ).count()
    
    return render_template('notifications/index.html',
                         notifications=notifications,
                         unread_count=unread_count)


@notifications_bp.route('/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_read(notification_id):
    """Mark a specific notification as read"""
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=current_user.id,
        organization_id=current_user.organization_id
    ).first_or_404()
    
    notification.read = True
    notification.read_at = datetime.utcnow()
    db.session.commit()
    
    if request.is_json:
        return jsonify({
            'success': True,
            'message': 'Notification marked as read'
        })
    
    flash('Notification marked as read', 'success')
    return redirect(url_for('notifications.index'))


@notifications_bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    """Mark all user notifications as read"""
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        read=False
    ).all()
    
    for notification in notifications:
        notification.read = True
        notification.read_at = datetime.utcnow()
    
    db.session.commit()
    
    if request.is_json:
        return jsonify({
            'success': True,
            'message': f'Marked {len(notifications)} notifications as read'
        })
    
    flash(f'Marked {len(notifications)} notifications as read', 'success')
    return redirect(url_for('notifications.index'))


@notifications_bp.route('/delete/<int:notification_id>', methods=['POST'])
@login_required
def delete_notification(notification_id):
    """Delete a specific notification"""
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=current_user.id,
        organization_id=current_user.organization_id
    ).first_or_404()
    
    db.session.delete(notification)
    db.session.commit()
    
    if request.is_json:
        return jsonify({
            'success': True,
            'message': 'Notification deleted'
        })
    
    flash('Notification deleted', 'success')
    return redirect(url_for('notifications.index'))


@notifications_bp.route('/preferences')
@login_required
def preferences():
    """Notification preferences page"""
    return render_template('notifications/preferences.html')


@notifications_bp.route('/preferences', methods=['POST'])
@login_required
def update_preferences():
    """Update notification preferences"""
    # Get form data
    email_notifications = request.form.get('email_notifications') == 'on'
    push_notifications = request.form.get('push_notifications') == 'on'
    workflow_notifications = request.form.get('workflow_notifications') == 'on'
    
    # Update user preferences (assuming we add these fields to User model)
    current_user.email_notifications = email_notifications
    current_user.push_notifications = push_notifications
    current_user.workflow_notifications = workflow_notifications
    
    db.session.commit()
    
    flash('Notification preferences updated', 'success')
    return redirect(url_for('notifications.preferences'))