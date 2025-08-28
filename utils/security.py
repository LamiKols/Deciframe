
# 🔒 MULTI-TENANT SECURITY DECORATOR
from functools import wraps
from flask import abort
from flask_login import current_user

def require_same_org(get_record_func=None):
    """
    Decorator to enforce organization-level access control
    Usage:
        @require_same_org(lambda id: Problem.query.get_or_404(id))
        def view_problem(id):
            # This will automatically check org access
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            # Extract record ID from kwargs or args
            record_id = kwargs.get('id') or (args[0] if args else None)
            
            if get_record_func and record_id:
                try:
                    record = get_record_func(record_id)
                    if hasattr(record, 'organization_id'):
                        if record.organization_id != current_user.organization_id:
                            abort(403, "Access denied: Resource belongs to different organization")
                except Exception:
                    abort(404)
            
            return f(*args, **kwargs)
        return wrapped
    return decorator

def enforce_org_filter(query_class):
    """
    Helper to automatically add organization filtering to queries
    Usage: Problem.query becomes enforce_org_filter(Problem).query
    """
    if hasattr(current_user, 'organization_id') and current_user.is_authenticated:
        return query_class.query.filter_by(organization_id=current_user.organization_id)
    return query_class.query
