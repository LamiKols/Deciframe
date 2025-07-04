"""
SSO/OIDC Authentication Module using Authlib
Provides enterprise-grade authentication with multiple provider support
"""

import os
import json
from urllib.parse import urlencode
from flask import current_app, url_for, request, session, redirect, flash
from authlib.integrations.flask_client import OAuth
from authlib.common.errors import AuthlibBaseError
from werkzeug.security import generate_password_hash
from models import User, db
from extensions import login_manager
import logging

logger = logging.getLogger(__name__)

class OAuthConfig:
    """Centralized OAuth configuration management"""
    
    PROVIDERS = {
        'google': {
            'server_metadata_url': 'https://accounts.google.com/.well-known/openid_configuration',
            'client_kwargs': {
                'scope': 'openid email profile'
            }
        },
        'azure': {
            'server_metadata_url': 'https://login.microsoftonline.com/{tenant}/v2.0/.well-known/openid_configuration',
            'client_kwargs': {
                'scope': 'openid email profile'
            }
        },
        'okta': {
            'server_metadata_url': 'https://{domain}/.well-known/openid_configuration',
            'client_kwargs': {
                'scope': 'openid email profile'
            }
        },
        'auth0': {
            'server_metadata_url': 'https://{domain}/.well-known/openid_configuration',
            'client_kwargs': {
                'scope': 'openid email profile'
            }
        },
        'oidc': {
            'server_metadata_url': '{discovery_url}',
            'client_kwargs': {
                'scope': 'openid email profile'
            }
        }
    }
    
    @classmethod
    def get_provider_config(cls, provider_name):
        """Get configuration for specific provider"""
        config = cls.PROVIDERS.get(provider_name, {}).copy()
        
        # Replace placeholders with environment variables
        if provider_name == 'azure':
            tenant = os.getenv('AZURE_TENANT_ID', 'common')
            config['server_metadata_url'] = config['server_metadata_url'].format(tenant=tenant)
        elif provider_name in ['okta', 'auth0']:
            domain = os.getenv(f'{provider_name.upper()}_DOMAIN')
            if domain:
                config['server_metadata_url'] = config['server_metadata_url'].format(domain=domain)
        elif provider_name == 'oidc':
            discovery_url = os.getenv('OIDC_DISCOVERY_URL')
            if discovery_url:
                config['server_metadata_url'] = discovery_url
        
        return config
    
    @classmethod
    def is_provider_enabled(cls, provider_name):
        """Check if provider is properly configured"""
        client_id = os.getenv(f'{provider_name.upper()}_CLIENT_ID')
        client_secret = os.getenv(f'{provider_name.upper()}_CLIENT_SECRET')
        
        if provider_name in ['okta', 'auth0']:
            domain = os.getenv(f'{provider_name.upper()}_DOMAIN')
            return bool(client_id and client_secret and domain)
        elif provider_name == 'oidc':
            discovery_url = os.getenv('OIDC_DISCOVERY_URL')
            return bool(client_id and client_secret and discovery_url)
        elif provider_name == 'azure':
            return bool(client_id and client_secret)
        
        return bool(client_id and client_secret)

class OAuthManager:
    """Manages OAuth providers and authentication flow"""
    
    def __init__(self, app=None):
        self.oauth = OAuth()
        self.providers = {}
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize OAuth with Flask app"""
        self.oauth.init_app(app)
        self._register_providers()
    
    def _register_providers(self):
        """Register all configured OAuth providers"""
        for provider_name in OAuthConfig.PROVIDERS.keys():
            if OAuthConfig.is_provider_enabled(provider_name):
                try:
                    self._register_provider(provider_name)
                    logger.info(f"✓ {provider_name.title()} OAuth provider registered")
                except Exception as e:
                    logger.error(f"Failed to register {provider_name} provider: {e}")
    
    def _register_provider(self, provider_name):
        """Register individual OAuth provider"""
        config = OAuthConfig.get_provider_config(provider_name)
        
        client_id = os.getenv(f'{provider_name.upper()}_CLIENT_ID')
        client_secret = os.getenv(f'{provider_name.upper()}_CLIENT_SECRET')
        
        provider = self.oauth.register(
            name=provider_name,
            client_id=client_id,
            client_secret=client_secret,
            server_metadata_url=config.get('server_metadata_url'),
            client_kwargs=config.get('client_kwargs', {})
        )
        
        self.providers[provider_name] = provider
        return provider
    
    def get_provider(self, provider_name):
        """Get registered OAuth provider"""
        return self.providers.get(provider_name)
    
    def get_enabled_providers(self):
        """Get list of enabled provider names"""
        return list(self.providers.keys())
    
    def authorize_redirect(self, provider_name, redirect_uri=None):
        """Initiate OAuth authorization flow"""
        provider = self.get_provider(provider_name)
        if not provider:
            raise ValueError(f"Provider {provider_name} not configured")
        
        if not redirect_uri:
            redirect_uri = url_for('auth.oauth_callback', provider=provider_name, _external=True)
        
        # Store the next URL in session for post-login redirect
        if 'next' in request.args:
            session['oauth_next_url'] = request.args.get('next')
        
        return provider.authorize_redirect(redirect_uri)
    
    def parse_token(self, provider_name):
        """Parse and validate OAuth token"""
        provider = self.get_provider(provider_name)
        if not provider:
            raise ValueError(f"Provider {provider_name} not configured")
        
        try:
            token = provider.authorize_access_token()
            user_info = provider.parse_id_token(token)
            return token, user_info
        except AuthlibBaseError as e:
            logger.error(f"OAuth token parsing failed for {provider_name}: {e}")
            raise

class UserManager:
    """Manages user creation and authentication from OAuth providers"""
    
    @staticmethod
    def create_or_update_user(user_info, provider_name):
        """Create or update user from OAuth user info"""
        try:
            # Extract user information
            email = user_info.get('email')
            if not email:
                raise ValueError("Email not provided by OAuth provider")
            
            # Look for existing user
            user = User.query.filter_by(email=email).first()
            
            if user:
                # Update existing user
                UserManager._update_user_from_oauth(user, user_info, provider_name)
                logger.info(f"Updated existing user: {email}")
            else:
                # Create new user
                user = UserManager._create_user_from_oauth(user_info, provider_name)
                logger.info(f"Created new user: {email}")
            
            db.session.commit()
            return user
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create/update user: {e}")
            raise
    
    @staticmethod
    def _create_user_from_oauth(user_info, provider_name):
        """Create new user from OAuth information"""
        email = user_info.get('email')
        
        # Extract name information
        name = user_info.get('name', '')
        given_name = user_info.get('given_name', '')
        family_name = user_info.get('family_name', '')
        
        # Generate username from email
        username = email.split('@')[0]
        
        # Ensure username is unique
        base_username = username
        counter = 1
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Create user with default role
        user = User(
            username=username,
            email=email,
            name=name or f"{given_name} {family_name}".strip(),
            first_name=given_name,
            last_name=family_name,
            role='Staff',  # Default role for OAuth users
            is_active=True,
            oauth_provider=provider_name,
            oauth_sub=user_info.get('sub'),
            profile_image_url=user_info.get('picture'),
            password_hash=generate_password_hash('oauth_user_no_password')  # Placeholder
        )
        
        db.session.add(user)
        return user
    
    @staticmethod
    def _update_user_from_oauth(user, user_info, provider_name):
        """Update existing user with OAuth information"""
        # Update profile information if available
        if user_info.get('name'):
            user.name = user_info['name']
        if user_info.get('given_name'):
            user.first_name = user_info['given_name']
        if user_info.get('family_name'):
            user.last_name = user_info['family_name']
        if user_info.get('picture'):
            user.profile_image_url = user_info['picture']
        
        # Update OAuth information
        user.oauth_provider = provider_name
        user.oauth_sub = user_info.get('sub')
        user.last_login = db.func.now()

class OAuthError(Exception):
    """Custom OAuth error class"""
    pass

# Initialize OAuth manager
oauth_manager = OAuthManager()