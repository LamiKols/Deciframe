"""Stateless authentication using JWT tokens in URLs"""
import jwt
import os
from datetime import datetime, timedelta
from flask import request, redirect, url_for
from models import User

# Use a simple secret for JWT signing
JWT_SECRET = os.environ.get('SESSION_SECRET', 'fallback-secret-key')

def create_auth_token(user_id):
    """Create a JWT token for the user"""
    payload = {
        'user_id': str(user_id),
        'exp': datetime.utcnow() + timedelta(hours=12),  # Extended to 12 hours for testing
        'iat': datetime.utcnow()
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
    print(f"🔧 Created auth token for user {user_id}: {token[:20]}...")
    return token

def verify_auth_token(token):
    """Verify and decode JWT token"""
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        user_id = payload['user_id']
        user = User.query.get(int(user_id))
        if user:
            print(f"🔧 Verified token for user {user_id}: {user.name}")
            return user
        else:
            print(f"🔧 User {user_id} not found in database")
            return None
    except jwt.ExpiredSignatureError:
        print(f"🔧 Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        print(f"🔧 Invalid token: {e}")
        # Clear invalid token from session
        from flask import session
        session.pop('auth_token', None)
        return None
    except ValueError as e:
        print(f"🔧 Token parsing error: {e}")
        return None

def require_auth(f):
    """Decorator to require JWT authentication for API endpoints"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            from flask import jsonify
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Get current user from token in Authorization header, cookie, URL, or form"""
    # Try Authorization header first (Bearer token)
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else None
    
    # Try HttpOnly cookie
    if not token:
        token = request.cookies.get('auth_token')
    
    # Try URL parameter (for backward compatibility)
    if not token:
        token = request.args.get('auth_token')
    
    # Try form data
    if not token and request.method == 'POST':
        token = request.form.get('auth_token')
    
    if token:
        user = verify_auth_token(token)
        if user:
            return user
        else:
            # Token is invalid, clear it from session
            from flask import session
            session.pop('auth_token', None)
    
    print(f"🔧 No auth token found in request")
    return None

def add_auth_token_to_url(endpoint, **values):
    """Add auth token to URL if user is authenticated"""
    user = get_current_user()
    if user:
        token = create_auth_token(user.id)
        values['auth_token'] = token
    return url_for(endpoint, **values)

def redirect_with_auth(endpoint, **values):
    """Redirect while preserving authentication token"""
    return redirect(add_auth_token_to_url(endpoint, **values))