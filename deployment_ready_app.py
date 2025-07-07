from flask import Flask, request, session, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from sqlalchemy.orm import DeclarativeBase
from config import Config
import os
import logging
import json
import secrets
import uuid
from datetime import datetime
from sqlalchemy import text

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from prometheus_flask_exporter import PrometheusMetrics
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize Flask extensions
db = SQLAlchemy(model_class=Base)
migrate = Migrate()
login_manager = LoginManager()

def generate_csrf_token():
    """Generate a CSRF token for forms"""
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(16)
    return session['_csrf_token']

# Initialize Sentry error tracking
sentry_dsn = os.getenv('SENTRY_DSN')
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[FlaskIntegration()],
        traces_sample_rate=0.2,  # capture 20% of transactions
        send_default_pii=True
    )
    logging.info("✓ Sentry error tracking initialized")
else:
    logging.warning("⚠️ SENTRY_DSN not found - error tracking disabled")

# Add JSON filter for Jinja2 templates
def from_json(value):
    try:
        return json.loads(value) if value else []
    except (json.JSONDecodeError, TypeError):
        return [value] if value else []

def to_json_filter(value):
    """Convert Python object to JSON string for JavaScript"""
    try:
        return json.dumps(value, default=str, ensure_ascii=False)
    except (TypeError, ValueError):
        return json.dumps([])

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    login_manager.session_protection = None  # Disable session protection for debugging
    
    # Initialize Prometheus metrics
    metrics = PrometheusMetrics(app, group_by='endpoint')
    # Custom metrics for API monitoring
    request_counter = metrics.counter(
        'api_requests_total', 'Total API Requests', 
        labels={'method': lambda: request.method}
    )
    logging.info("✓ Prometheus metrics initialized at /metrics")
    
    # Configure upload folder for bulk data import
    app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size
    
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Add custom Jinja2 filters
    app.jinja_env.filters['from_json'] = from_json
    app.jinja_env.filters['tojsonfilter'] = to_json_filter
    
    # Register currency formatting as global template function
    def format_currency_filter(value, currency_code=None, include_symbol=True):
        """Format a value as currency using organization preferences"""
        from utils.currency import format_currency
        return format_currency(value, currency_code, include_symbol)
    
    # Register organization-aware date formatting filters
    def format_org_date_filter(value, format_override=None):
        """Format a date using organization preferences"""
        from utils.date import format_org_date
        return format_org_date(value, format_override)
    
    def format_org_datetime_filter(value, format_override=None, include_time=True):
        """Format a datetime using organization preferences with timezone support"""
        from utils.date import format_org_datetime
        return format_org_datetime(value, format_override, include_time)
    
    # Add filters to Jinja2 environment
    app.jinja_env.filters['format_currency'] = format_currency_filter
    app.jinja_env.filters['format_org_date'] = format_org_date_filter
    app.jinja_env.filters['format_org_datetime'] = format_org_datetime_filter
    
    # Global template function to get currency symbol
    def get_currency_symbol():
        """Global template function to get currency symbol"""
        from utils.currency import get_currency_symbol as get_symbol
        return get_symbol()
    
    app.jinja_env.globals['get_currency_symbol'] = get_currency_symbol
    
    # Inject organization preferences into all templates
    @app.context_processor
    def inject_org_preferences():
        """Inject organization preferences into all templates"""
        from models import OrganizationSettings
        
        org_settings = OrganizationSettings.get_organization_settings()
        
        class OrgSettings:
            def __init__(self, currency, date_format, timezone, theme):
                self.currency = currency
                self.date_format = date_format
                self.timezone = timezone
                self.theme = theme
            
            def get_currency_symbol(self):
                from utils.currency import get_currency_symbol
                return get_currency_symbol()
        
        # Get user theme preference or fall back to organization default
        user_theme = None
        if current_user.is_authenticated and hasattr(current_user, 'theme'):
            user_theme = current_user.theme
        
        final_theme = user_theme if user_theme else org_settings.theme
        
        logging.debug(f"🔧 Context Processor Debug:")
        logging.debug(f"   User Theme: {user_theme}")
        logging.debug(f"   Org Theme: {org_settings.theme}")
        logging.debug(f"   Final Theme: {final_theme}")
        
        result = {
            'org_settings': OrgSettings(
                org_settings.currency,
                org_settings.date_format,
                org_settings.timezone,
                final_theme
            ),
            'currency': org_settings.currency,
            'theme': final_theme
        }
        
        logging.debug(f"🔧 Context Processor Debug: Returning currency={org_settings.currency}, theme={final_theme}")
        return result
    
    # Inject pending review counts for navigation badges
    @app.context_processor
    def inject_pending_counts():
        """Inject pending review counts for navigation badges"""
        if not current_user.is_authenticated:
            return {
                'pending_epics': 0,
                'pending_cases': 0, 
                'pending_projects': 0,
                'total_pending': 0
            }
        
        from models import Epic, BusinessCase, Project
        from sqlalchemy import and_
        
        try:
            logging.debug(f"🔧 Badge Debug: User {current_user.email} role: {current_user.role}")
            
            # Get pending counts based on user role
            pending_epics = 0
            pending_cases = 0
            pending_projects = 0
            
            if current_user.role.name in ['Director', 'CEO', 'Admin']:
                # Directors, CEOs, and Admins see all pending items
                pending_epics = Epic.query.filter_by(status='Pending Review').count()
                pending_cases = BusinessCase.query.filter_by(status='Pending Review').count()
                pending_projects = Project.query.filter_by(status='Pending Review').count()
            
            total_pending = pending_epics + pending_cases + pending_projects
            
            logging.debug(f"🔧 Badge Debug: Counts - Epics: {pending_epics}, Cases: {pending_cases}, Projects: {pending_projects}")
            
            result = {
                'pending_epics': pending_epics,
                'pending_cases': pending_cases,
                'pending_projects': pending_projects,
                'total_pending': total_pending
            }
            
            logging.debug(f"🔧 Badge Debug: Returning context: {result}")
            return result
            
        except Exception as e:
            logging.error(f"Error getting pending counts: {e}")
            return {
                'pending_epics': 0,
                'pending_cases': 0,
                'pending_projects': 0,
                'total_pending': 0
            }
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        try:
            user = User.query.get(int(user_id))
            if user:
                logging.debug(f"🔧 User Loader Debug: Successfully loaded user {user.email} (ID: {user_id})")
            else:
                logging.debug(f"🔧 User Loader Debug: No user found with ID: {user_id}")
            return user
        except Exception as e:
            logging.error(f"🔧 User Loader Error: {e}")
            return None
    
    # Health check route
    @app.route('/health')
    def health():
        """Health check endpoint for monitoring systems"""
        return {'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}
    
    # Test route for triggering errors (Sentry validation)
    @app.route('/trigger-error')
    def trigger_error():
        """Test route to trigger an error for Sentry validation"""
        if app.config['DEBUG']:
            raise Exception("Test error for monitoring validation")
        return "Error triggering disabled in production", 404
    
    # Debug session state before each request
    @app.before_request
    def before_request():
        """Debug session and authentication state before each request"""
        if request.endpoint and request.endpoint not in ['static', 'health', 'trigger_error']:
            logging.debug(f"🔧 Session Debug: {dict(session)}")
            if current_user.is_authenticated:
                logging.debug(f"🔧 Auth Debug: Authenticated=True")
                logging.debug(f"🔧 Auth Debug: User={current_user.email}, Role={current_user.role}")
            else:
                logging.debug(f"🔧 Auth Debug: Authenticated=False")
    
    # Inject authentication state into templates
    @app.context_processor
    def inject_auth():
        """Inject authentication state into templates"""
        return dict(current_user=current_user)
    
    # Register blueprints with error handling
    try:
        from auth.routes import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')
        logging.info("✓ Auth blueprint registered")
    except ImportError as e:
        logging.warning(f"⚠️ Auth blueprint not found: {e}")
    
    try:
        from dept.routes import dept_bp
        app.register_blueprint(dept_bp, url_prefix='/dept')
        logging.info("✓ Department blueprint registered")
    except ImportError as e:
        logging.warning(f"⚠️ Department blueprint not found: {e}")
    
    try:
        from problems.routes import problems_bp
        app.register_blueprint(problems_bp, url_prefix='/problems')
        logging.info("✓ Problems blueprint registered")
    except ImportError as e:
        logging.warning(f"⚠️ Problems blueprint not found: {e}")
    
    try:
        from business.routes import business_bp
        app.register_blueprint(business_bp, url_prefix='/business')
        logging.info("✓ Business blueprint registered")
    except ImportError as e:
        logging.warning(f"⚠️ Business blueprint not found: {e}")
    
    try:
        from projects.routes import projects_bp
        app.register_blueprint(projects_bp, url_prefix='/projects')
        logging.info("✓ Projects blueprint registered")
    except ImportError as e:
        logging.warning(f"⚠️ Projects blueprint not found: {e}")
    
    try:
        from solutions.routes import solutions_bp
        app.register_blueprint(solutions_bp, url_prefix='/solutions')
        logging.info("✓ Solutions blueprint registered")
    except ImportError as e:
        logging.warning(f"⚠️ Solutions blueprint not found: {e}")
    
    try:
        from notifications.routes import notifications_bp
        app.register_blueprint(notifications_bp, url_prefix='/notifications')
        logging.info("✓ Notifications blueprint registered")
    except ImportError as e:
        logging.warning(f"⚠️ Notifications blueprint not found: {e}")
    
    try:
        from search.routes import search_bp
        app.register_blueprint(search_bp, url_prefix='/search')
        logging.info("✓ Search blueprint registered")
    except ImportError as e:
        logging.warning(f"⚠️ Search blueprint not found: {e}")
    
    try:
        from reports.routes import reports_bp
        app.register_blueprint(reports_bp, url_prefix='/reports')
        logging.info("✓ Reports blueprint registered")
    except ImportError as e:
        logging.warning(f"⚠️ Reports blueprint not found: {e}")
    
    try:
        from help.routes import help_bp
        app.register_blueprint(help_bp, url_prefix='/help')
        logging.info("✓ Help blueprint registered")
    except ImportError as e:
        logging.warning(f"⚠️ Help blueprint not found: {e}")
    
    try:
        from public.routes import public_bp
        app.register_blueprint(public_bp, url_prefix='/public')
        logging.info("✓ Public blueprint registered")
    except ImportError as e:
        logging.warning(f"⚠️ Public blueprint not found: {e}")
    
    try:
        from ai.routes import ai_bp
        app.register_blueprint(ai_bp, url_prefix='/ai')
        logging.info("✓ AI blueprint registered")
    except ImportError as e:
        logging.warning(f"⚠️ AI blueprint not found: {e}")
    
    try:
        from predict.routes import predict_bp
        app.register_blueprint(predict_bp, url_prefix='/predict')
        logging.info("✓ Predict blueprint registered")
    except ImportError as e:
        logging.warning(f"⚠️ Predict blueprint not found: {e}")
    
    try:
        from settings.routes import settings_bp
        app.register_blueprint(settings_bp, url_prefix='/settings')
        logging.info("✓ Settings blueprint registered")
    except ImportError as e:
        logging.warning(f"⚠️ Settings blueprint not found: {e}")
    
    try:
        from waitlist.routes import waitlist_bp
        app.register_blueprint(waitlist_bp, url_prefix='/waitlist')
        logging.info("✓ Waitlist blueprint registered")
    except ImportError as e:
        logging.warning(f"⚠️ Waitlist blueprint not found: {e}")
    
    try:
        from workflows.routes import workflows_bp
        app.register_blueprint(workflows_bp, url_prefix='/workflows')
        logging.info("✓ Workflows blueprint registered")
    except ImportError as e:
        logging.warning(f"⚠️ Workflows blueprint not found: {e}")
    
    try:
        from monitoring.routes import monitoring_bp
        app.register_blueprint(monitoring_bp, url_prefix='/monitoring')
        logging.info("✓ Monitoring blueprint registered")
    except ImportError as e:
        logging.warning(f"⚠️ Monitoring blueprint not found: {e}")
    
    try:
        from analytics.routes import analytics_bp
        app.register_blueprint(analytics_bp, url_prefix='/analytics')
        logging.info("✓ Analytics blueprint registered")
    except ImportError as e:
        logging.warning(f"⚠️ Analytics blueprint not found: {e}")
    
    try:
        from review.routes import review_bp
        app.register_blueprint(review_bp, url_prefix='/review')
        logging.info("✓ Review blueprint registered")
    except ImportError as e:
        logging.warning(f"⚠️ Review blueprint not found: {e}")
    
    try:
        from dashboard.routes import dashboard_bp
        app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
        logging.info("✓ Dashboard blueprint registered")
    except ImportError as e:
        logging.warning(f"⚠️ Dashboard blueprint not found: {e}")
    
    # Import and initialize admin routes with the app instance
    try:
        from admin_working import init_admin_routes
        init_admin_routes(app)
        logging.info("✓ Admin routes initialized")
    except ImportError as e:
        logging.warning(f"⚠️ Admin routes not found: {e}")
    
    # Setup scheduled workflows
    try:
        from workflows.integration import setup_scheduled_workflows
        setup_scheduled_workflows(app)
        logging.info("✓ Scheduled workflows initialized")
    except ImportError as e:
        logging.warning(f"⚠️ Workflow integration not found: {e}")
    
    # Create database tables
    with app.app_context():
        try:
            from models import *  # Import all models
            db.create_all()
            logging.info("✓ Database tables created")
        except Exception as e:
            logging.error(f"❌ Database initialization failed: {e}")
    
    return app

# Create the application instance
app = create_app()

# Application routes
@app.route('/')
def index():
    """Main application landing page"""
    from flask import render_template, redirect, url_for
    from flask_login import current_user
    
    # If user is authenticated, redirect to appropriate dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.personal_dashboard'))
    
    # Show landing page for unauthenticated users
    return render_template('index.html')

@app.route('/debug/session')
def debug_session():
    """Debug route to check session state"""
    from flask import jsonify
    if app.config['DEBUG']:
        return jsonify({
            'session': dict(session),
            'authenticated': current_user.is_authenticated,
            'user_id': current_user.get_id() if current_user.is_authenticated else None
        })
    return "Debug disabled", 404

@app.route('/sync-logs/<int:epic_id>')
def sync_logs(epic_id):
    """Development helper to synchronize epic sync logs"""
    from flask import jsonify, redirect, url_for
    if app.config['DEBUG']:
        try:
            from models import Epic, EpicSyncLog
            epic = Epic.query.get_or_404(epic_id)
            
            # Create sync log entry
            sync_log = EpicSyncLog(
                epic_id=epic.id,
                action='manual_sync',
                status='completed',
                details='Manual sync triggered from debug route'
            )
            db.session.add(sync_log)
            epic.last_synced = datetime.utcnow()
            db.session.commit()
            
            return redirect(url_for('business.view_case', id=epic.business_case_id))
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return "Debug disabled", 404

@app.route('/unsync-epic/<int:epic_id>')
def unsync_epic(epic_id):
    """Remove epic sync status (development helper)"""
    from flask import redirect, url_for, flash
    if app.config['DEBUG']:
        try:
            from models import Epic
            epic = Epic.query.get_or_404(epic_id)
            epic.last_synced = None
            db.session.commit()
            flash('Epic sync status removed', 'info')
            return redirect(url_for('business.view_case', id=epic.business_case_id))
        except Exception as e:
            flash(f'Error removing sync status: {e}', 'error')
            return redirect(url_for('business.view_case', id=epic.business_case_id))
    return "Debug disabled", 404

@app.route('/dropdown-demo')
def dropdown_demo():
    """Demonstration of reusable dropdown macros"""
    from flask import render_template
    return render_template('dropdown_demo.html')

@app.route('/thank-you')
def thank_you():
    """Thank you page after waitlist signup"""
    from flask import render_template
    return render_template('thank_you.html')

@app.route('/logout-demo')
def logout_demo():
    """Simple logout for demo purposes"""
    from flask import redirect, url_for, flash
    from flask_login import logout_user
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)