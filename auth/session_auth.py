"""
Session-based authentication helper functions
Replaces JWT-based authentication with Flask-Login session management
"""
from functools import wraps
from flask import session, redirect, url_for, flash
from flask_login import current_user

def require_session_auth(f):
    """
    Decorator to require session-based authentication for routes
    Replaces JWT authentication with Flask-Login session checks
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        
        # Verify user_id exists in session for additional security
        if 'user_id' not in session or session['user_id'] != current_user.id:
            flash('Session expired. Please log in again.', 'warning')
            return redirect(url_for('auth.login'))
            
        return f(*args, **kwargs)
    return decorated_function

def get_current_session_user():
    """
    Get current user from session-based authentication
    Returns current_user if authenticated, None otherwise
    """
    if current_user.is_authenticated and 'user_id' in session:
        return current_user
    return None

def is_session_authenticated():
    """
    Check if user is authenticated via session
    """
    return current_user.is_authenticated and 'user_id' in session

def require_role(*allowed_roles):
    """
    Decorator to require specific user roles
    """
    def decorator(f):
        @wraps(f)
        @require_session_auth
        def decorated_function(*args, **kwargs):
            if current_user.role.value not in allowed_roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator