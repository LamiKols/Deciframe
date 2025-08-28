"""
Admin permission management and RBAC decorators
"""

from functools import wraps
from flask import flash, redirect, url_for, jsonify, request
from flask_login import current_user
import logging

logger = logging.getLogger(__name__)

# Role constants
class AdminRoles:
    ADMIN = "Admin"
    DIRECTOR = "Director" 
    CEO = "CEO"
    MANAGER = "Manager"
    USER = "User"
    BA = "BA"

# Permission levels
SUPER_ADMIN_ROLES = [AdminRoles.ADMIN, AdminRoles.CEO]
ADMIN_ROLES = [AdminRoles.ADMIN, AdminRoles.DIRECTOR, AdminRoles.CEO]
MANAGER_ROLES = [AdminRoles.ADMIN, AdminRoles.DIRECTOR, AdminRoles.CEO, AdminRoles.MANAGER]


def has_role(user, required_roles):
    """Check if user has any of the required roles"""
    if not user or not user.is_authenticated:
        return False
    
    if isinstance(required_roles, str):
        required_roles = [required_roles]
    
    return user.role.value in required_roles


def require_role(*required_roles):
    """Decorator to require specific roles for route access"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                flash('Please log in to access this page', 'error')
                return redirect(url_for('auth.login'))
            
            if not has_role(current_user, required_roles):
                logger.warning(f"Access denied: User {current_user.email} (role: {current_user.role.value}) "
                             f"attempted to access {request.endpoint} requiring roles: {required_roles}")
                
                if request.is_json:
                    return jsonify({'error': 'Insufficient permissions'}), 403
                flash('Access denied. Insufficient permissions.', 'error')
                return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_admin():
    """Decorator requiring admin-level access"""
    return require_role(*ADMIN_ROLES)


def require_super_admin():
    """Decorator requiring super admin access (Admin/CEO only)"""
    return require_role(*SUPER_ADMIN_ROLES)


def check_organization_access(user, target_org_id):
    """Check if user can access resources from target organization"""
    if not user or not user.is_authenticated:
        return False
    
    # Super admins can access all organizations
    if has_role(user, SUPER_ADMIN_ROLES):
        return True
    
    # Regular users can only access their own organization
    return user.organization_id == target_org_id


def require_organization_access(get_org_id_func=None):
    """Decorator to enforce organization-level access control"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get organization ID from function parameter or custom function
            if get_org_id_func:
                target_org_id = get_org_id_func(*args, **kwargs)
            else:
                # Default: look for org_id in kwargs or use current user's org
                target_org_id = kwargs.get('org_id', current_user.organization_id)
            
            if not check_organization_access(current_user, target_org_id):
                logger.warning(f"Organization access denied: User {current_user.email} "
                             f"attempted to access org {target_org_id}")
                
                if request.is_json:
                    return jsonify({'error': 'Organization access denied'}), 403
                flash('Access denied to organization resources', 'error')
                return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_accessible_organizations(user):
    """Get list of organization IDs the user can access"""
    if not user or not user.is_authenticated:
        return []
    
    # Super admins can access all organizations
    if has_role(user, SUPER_ADMIN_ROLES):
        from models import Organization
        return [org.id for org in Organization.query.all()]
    
    # Regular users can only access their own organization
    return [user.organization_id]


def validate_admin_action(action_type, target_user=None, target_resource=None):
    """Validate if current user can perform admin action"""
    if not current_user.is_authenticated:
        return False, "Authentication required"
    
    if not has_role(current_user, ADMIN_ROLES):
        return False, "Admin privileges required"
    
    # Prevent self-modification for critical actions
    if action_type in ['delete_user', 'change_role'] and target_user:
        if target_user.id == current_user.id:
            return False, "Cannot modify your own account"
    
    # Organization-level restrictions
    if target_user and not check_organization_access(current_user, target_user.organization_id):
        return False, "Cannot modify users from other organizations"
    
    return True, "Action permitted"