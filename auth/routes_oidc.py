from flask import Blueprint, redirect, url_for, session, request, flash, current_app
from flask_login import login_user, logout_user
from auth.oidc import oauth
from auth.oauth import UserManager
import logging

logger = logging.getLogger(__name__)

oidc_bp = Blueprint('oidc', __name__, url_prefix='/auth')

@oidc_bp.route('/login')
def login():
    """Initiate OIDC login flow"""
    try:
        if not hasattr(oauth, 'oidc'):
            flash('OIDC authentication not configured', 'danger')
            return redirect(url_for('auth.login'))
        
        # Store the next URL for post-login redirect
        if 'next' in request.args:
            session['oauth_next_url'] = request.args.get('next')
        
        redirect_uri = current_app.config.get('OIDC_REDIRECT_URI') or url_for('oidc.callback', _external=True)
        return oauth.oidc.authorize_redirect(redirect_uri=redirect_uri)
        
    except Exception as e:
        logger.error(f"OIDC login failed: {e}")
        flash('Authentication service temporarily unavailable', 'danger')
        return redirect(url_for('auth.login'))

@oidc_bp.route('/callback')
def callback():
    """Handle OIDC callback and user authentication"""
    try:
        if not hasattr(oauth, 'oidc'):
            flash('OIDC authentication not configured', 'danger')
            return redirect(url_for('auth.login'))
        
        # Get the token and parse user info
        token = oauth.oidc.authorize_access_token()
        userinfo = oauth.oidc.parse_id_token(token)
        
        if not userinfo or not userinfo.get('email'):
            flash('Authentication failed: Email not provided by provider', 'danger')
            return redirect(url_for('auth.login'))
        
        # Create or update user using existing UserManager
        user = UserManager.create_or_update_user(userinfo, 'oidc')
        
        # Store user_id in session and log the user in using Flask-Login
        session['user_id'] = user.id
        login_user(user, remember=True)
        
        # Redirect to intended destination
        next_url = session.pop('oauth_next_url', None)
        if next_url and next_url.startswith('/'):
            return redirect(next_url)
        
        flash('Successfully logged in via Enterprise SSO', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        logger.error(f"OIDC callback failed: {e}")
        flash('Authentication failed. Please try again.', 'danger')
        return redirect(url_for('auth.login'))

@oidc_bp.route('/logout')
def logout():
    """Handle OIDC logout"""
    try:
        # Log out from Flask-Login
        logout_user()
        session.clear()
        
        # Optional: redirect to provider logout if configured
        provider_logout_url = current_app.config.get('OIDC_LOGOUT_URL')
        if provider_logout_url:
            return redirect(provider_logout_url)
        
        flash('Successfully logged out', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        logger.error(f"OIDC logout failed: {e}")
        flash('Logout completed', 'info')
        return redirect(url_for('index'))