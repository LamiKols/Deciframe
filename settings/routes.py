"""
Application settings routes
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Setting, OrganizationSettings, AuditLog
import logging
from datetime import datetime

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')
logger = logging.getLogger(__name__)


def admin_required(f):
    """Decorator to require admin access"""
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role.value not in ['Admin', 'Director', 'CEO']:
            flash('Admin access required', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper


@settings_bp.route('/')
@login_required
@admin_required
def settings_index():
    """Display settings dashboard"""
    try:
        # Get organization settings
        org_settings = OrganizationSettings.query.filter_by(
            organization_id=current_user.organization_id
        ).first()
        
        # Get system settings
        system_settings = Setting.query.all()
        
        return render_template('settings/index.html', 
                             org_settings=org_settings,
                             system_settings=system_settings)
    except Exception as e:
        logger.error(f"Error loading settings: {e}")
        flash('Unable to load settings', 'error')
        return redirect(url_for('index'))


@settings_bp.route('/organization', methods=['GET', 'POST'])
@login_required
@admin_required
def organization_settings():
    """Manage organization settings"""
    if request.method == 'GET':
        try:
            org_settings = OrganizationSettings.query.filter_by(
                organization_id=current_user.organization_id
            ).first()
            
            return render_template('settings/organization.html', settings=org_settings)
        except Exception as e:
            logger.error(f"Error loading organization settings: {e}")
            flash('Unable to load organization settings', 'error')
            return redirect(url_for('settings.settings_index'))
    
    try:
        # Get form data
        currency = request.form.get('currency', 'USD')
        date_format = request.form.get('date_format', '%Y-%m-%d')
        timezone = request.form.get('timezone', 'UTC')
        business_hours_start = request.form.get('business_hours_start', '09:00')
        business_hours_end = request.form.get('business_hours_end', '17:00')
        
        # Get or create organization settings
        org_settings = OrganizationSettings.query.filter_by(
            organization_id=current_user.organization_id
        ).first()
        
        if not org_settings:
            org_settings = OrganizationSettings(
                organization_id=current_user.organization_id,
                created_by_id=current_user.id
            )
            db.session.add(org_settings)
        
        # Update settings
        org_settings.currency = currency
        org_settings.date_format = date_format
        org_settings.timezone = timezone
        org_settings.business_hours_start = business_hours_start
        org_settings.business_hours_end = business_hours_end
        org_settings.updated_by_id = current_user.id
        org_settings.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Log the update
        audit_log = AuditLog(
            user_id=current_user.id,
            action='UPDATE_ORGANIZATION_SETTINGS',
            details='Updated organization settings',
            ip_address=request.remote_addr,
            organization_id=current_user.organization_id
        )
        db.session.add(audit_log)
        db.session.commit()
        
        flash('Organization settings updated successfully', 'success')
        return redirect(url_for('settings.organization_settings'))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating organization settings: {e}")
        flash('Failed to update organization settings', 'error')
        return redirect(url_for('settings.organization_settings'))


@settings_bp.route('/system', methods=['GET', 'POST'])
@login_required
@admin_required
def system_settings():
    """Manage system settings"""
    # Only allow Admin role for system settings
    if current_user.role.value != 'Admin':
        flash('System settings require Admin privileges', 'error')
        return redirect(url_for('settings.settings_index'))
    
    if request.method == 'GET':
        try:
            settings = Setting.query.order_by(Setting.key).all()
            return render_template('settings/system.html', settings=settings)
        except Exception as e:
            logger.error(f"Error loading system settings: {e}")
            flash('Unable to load system settings', 'error')
            return redirect(url_for('settings.settings_index'))
    
    try:
        # Create new setting
        key = request.form.get('key', '').strip()
        value = request.form.get('value', '').strip()
        description = request.form.get('description', '').strip()
        
        if not key or not value:
            flash('Key and value are required', 'error')
            return redirect(url_for('settings.system_settings'))
        
        # Check for duplicate keys
        existing = Setting.query.filter_by(key=key).first()
        if existing:
            flash('Setting key already exists', 'error')
            return redirect(url_for('settings.system_settings'))
        
        # Create setting
        setting = Setting(
            key=key,
            value=value,
            description=description
        )
        
        db.session.add(setting)
        db.session.commit()
        
        # Log the creation
        audit_log = AuditLog(
            user_id=current_user.id,
            action='CREATE_SYSTEM_SETTING',
            details=f'Created system setting: {key}',
            ip_address=request.remote_addr,
            organization_id=current_user.organization_id
        )
        db.session.add(audit_log)
        db.session.commit()
        
        flash('System setting created successfully', 'success')
        return redirect(url_for('settings.system_settings'))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating system setting: {e}")
        flash('Failed to create system setting', 'error')
        return redirect(url_for('settings.system_settings'))


@settings_bp.route('/system/<int:setting_id>/update', methods=['POST'])
@login_required
@admin_required
def update_system_setting(setting_id):
    """Update a system setting"""
    if current_user.role.value != 'Admin':
        return jsonify({'error': 'Admin privileges required'}), 403
    
    try:
        setting = Setting.query.get(setting_id)
        if not setting:
            return jsonify({'error': 'Setting not found'}), 404
        
        data = request.get_json()
        value = data.get('value', '').strip()
        
        if not value:
            return jsonify({'error': 'Value is required'}), 400
        
        old_value = setting.value
        setting.value = value
        db.session.commit()
        
        # Log the update
        audit_log = AuditLog(
            user_id=current_user.id,
            action='UPDATE_SYSTEM_SETTING',
            details=f'Updated {setting.key}: {old_value} -> {value}',
            ip_address=request.remote_addr,
            organization_id=current_user.organization_id
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Setting updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating system setting: {e}")
        return jsonify({'error': 'Failed to update setting'}), 500


@settings_bp.route('/system/<int:setting_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_system_setting(setting_id):
    """Delete a system setting"""
    if current_user.role.value != 'Admin':
        return jsonify({'error': 'Admin privileges required'}), 403
    
    try:
        setting = Setting.query.get(setting_id)
        if not setting:
            return jsonify({'error': 'Setting not found'}), 404
        
        setting_key = setting.key
        db.session.delete(setting)
        db.session.commit()
        
        # Log the deletion
        audit_log = AuditLog(
            user_id=current_user.id,
            action='DELETE_SYSTEM_SETTING',
            details=f'Deleted system setting: {setting_key}',
            ip_address=request.remote_addr,
            organization_id=current_user.organization_id
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Setting deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting system setting: {e}")
        return jsonify({'error': 'Failed to delete setting'}), 500


@settings_bp.route('/api/currencies')
@login_required
def api_currencies():
    """API endpoint for available currencies"""
    currencies = [
        {'code': 'USD', 'name': 'US Dollar', 'symbol': '$'},
        {'code': 'EUR', 'name': 'Euro', 'symbol': '€'},
        {'code': 'GBP', 'name': 'British Pound', 'symbol': '£'},
        {'code': 'CAD', 'name': 'Canadian Dollar', 'symbol': 'C$'},
        {'code': 'AUD', 'name': 'Australian Dollar', 'symbol': 'A$'},
        {'code': 'JPY', 'name': 'Japanese Yen', 'symbol': '¥'},
        {'code': 'CNY', 'name': 'Chinese Yuan', 'symbol': '¥'},
        {'code': 'INR', 'name': 'Indian Rupee', 'symbol': '₹'}
    ]
    
    return jsonify({'currencies': currencies})


@settings_bp.route('/api/timezones')
@login_required
def api_timezones():
    """API endpoint for available timezones"""
    import pytz
    
    timezones = []
    for tz in pytz.common_timezones:
        timezones.append({
            'value': tz,
            'label': tz.replace('_', ' ')
        })
    
    return jsonify({'timezones': sorted(timezones, key=lambda x: x['label'])})