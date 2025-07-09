"""
Notifications & Escalations Configuration Routes
Admin-only configuration for notification settings per event
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from models import NotificationSetting, FrequencyEnum, RoleEnum, User
from sqlalchemy.exc import IntegrityError
from functools import wraps
import logging

notifications_config_bp = Blueprint('notifications_config', __name__, url_prefix='/admin/notifications')

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        # Also check for unrestricted admin access (first user in org)
        is_unrestricted_admin = (current_user.is_authenticated and 
                               current_user.role == RoleEnum.Admin and 
                               hasattr(current_user, 'organization_id') and
                               User.query.filter_by(organization_id=current_user.organization_id).count() == 1)
        
        if not current_user.is_authenticated or (current_user.role != RoleEnum.Admin and not is_unrestricted_admin):
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Default notification events that can be configured
DEFAULT_NOTIFICATION_EVENTS = [
    {
        'name': 'problem_created',
        'display_name': 'Problem Created',
        'description': 'When a new problem is reported'
    },
    {
        'name': 'problem_assigned',
        'display_name': 'Problem Assigned',
        'description': 'When a problem is assigned to someone'
    },
    {
        'name': 'problem_resolved',
        'display_name': 'Problem Resolved',
        'description': 'When a problem is marked as resolved'
    },
    {
        'name': 'case_submitted',
        'display_name': 'Business Case Submitted',
        'description': 'When a new business case is submitted'
    },
    {
        'name': 'case_assigned',
        'display_name': 'Business Case Assigned',
        'description': 'When a business case is assigned to a BA'
    },
    {
        'name': 'case_approved',
        'display_name': 'Business Case Approved',
        'description': 'When a business case is approved'
    },
    {
        'name': 'project_created',
        'display_name': 'Project Created',
        'description': 'When a new project is created'
    },
    {
        'name': 'project_milestone_due',
        'display_name': 'Milestone Due Soon',
        'description': 'When a project milestone is due soon'
    },
    {
        'name': 'project_milestone_overdue',
        'display_name': 'Milestone Overdue',
        'description': 'When a project milestone is overdue'
    },
    {
        'name': 'project_completed',
        'display_name': 'Project Completed',
        'description': 'When a project is marked as completed'
    },
    {
        'name': 'task_assigned',
        'display_name': 'Task Assigned',
        'description': 'When a task is assigned to someone'
    },
    {
        'name': 'task_due_soon',
        'display_name': 'Task Due Soon',
        'description': 'When a task is due soon'
    }
]

@notifications_config_bp.route('/')
@admin_required
def notification_settings():
    """Main notification settings page"""
    try:
        print(f"🔧 Notifications Config: Loading for user {current_user.email} (org: {current_user.organization_id})")
        
        # Get all notification settings for current organization
        settings = NotificationSetting.query.filter_by(organization_id=current_user.organization_id).all()
        print(f"🔧 Notifications Config: Found {len(settings)} existing settings")
        settings_dict = {setting.event_name: setting for setting in settings}
        
        # Ensure all default events have settings
        _ensure_default_settings()
        
        # Refresh after ensuring defaults
        settings = NotificationSetting.query.filter_by(organization_id=current_user.organization_id).all()
        print(f"🔧 Notifications Config: After ensuring defaults, found {len(settings)} settings")
        settings_dict = {setting.event_name: setting for setting in settings}
        
        # Prepare display data
        notification_configs = []
        for event in DEFAULT_NOTIFICATION_EVENTS:
            setting = settings_dict.get(event['name'])
            if setting:
                config = {
                    'id': setting.id,
                    'event_name': setting.event_name,
                    'display_name': event['display_name'],
                    'description': event['description'],
                    'frequency': setting.frequency,
                    'threshold_hours': setting.threshold_hours,
                    'channel_email': setting.channel_email,
                    'channel_in_app': setting.channel_in_app,
                    'channel_push': setting.channel_push,
                    'updated_at': setting.updated_at
                }
                notification_configs.append(config)
                print(f"🔧 Config added: {event['name']} -> ID={setting.id}")
        
        print(f"🔧 Notifications Config: Total configs prepared: {len(notification_configs)}")
        
        return render_template('notifications/config/settings.html', 
                             notification_configs=notification_configs,
                             frequency_options=FrequencyEnum)
                             
    except Exception as e:
        logging.error(f"Error loading notification settings: {e}")
        print(f"🚨 Notifications Config Error: {e}")
        flash('Error loading notification settings', 'danger')
        return redirect(url_for('admin_dashboard'))

@notifications_config_bp.route('/edit/<int:setting_id>', methods=['GET', 'POST'])
@admin_required
def edit_setting(setting_id):
    """Edit notification setting"""
    setting = NotificationSetting.query.filter_by(id=setting_id, organization_id=current_user.organization_id).first_or_404()
    
    if request.method == 'POST':
        try:
            # Update setting fields
            frequency_value = request.form.get('frequency')
            if frequency_value:
                setting.frequency = FrequencyEnum(frequency_value)
            
            threshold_hours = request.form.get('threshold_hours')
            if threshold_hours and threshold_hours.isdigit():
                setting.threshold_hours = int(threshold_hours)
            else:
                setting.threshold_hours = None
            
            setting.channel_email = bool(request.form.get('channel_email'))
            setting.channel_in_app = bool(request.form.get('channel_in_app'))
            setting.channel_push = bool(request.form.get('channel_push'))
            
            db.session.commit()
            flash(f'Notification setting for {setting.event_name} updated successfully', 'success')
            return redirect(url_for('notifications_config.notification_settings'))
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating notification setting: {e}")
            flash('Error updating notification setting', 'danger')
    
    # Get display info for this event
    event_info = next((e for e in DEFAULT_NOTIFICATION_EVENTS if e['name'] == setting.event_name), 
                      {'display_name': setting.event_name, 'description': ''})
    
    return render_template('notifications/config/edit_setting.html',
                         setting=setting,
                         event_info=event_info,
                         frequency_options=FrequencyEnum)

@notifications_config_bp.route('/create', methods=['GET', 'POST'])
@admin_required
def create_setting():
    """Create new notification setting"""
    if request.method == 'POST':
        try:
            event_name = request.form.get('event_name')
            if not event_name:
                flash('Event name is required', 'danger')
                return redirect(request.url)
            
            # Check if setting already exists for this organization
            existing = NotificationSetting.query.filter_by(event_name=event_name, organization_id=current_user.organization_id).first()
            if existing:
                flash(f'Setting for {event_name} already exists', 'warning')
                return redirect(url_for('notifications_config.edit_setting', setting_id=existing.id))
            
            frequency_value = request.form.get('frequency', 'immediate')
            threshold_hours = request.form.get('threshold_hours')
            
            setting = NotificationSetting(
                organization_id=current_user.organization_id,
                event_name=event_name,
                frequency=FrequencyEnum(frequency_value),
                threshold_hours=int(threshold_hours) if threshold_hours and threshold_hours.isdigit() else None,
                channel_email=bool(request.form.get('channel_email')),
                channel_in_app=bool(request.form.get('channel_in_app')),
                channel_push=bool(request.form.get('channel_push'))
            )
            
            db.session.add(setting)
            db.session.commit()
            flash(f'Notification setting for {event_name} created successfully', 'success')
            return redirect(url_for('notifications_config.notification_settings'))
            
        except IntegrityError:
            db.session.rollback()
            flash('Setting with this event name already exists', 'danger')
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating notification setting: {e}")
            flash('Error creating notification setting', 'danger')
    
    return render_template('notifications/config/create_setting.html',
                         default_events=DEFAULT_NOTIFICATION_EVENTS,
                         frequency_options=FrequencyEnum)

@notifications_config_bp.route('/delete/<int:setting_id>', methods=['POST'])
@admin_required
def delete_setting(setting_id):
    """Delete notification setting"""
    try:
        setting = NotificationSetting.query.filter_by(id=setting_id, organization_id=current_user.organization_id).first_or_404()
        event_name = setting.event_name
        
        db.session.delete(setting)
        db.session.commit()
        flash(f'Notification setting for {event_name} deleted successfully', 'success')
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting notification setting: {e}")
        flash('Error deleting notification setting', 'danger')
    
    return redirect(url_for('notifications_config.notification_settings'))

@notifications_config_bp.route('/reset-defaults', methods=['POST'])
@admin_required
def reset_defaults():
    """Reset all settings to defaults"""
    try:
        # Delete all existing settings for current organization
        NotificationSetting.query.filter_by(organization_id=current_user.organization_id).delete()
        
        # Create default settings
        _create_default_settings()
        
        db.session.commit()
        flash('All notification settings reset to defaults', 'success')
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error resetting notification settings: {e}")
        flash('Error resetting notification settings', 'danger')
    
    return redirect(url_for('notifications_config.notification_settings'))

@notifications_config_bp.route('/api/test-escalation/<int:setting_id>', methods=['POST'])
@admin_required
def test_escalation(setting_id):
    """Test escalation for a specific setting"""
    try:
        setting = NotificationSetting.query.filter_by(id=setting_id, organization_id=current_user.organization_id).first_or_404()
        
        # Simulate escalation test
        test_result = {
            'event_name': setting.event_name,
            'frequency': setting.frequency.value,
            'threshold_hours': setting.threshold_hours,
            'channels': {
                'email': setting.channel_email,
                'in_app': setting.channel_in_app,
                'push': setting.channel_push
            },
            'test_status': 'success',
            'message': f'Test escalation for {setting.event_name} would trigger after {setting.threshold_hours or "immediate"} hours'
        }
        
        return jsonify(test_result)
        
    except Exception as e:
        logging.error(f"Error testing escalation: {e}")
        return jsonify({'test_status': 'error', 'message': 'Error testing escalation'}), 500

def _ensure_default_settings():
    """Ensure all default events have notification settings"""
    from flask_login import current_user
    
    for event in DEFAULT_NOTIFICATION_EVENTS:
        existing = NotificationSetting.query.filter_by(event_name=event['name'], organization_id=current_user.organization_id).first()
        if not existing:
            # Create default setting
            default_threshold = None
            if 'due_soon' in event['name'] or 'overdue' in event['name']:
                default_threshold = 24  # 24 hours for due/overdue events
            
            setting = NotificationSetting(
                organization_id=current_user.organization_id,
                event_name=event['name'],
                frequency=FrequencyEnum.immediate,
                threshold_hours=default_threshold,
                channel_email=True,
                channel_in_app=True,
                channel_push=False
            )
            db.session.add(setting)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating default notification settings: {e}")

def _create_default_settings():
    """Create all default notification settings"""
    from flask_login import current_user
    
    for event in DEFAULT_NOTIFICATION_EVENTS:
        default_threshold = None
        if 'due_soon' in event['name'] or 'overdue' in event['name']:
            default_threshold = 24  # 24 hours for due/overdue events
        
        setting = NotificationSetting(
            organization_id=current_user.organization_id,
            event_name=event['name'],
            frequency=FrequencyEnum.immediate,
            threshold_hours=default_threshold,
            channel_email=True,
            channel_in_app=True,
            channel_push=False
        )
        db.session.add(setting)

# Add a debug route to test data loading
@notifications_config_bp.route('/debug-data')
@admin_required
def debug_data():
    """Debug route to check notification data"""
    settings = NotificationSetting.query.filter_by(organization_id=current_user.organization_id).all()
    data = {
        'user': current_user.email,
        'organization_id': current_user.organization_id,
        'settings_count': len(settings),
        'settings': [
            {
                'id': s.id,
                'event_name': s.event_name,
                'frequency': s.frequency.value,
                'email': s.channel_email,
                'in_app': s.channel_in_app,
                'push': s.channel_push
            } for s in settings
        ]
    }
    return jsonify(data)