import os

class Config:
    DEBUG = True
    SECRET_KEY = os.getenv('SESSION_SECRET', os.getenv('SECRET_KEY', 'change-this-to-a-secure-secret-key-for-production'))
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///deciframe.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {'sslmode': 'prefer'}
    }
    
    # Feature flag for hybrid business cases
    ENABLE_HYBRID_CASES = os.getenv('ENABLE_HYBRID_CASES', 'False') == 'True'
    
    # Progressive elaboration settings
    FULL_CASE_THRESHOLD = float(os.getenv('FULL_CASE_THRESHOLD', '25000'))
    # Session configuration for Flask-Login - simplified for debugging
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = False
    SESSION_COOKIE_SAMESITE = None
    PERMANENT_SESSION_LIFETIME = 43200  # 12 hours in seconds
    
    # AI Service Configuration
    AI_AVAILABLE = bool(os.getenv('OPENAI_API_KEY'))
    ENABLE_AI_REQS = os.getenv('ENABLE_AI_REQS', 'True') == 'True'
    
    # OIDC settings for generic identity providers
    OIDC_CLIENT_ID = os.getenv('OIDC_CLIENT_ID')
    OIDC_CLIENT_SECRET = os.getenv('OIDC_CLIENT_SECRET')
    OIDC_DISCOVERY_URL = os.getenv('OIDC_DISCOVERY_URL')  # e.g. https://accounts.example.com/.well-known/openid-configuration
    OIDC_REDIRECT_URI = os.getenv('OIDC_REDIRECT_URI')   # e.g. https://yourapp.com/auth/callback
    OIDC_LOGOUT_URL = os.getenv('OIDC_LOGOUT_URL')       # optional: provider logout endpoint
    
    # Organization-level preference defaults
    DEFAULT_CURRENCY = os.getenv('DEFAULT_CURRENCY', 'USD')
    DEFAULT_DATE_FORMAT = os.getenv('DEFAULT_DATE_FORMAT', '%Y-%m-%d')
    DEFAULT_TIMEZONE = os.getenv('DEFAULT_TIMEZONE', 'UTC')
    
    @property
    def AI_SERVICE_STATUS(self):
        return "online" if self.AI_AVAILABLE else "offline"
