"""
Additional admin routes for comprehensive management
"""

from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, User, Organization, Department, AuditLog, OrganizationSettings, RoleEnum
from admin.permissions import require_admin, require_super_admin, validate_admin_action
from audit.log import audit_user_action, audit_organization_action, audit_role_change, get_audit_trail
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def init_additional_admin_routes(app):
    """Initialize additional admin routes"""
    
    @app.route('/admin/audit-trail')
    @app.route('/admin/audit_trail')
    @login_required
    @require_admin()
    def admin_audit_trail():
        """Display comprehensive audit trail"""
        try:
            # Get filter parameters
            obj_type = request.args.get('obj_type')
            user_id = request.args.get('user_id')
            days = request.args.get('days', 30, type=int)
            page = request.args.get('page', 1, type=int)
            per_page = 50
            
            # Build query
            query = AuditLog.query
            
            # Organization filter for non-super admins
            if current_user.role.value not in ['Admin', 'CEO']:
                query = query.filter(AuditLog.organization_id == current_user.organization_id)
            
            # Apply filters
            if obj_type:
                query = query.filter(AuditLog.object_type == obj_type)
            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
            if days:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                query = query.filter(AuditLog.timestamp >= cutoff_date)
            
            # Paginate results
            audit_logs = query.order_by(AuditLog.timestamp.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            # Get users for filter dropdown
            users = User.query.filter_by(organization_id=current_user.organization_id).all()
            
            return render_template('admin/audit_trail.html',
                                 audit_logs=audit_logs,
                                 users=users,
                                 filters={
                                     'obj_type': obj_type,
                                     'user_id': user_id,
                                     'days': days
                                 })
            
        except Exception as e:
            logger.error(f"Error loading audit trail: {e}")
            flash('Unable to load audit trail', 'error')
            return redirect(url_for('admin_dashboard'))
    
    @app.route('/admin/assign-department', methods=['POST'])
    @app.route('/admin/assign_department', methods=['POST'])
    @login_required
    @require_admin()
    def admin_assign_department():
        """Assign user to department"""
        try:
            user_id = request.form.get('user_id') or request.json.get('user_id')
            department_id = request.form.get('department_id') or request.json.get('department_id')
            
            if not user_id or not department_id:
                error_msg = 'User ID and Department ID are required'
                if request.is_json:
                    return jsonify({'error': error_msg}), 400
                flash(error_msg, 'error')
                return redirect(request.referrer or url_for('admin_dashboard'))
            
            # Get user and validate access
            user = User.query.filter_by(
                id=user_id,
                organization_id=current_user.organization_id
            ).first()
            
            if not user:
                error_msg = 'User not found or access denied'
                if request.is_json:
                    return jsonify({'error': error_msg}), 404
                flash(error_msg, 'error')
                return redirect(request.referrer or url_for('admin_dashboard'))
            
            # Get department and validate
            department = Department.query.filter_by(
                id=department_id,
                organization_id=current_user.organization_id
            ).first()
            
            if not department:
                error_msg = 'Department not found'
                if request.is_json:
                    return jsonify({'error': error_msg}), 404
                flash(error_msg, 'error')
                return redirect(request.referrer or url_for('admin_dashboard'))
            
            # Validate admin action
            is_valid, message = validate_admin_action('assign_department', target_user=user)
            if not is_valid:
                if request.is_json:
                    return jsonify({'error': message}), 403
                flash(message, 'error')
                return redirect(request.referrer or url_for('admin_dashboard'))
            
            # Store old state for audit
            old_dept_id = user.department_id
            old_dept_name = user.department.name if user.department else 'None'
            
            # Update user department
            user.department_id = department_id
            db.session.commit()
            
            # Create audit log
            audit_user_action(
                'ASSIGN_DEPARTMENT',
                user,
                before_state={'department_id': old_dept_id, 'department_name': old_dept_name},
                after_state={'department_id': department_id, 'department_name': department.name}
            )
            
            success_msg = f'User {user.name} assigned to {department.name}'
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': success_msg,
                    'user_id': user.id,
                    'department_name': department.name
                })
            
            flash(success_msg, 'success')
            return redirect(request.referrer or url_for('admin_dashboard'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error assigning department: {e}")
            error_msg = 'Failed to assign department'
            if request.is_json:
                return jsonify({'error': error_msg}), 500
            flash(error_msg, 'error')
            return redirect(request.referrer or url_for('admin_dashboard'))
    
    @app.route('/admin/regional-settings')
    @app.route('/admin/regional_settings')
    @app.route('/admin/organization-settings')
    @app.route('/admin/organization_settings')
    @login_required
    @require_admin()
    def admin_regional_settings():
        """Manage organization regional settings"""
        try:
            org_settings = OrganizationSettings.query.filter_by(
                organization_id=current_user.organization_id
            ).first()
            
            # Create default settings if none exist
            if not org_settings:
                org_settings = OrganizationSettings(
                    organization_id=current_user.organization_id,
                    currency='USD',
                    date_format='ISO',
                    timezone='UTC',
                    created_by_id=current_user.id
                )
                db.session.add(org_settings)
                db.session.commit()
            
            return render_template('admin/regional_settings.html', settings=org_settings)
            
        except Exception as e:
            logger.error(f"Error loading regional settings: {e}")
            flash('Unable to load regional settings', 'error')
            return redirect(url_for('admin_dashboard'))
    
    @app.route('/admin/regional-settings', methods=['POST'])
    @app.route('/admin/regional_settings', methods=['POST'])
    @app.route('/admin/organization-settings', methods=['POST'])
    @app.route('/admin/organization_settings', methods=['POST'])
    @login_required
    @require_admin()
    def update_regional_settings():
        """Update organization regional settings"""
        try:
            org_settings = OrganizationSettings.query.filter_by(
                organization_id=current_user.organization_id
            ).first()
            
            if not org_settings:
                org_settings = OrganizationSettings(
                    organization_id=current_user.organization_id,
                    created_by_id=current_user.id
                )
                db.session.add(org_settings)
            
            # Store old state for audit
            old_state = {
                'currency': org_settings.currency,
                'date_format': org_settings.date_format,
                'timezone': org_settings.timezone,
                'business_hours_start': org_settings.business_hours_start,
                'business_hours_end': org_settings.business_hours_end
            }
            
            # Update settings
            org_settings.currency = request.form.get('currency', 'USD')
            org_settings.date_format = request.form.get('date_format', 'ISO')
            org_settings.timezone = request.form.get('timezone', 'UTC')
            org_settings.business_hours_start = request.form.get('business_hours_start', '09:00')
            org_settings.business_hours_end = request.form.get('business_hours_end', '17:00')
            org_settings.updated_by_id = current_user.id
            org_settings.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            # Create audit log
            new_state = {
                'currency': org_settings.currency,
                'date_format': org_settings.date_format,
                'timezone': org_settings.timezone,
                'business_hours_start': org_settings.business_hours_start,
                'business_hours_end': org_settings.business_hours_end
            }
            
            audit_organization_action(
                'UPDATE_SETTINGS',
                current_user.organization,
                before_state=old_state,
                after_state=new_state
            )
            
            flash('Regional settings updated successfully', 'success')
            return redirect(url_for('admin_regional_settings'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating regional settings: {e}")
            flash('Failed to update regional settings', 'error')
            return redirect(url_for('admin_regional_settings'))
    
    @app.route('/admin/user-roles')
    @app.route('/admin/user_roles')
    @login_required
    @require_admin()
    def admin_user_roles():
        """Manage user roles"""
        try:
            users = User.query.filter_by(
                organization_id=current_user.organization_id
            ).order_by(User.name).all()
            
            roles = [role.value for role in RoleEnum]
            
            return render_template('admin/user_roles.html', users=users, roles=roles)
            
        except Exception as e:
            logger.error(f"Error loading user roles: {e}")
            flash('Unable to load user roles', 'error')
            return redirect(url_for('admin_dashboard'))
    
    @app.route('/admin/user-roles/<int:user_id>', methods=['POST'])
    @app.route('/admin/user_roles/<int:user_id>', methods=['POST'])
    @login_required
    @require_admin()
    def update_user_role(user_id):
        """Update user role"""
        try:
            user = User.query.filter_by(
                id=user_id,
                organization_id=current_user.organization_id
            ).first()
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            new_role = request.form.get('role') or request.json.get('role')
            if not new_role:
                return jsonify({'error': 'Role is required'}), 400
            
            # Validate role
            try:
                new_role_enum = RoleEnum(new_role)
            except ValueError:
                return jsonify({'error': 'Invalid role'}), 400
            
            # Validate admin action
            is_valid, message = validate_admin_action('change_role', target_user=user)
            if not is_valid:
                return jsonify({'error': message}), 403
            
            # Store old role for audit
            old_role = user.role
            
            # Update role
            user.role = new_role_enum
            db.session.commit()
            
            # Create audit log
            audit_role_change(user, old_role, new_role_enum)
            
            return jsonify({
                'success': True,
                'message': f'Role updated to {new_role}',
                'user_id': user.id,
                'new_role': new_role
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating user role: {e}")
            return jsonify({'error': 'Failed to update role'}), 500
    
    @app.route('/admin/organization-policies')
    @app.route('/admin/organization_policies')
    @app.route('/admin/org-policies')
    @app.route('/admin/org_policies')
    @login_required
    @require_admin()
    def admin_organization_policies():
        """Manage organization policies"""
        try:
            # Get organization settings which include policy configurations
            org_settings = OrganizationSettings.query.filter_by(
                organization_id=current_user.organization_id
            ).first()
            
            if not org_settings:
                org_settings = OrganizationSettings(
                    organization_id=current_user.organization_id,
                    created_by_id=current_user.id
                )
                db.session.add(org_settings)
                db.session.commit()
            
            # Get recent policy changes from audit log
            policy_changes = get_audit_trail(
                obj_type='Organization',
                obj_id=current_user.organization_id,
                limit=20
            )
            
            return render_template('admin/organization_policies.html',
                                 settings=org_settings,
                                 policy_changes=policy_changes)
            
        except Exception as e:
            logger.error(f"Error loading organization policies: {e}")
            flash('Unable to load organization policies', 'error')
            return redirect(url_for('admin_dashboard'))
    
    @app.route('/admin/system-health')
    @app.route('/admin/system_health')
    @login_required
    @require_super_admin()
    def admin_system_health():
        """Display system health dashboard"""
        try:
            # Get system metrics
            total_users = User.query.count()
            active_users = User.query.filter_by(is_active=True).count()
            total_orgs = Organization.query.count()
            
            # Get recent activity
            recent_activity = get_audit_trail(limit=50)
            
            # System health metrics
            health_metrics = {
                'total_users': total_users,
                'active_users': active_users,
                'total_organizations': total_orgs,
                'recent_activity_count': len(recent_activity),
                'database_status': 'healthy',  # Could add actual DB health checks
                'cache_status': 'healthy',
                'queue_status': 'healthy'
            }
            
            return render_template('admin/system_health.html',
                                 metrics=health_metrics,
                                 recent_activity=recent_activity[:10])
            
        except Exception as e:
            logger.error(f"Error loading system health: {e}")
            flash('Unable to load system health', 'error')
            return redirect(url_for('admin_dashboard'))