"""
Rate limiting and security headers implementation
"""
import os
import time
from collections import defaultdict, deque
from functools import wraps
from flask import request, jsonify, current_app
from flask_login import current_user


# In-memory rate limit storage - use Redis in production
rate_limit_storage = defaultdict(lambda: deque())


class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize rate limiter with Flask app"""
        self.app = app
        app.extensions = getattr(app, 'extensions', {})
        app.extensions['rate_limiter'] = self
    
    def limit(self, rate_limit, per_user=True, per_ip=True):
        """
        Rate limiting decorator
        
        Args:
            rate_limit: String like "10/min" or "100/hour" 
            per_user: Apply limit per authenticated user
            per_ip: Apply limit per IP address
        """
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if not self._is_rate_limited(rate_limit, per_user, per_ip):
                    return f(*args, **kwargs)
                else:
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'message': f'Request rate limit of {rate_limit} exceeded'
                    }), 429
            
            return decorated_function
        return decorator
    
    def _is_rate_limited(self, rate_limit, per_user, per_ip):
        """Check if request should be rate limited"""
        
        # Parse rate limit (e.g., "10/min" -> 10 requests per 60 seconds)
        try:
            count, period = rate_limit.split('/')
            count = int(count)
            
            if period == 'min':
                window_seconds = 60
            elif period == 'hour':
                window_seconds = 3600
            elif period == 'day':
                window_seconds = 86400
            else:
                window_seconds = int(period)  # Assume seconds
        except ValueError:
            current_app.logger.error(f"Invalid rate limit format: {rate_limit}")
            return False
        
        current_time = time.time()
        
        # Generate keys for rate limiting
        keys = []
        
        if per_ip:
            keys.append(f"ip:{request.remote_addr}")
        
        if per_user and hasattr(current_user, 'id') and current_user.is_authenticated:
            keys.append(f"user:{current_user.id}")
        
        if not keys:
            keys.append(f"ip:{request.remote_addr}")  # Fallback to IP
        
        # Check rate limits for each key
        for key in keys:
            request_times = rate_limit_storage[key]
            
            # Remove old requests outside the time window
            while request_times and request_times[0] < current_time - window_seconds:
                request_times.popleft()
            
            # Check if we're over the limit
            if len(request_times) >= count:
                return True
            
            # Add current request
            request_times.append(current_time)
        
        return False


def setup_security_headers(app):
    """Setup security headers for all responses"""
    
    enable_headers = os.getenv('ENABLE_SECURITY_HEADERS', '1') == '1'
    
    if not enable_headers:
        return app
    
    @app.after_request
    def add_security_headers(response):
        """Add security headers to all responses"""
        
        # HSTS (only if HTTPS)
        if request.is_secure:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Frame options
        response.headers['X-Frame-Options'] = 'DENY'
        
        # Content type options
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Referrer policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content Security Policy
        csp_policy = (
            "default-src 'self' https: data:; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "connect-src 'self'; "
            "frame-src 'none';"
        )
        response.headers['Content-Security-Policy'] = csp_policy
        
        # Additional security headers
        response.headers['X-Permitted-Cross-Domain-Policies'] = 'none'
        response.headers['Cross-Origin-Embedder-Policy'] = 'require-corp'
        response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
        response.headers['Cross-Origin-Resource-Policy'] = 'same-site'
        
        return response
    
    return app


def setup_rate_limiting(app):
    """Setup rate limiting for the application"""
    
    limiter = RateLimiter(app)
    
    # Apply rate limiting to authentication endpoints
    from auth import bp as auth_bp
    
    # Wrap login route with rate limiting
    if hasattr(auth_bp, 'view_functions'):
        login_view = auth_bp.view_functions.get('login')
        if login_view:
            auth_bp.view_functions['login'] = limiter.limit("10/min")(login_view)
    
    # Apply rate limiting to admin endpoints
    @app.before_request
    def apply_admin_rate_limits():
        """Apply rate limits to admin endpoints"""
        if (request.endpoint and request.endpoint.startswith('admin') and 
            request.method in ['POST', 'PUT', 'PATCH', 'DELETE']):
            
            if limiter._is_rate_limited("30/min", per_user=True, per_ip=True):
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': 'Admin operation rate limit exceeded'
                }), 429
    
    return app


def require_api_key(f):
    """Decorator to require API key for certain endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        expected_key = os.getenv('API_KEY')
        
        if not expected_key:
            # No API key configured, skip check
            return f(*args, **kwargs)
        
        if not api_key or api_key != expected_key:
            return jsonify({
                'error': 'Invalid or missing API key',
                'message': 'Valid API key required for this endpoint'
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated_function