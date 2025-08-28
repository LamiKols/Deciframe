"""
Feature flags system for canary deployments and A/B testing
"""
import os
import logging
from functools import wraps
from flask import g, request
from flask_login import current_user


logger = logging.getLogger(__name__)


def is_enabled(flag_name, user=None, default=False):
    """
    Check if a feature flag is enabled
    
    Args:
        flag_name: Name of the feature flag (e.g. 'NEW_DASHBOARD_UI')
        user: Optional user object for user-specific flags
        default: Default value if flag is not set
        
    Returns:
        bool: True if feature is enabled
    """
    
    # Check environment variable first
    env_flag = os.getenv(flag_name, '').lower()
    if env_flag in ['true', '1', 'yes', 'on']:
        return True
    elif env_flag in ['false', '0', 'no', 'off']:
        return False
    
    # Check user-specific flags (if user provided)
    if user and hasattr(user, 'id'):
        user_flag = os.getenv(f"{flag_name}_USER_{user.id}", '').lower()
        if user_flag in ['true', '1']:
            return True
        elif user_flag in ['false', '0']:
            return False
    
    # Check organization-specific flags
    if user and hasattr(user, 'organization_id'):
        org_flag = os.getenv(f"{flag_name}_ORG_{user.organization_id}", '').lower()
        if org_flag in ['true', '1']:
            return True
        elif org_flag in ['false', '0']:
            return False
    
    # Check percentage rollout
    percentage_flag = os.getenv(f"{flag_name}_PERCENTAGE", '').strip()
    if percentage_flag.isdigit():
        percentage = int(percentage_flag)
        if 0 <= percentage <= 100:
            # Use user ID for consistent rollout if available
            if user and hasattr(user, 'id'):
                user_hash = hash(f"{flag_name}:{user.id}") % 100
                return user_hash < percentage
            else:
                # Use IP address as fallback
                ip_hash = hash(f"{flag_name}:{request.remote_addr}") % 100
                return ip_hash < percentage
    
    return default


def require_flag(flag_name, default=False, redirect_url=None):
    """
    Decorator to require a feature flag to be enabled
    
    Args:
        flag_name: Name of the feature flag
        default: Default value if flag is not set
        redirect_url: URL to redirect to if flag is disabled
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = current_user if hasattr(current_user, 'id') and current_user.is_authenticated else None
            
            if not is_enabled(flag_name, user, default):
                if redirect_url:
                    from flask import redirect
                    return redirect(redirect_url)
                else:
                    from flask import jsonify
                    return jsonify({'error': 'Feature not available'}), 404
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def flag_context():
    """Add feature flag context to templates"""
    user = current_user if hasattr(current_user, 'id') and current_user.is_authenticated else None
    
    # Common feature flags that templates might need
    common_flags = [
        'NEW_DASHBOARD_UI',
        'ADVANCED_ANALYTICS',
        'BETA_FEATURES',
        'DARK_MODE_TOGGLE',
        'EXPERIMENTAL_CHARTS',
    ]
    
    flags = {}
    for flag in common_flags:
        flags[flag.lower()] = is_enabled(flag, user)
    
    return {'feature_flags': flags}


def log_flag_usage(flag_name, enabled, user=None):
    """Log feature flag usage for analytics"""
    context = {
        'flag_name': flag_name,
        'enabled': enabled,
        'user_id': user.id if user and hasattr(user, 'id') else None,
        'organization_id': user.organization_id if user and hasattr(user, 'organization_id') else None,
        'ip_address': request.remote_addr if request else None,
    }
    
    logger.info(f"Feature flag usage: {flag_name}", extra=context)


def setup_feature_flags(app):
    """Setup feature flags system with Flask app"""
    
    # Add template context processor for flags
    app.context_processor(flag_context)
    
    # Log feature flag usage on requests
    @app.before_request
    def log_active_flags():
        if hasattr(g, 'feature_flags_logged'):
            return  # Already logged for this request
        
        g.feature_flags_logged = True
        user = current_user if hasattr(current_user, 'id') and current_user.is_authenticated else None
        
        # Check and log commonly used flags
        important_flags = ['NEW_DASHBOARD_UI', 'BETA_FEATURES', 'EXPERIMENTAL_CHARTS']
        
        for flag in important_flags:
            if os.getenv(flag):  # Only log if flag is explicitly set
                enabled = is_enabled(flag, user)
                log_flag_usage(flag, enabled, user)
    
    return app


# Predefined feature flags for the application
class FeatureFlags:
    """Predefined feature flags with descriptions"""
    
    # UI/UX Features
    NEW_DASHBOARD_UI = "NEW_DASHBOARD_UI"  # New dashboard redesign
    DARK_MODE_TOGGLE = "DARK_MODE_TOGGLE"  # Dark mode toggle in UI
    ADVANCED_SEARCH = "ADVANCED_SEARCH"    # Advanced search functionality
    
    # Analytics Features  
    ADVANCED_ANALYTICS = "ADVANCED_ANALYTICS"  # Advanced analytics dashboard
    EXPERIMENTAL_CHARTS = "EXPERIMENTAL_CHARTS"  # New chart types
    REALTIME_METRICS = "REALTIME_METRICS"  # Real-time metrics updates
    
    # Admin Features
    ENHANCED_ADMIN = "ENHANCED_ADMIN"      # Enhanced admin interface
    BULK_OPERATIONS = "BULK_OPERATIONS"   # Bulk edit operations
    ADVANCED_AUDIT = "ADVANCED_AUDIT"     # Advanced audit trail features
    
    # Performance Features
    LAZY_LOADING = "LAZY_LOADING"         # Lazy loading for large datasets
    CACHING_V2 = "CACHING_V2"             # Improved caching system
    ASYNC_PROCESSING = "ASYNC_PROCESSING"  # Async background processing
    
    # Beta Features
    BETA_FEATURES = "BETA_FEATURES"       # General beta features toggle
    AI_INSIGHTS = "AI_INSIGHTS"           # AI-powered insights
    PREDICTIVE_ANALYTICS = "PREDICTIVE_ANALYTICS"  # Predictive analytics


# Helper functions for common flag checks
def is_beta_enabled(user=None):
    """Check if beta features are enabled for user"""
    return is_enabled(FeatureFlags.BETA_FEATURES, user, default=False)


def is_admin_enhanced(user=None):
    """Check if enhanced admin features are enabled"""
    return is_enabled(FeatureFlags.ENHANCED_ADMIN, user, default=True)


def is_dark_mode_available(user=None):
    """Check if dark mode toggle is available"""
    return is_enabled(FeatureFlags.DARK_MODE_TOGGLE, user, default=True)