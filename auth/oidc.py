"""
Clean OIDC Factory Pattern Implementation
"""
from authlib.integrations.flask_client import OAuth
from flask import current_app

oauth = OAuth()

def init_oidc(app):
    """Initialize OIDC client with factory pattern"""
    oauth.init_app(app)
    
    # Register generic OIDC provider if configured
    if (app.config.get('OIDC_CLIENT_ID') and 
        app.config.get('OIDC_CLIENT_SECRET') and 
        app.config.get('OIDC_DISCOVERY_URL')):
        
        oauth.register(
            name='oidc',
            client_id=app.config['OIDC_CLIENT_ID'],
            client_secret=app.config['OIDC_CLIENT_SECRET'],
            server_metadata_url=app.config['OIDC_DISCOVERY_URL'],
            client_kwargs={'scope': 'openid profile email'}
        )
        
        print("✓ Generic OIDC provider registered successfully")
    else:
        print("⚠️ OIDC provider not configured - missing required environment variables")
    
    return oauth

def get_oidc_client():
    """Get the OIDC client instance"""
    return oauth.oidc if hasattr(oauth, 'oidc') else None