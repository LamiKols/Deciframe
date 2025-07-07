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
    from utils.currency import format_currency
    app.jinja_env.globals.update(format_currency=format_currency)
    
    # Register date formatting as global template function
    from utils.date import format_date, format_datetime
    app.jinja_env.globals.update(format_date=format_date, format_datetime=format_datetime)
    
    # Custom template filter for currency formatting
    def format_currency_filter(value, currency_code=None, include_symbol=True):
        """Format a value as currency using organization preferences"""
        if not isinstance(value, (int, float)):
            try:
                value = float(value)
            except (ValueError, TypeError):
                return "$0.00"
        
        # Get currency from org preferences if available
        if not currency_code and current_user and current_user.is_authenticated:
            org = getattr(current_user, 'organization', None)
            currency_code = getattr(org, 'currency', 'USD') if org else 'USD'
        
        if not currency_code:
            currency_code = current_app.config.get('DEFAULT_CURRENCY', 'USD')
        
        # Format the number
        formatted = f"{value:,.2f}"
        
        if include_symbol:
            # Currency symbols mapping
            currency_symbols = {
                'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥',
                'CAD': 'C$', 'AUD': 'A$', 'CHF': 'CHF', 'CNY': '¥'
            }
            symbol = currency_symbols.get(currency_code, '$')
            return f"{symbol}{formatted}"
        
        return formatted
    
    # Custom template filter for date formatting using org preferences
    def format_org_date_filter(value, format_override=None):
        """Format a date using organization preferences"""
        if not value:
            return ""
        
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                return value
        
        # Get format from org preferences if available
        if not format_override and current_user and current_user.is_authenticated:
            org = getattr(current_user, 'organization', None)
            date_format = getattr(org, 'date_format', 'ISO') if org else 'ISO'
        else:
            date_format = format_override or current_app.config.get('DEFAULT_DATE_FORMAT', 'ISO')
        
        # Format mapping
        format_mapping = {
            'US': '%m/%d/%Y',      # 12/31/2023
            'EU': '%d/%m/%Y',      # 31/12/2023
            'ISO': '%Y-%m-%d',     # 2023-12-31
            'Long': '%B %d, %Y'    # December 31, 2023
        }
        
        date_format_str = format_mapping.get(date_format, '%Y-%m-%d')
        return value.strftime(date_format_str)
    
    # Custom template filter for datetime formatting using org preferences
    def format_org_datetime_filter(value, format_override=None, include_time=True):
        """Format a datetime using organization preferences with timezone support"""
        if not value:
            return ""
        
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                return value
        
        # Get timezone and format from org preferences if available
        if current_user and current_user.is_authenticated:
            org = getattr(current_user, 'organization', None)
            if org:
                timezone_name = getattr(org, 'timezone', 'UTC')
                date_format = getattr(org, 'date_format', 'ISO')
            else:
                timezone_name = 'UTC'
                date_format = 'ISO'
        else:
            timezone_name = current_app.config.get('DEFAULT_TIMEZONE', 'UTC')
            date_format = current_app.config.get('DEFAULT_DATE_FORMAT', 'ISO')
        
        date_format = format_override or date_format
        
        # Convert timezone if needed
        import pytz
        try:
            if value.tzinfo is None:
                # Assume UTC if no timezone info
                value = pytz.UTC.localize(value)
            
            # Convert to org timezone
            org_tz = pytz.timezone(timezone_name)
            value = value.astimezone(org_tz)
        except:
            # Fallback if timezone conversion fails
            pass
        
        # Format mapping
        format_mapping = {
            'US': '%m/%d/%Y',      # 12/31/2023
            'EU': '%d/%m/%Y',      # 31/12/2023
            'ISO': '%Y-%m-%d',     # 2023-12-31
            'Long': '%B %d, %Y'    # December 31, 2023
        }
        
        date_format_str = format_mapping.get(date_format, '%Y-%m-%d')
        
        if include_time:
            date_format_str += ' %H:%M'
        
        return value.strftime(date_format_str)
    
    # Register filters
    app.jinja_env.filters['format_currency'] = format_currency_filter
    app.jinja_env.filters['format_org_date'] = format_org_date_filter
    app.jinja_env.filters['format_org_datetime'] = format_org_datetime_filter
    
    # Register CSRF token generator as global function
    app.jinja_env.globals.update(csrf_token=generate_csrf_token)
    
    @app.context_processor
    def inject_org_preferences():
        """Inject organization preferences into all templates"""
        
        # Currency symbols mapping for template use
        currency_symbols = {
            'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥',
            'CAD': 'C$', 'AUD': 'A$', 'CHF': 'CHF', 'CNY': '¥'
        }
        
        class OrgSettings:
            def __init__(self, currency, date_format, timezone, theme):
                self.currency = currency
                self.date_format = date_format
                self.timezone = timezone
                self.theme = theme
            
            def get_currency_symbol(self):
                return currency_symbols.get(self.currency, '$')
        
        # Only inject if user is authenticated
        if not current_user.is_authenticated:
            print(f"🔧 Context Processor Debug: User not authenticated, using defaults")
            default_currency = current_app.config.get('DEFAULT_CURRENCY', 'USD')
            default_date_format = current_app.config.get('DEFAULT_DATE_FORMAT', 'ISO')
            default_timezone = current_app.config.get('DEFAULT_TIMEZONE', 'UTC')
            default_theme = 'light'
            
            return {
                'org_prefs': {
                    'currency': default_currency,
                    'date_format': default_date_format,
                    'timezone': default_timezone,
                    'theme': default_theme
                },
                'org_settings': OrgSettings(default_currency, default_date_format, default_timezone, default_theme)
            }
        
        # Get organization from user
        org = getattr(current_user, 'organization', None)
        
        # Use user theme preference first, then organization default, then 'light'
        user_theme = getattr(current_user, 'theme', None)
        org_theme = getattr(org, 'default_theme', 'light') if org else 'light'
        theme = user_theme if user_theme else org_theme
        
        print(f"🔧 Context Processor Debug:")
        print(f"   User Theme: {user_theme}")
        print(f"   Org Theme: {org_theme}")
        print(f"   Final Theme: {theme}")
        
        currency = getattr(org, 'currency', current_app.config.get('DEFAULT_CURRENCY', 'USD'))
        date_format = getattr(org, 'date_format', current_app.config.get('DEFAULT_DATE_FORMAT', 'ISO'))
        timezone = getattr(org, 'timezone', current_app.config.get('DEFAULT_TIMEZONE', 'UTC'))
        
        return {
            'org_prefs': {
                'currency': currency,
                'date_format': date_format,
                'timezone': timezone,
                'theme': theme
            },
            'org_settings': OrgSettings(currency, date_format, timezone, theme)
        }
    
    @app.context_processor
    def inject_pending_counts():
        """Inject pending review counts for navigation badges"""
        
        # Only show counts for users with reviewing roles
        if not current_user.is_authenticated:
            print(f"🔧 Badge Debug: User not authenticated")
            return {}
        
        print(f"🔧 Badge Debug: User {current_user.email} role: {current_user.role}")
        
        if current_user.role.value not in ['Manager', 'Director', 'CEO', 'PM', 'Admin']:
            print(f"🔧 Badge Debug: Role {current_user.role.value} not in reviewing roles")
            return {}
        
        try:
            from models import Epic, BusinessCase, Project, StatusEnum
            
            pending_epics = Epic.query.filter_by(status='Submitted').count()
            pending_cases = BusinessCase.query.filter_by(status='Submitted').count()
            pending_projects = Project.query.filter_by(status='Submitted').count()
            
            print(f"🔧 Badge Debug: Counts - Epics: {pending_epics}, Cases: {pending_cases}, Projects: {pending_projects}")
            
            result = {
                'pending_epics': pending_epics,
                'pending_cases': pending_cases,
                'pending_projects': pending_projects,
                'total_pending': pending_epics + pending_cases + pending_projects
            }
            
            print(f"🔧 Badge Debug: Returning context: {result}")
            return result
        except Exception as e:
            print(f"🔧 Badge Debug: Exception occurred: {e}")
            db.session.rollback()  # Rollback failed transaction
            # Graceful fallback if database query fails
            return {
                'pending_epics': 0,
                'pending_cases': 0,
                'pending_projects': 0,
                'total_pending': 0
            }
    
    # Configure user loader to bridge JWT and session authentication
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        from flask import session
        
        # Always try to load user if user_id is provided
        try:
            user = User.query.get(int(user_id))
            if user:
                print(f"🔧 User Loader Debug: Successfully loaded user {user.email} (ID: {user_id})")
                # Store user_id in session for debugging
                session['user_id'] = user.id
                return user
            else:
                print(f"🔧 User Loader Debug: No user found with ID {user_id}")
                return None
        except Exception as e:
            print(f"🔧 User Loader Debug: Error loading user {user_id}: {e}")
            return None
    
    # Health check endpoint
    @app.route('/health')
    def health():
        """Health check endpoint for monitoring systems"""
        try:
            # Test database connection
            result = db.session.execute(text('SELECT 1')).scalar()
            
            return {
                'status': 'healthy',
                'database': 'connected' if result == 1 else 'disconnected',
                'timestamp': datetime.utcnow().isoformat()
            }, 200
        except Exception as e:
            logging.error(f"Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }, 500
    
    # Error trigger for Sentry testing
    @app.route('/trigger-error')
    def trigger_error():
        """Test route to trigger an error for Sentry validation"""
        division_by_zero = 1 / 0
        return "This should not be reached"
    
    @app.before_request
    def before_request():
        """Debug session and authentication state before each request"""
        from flask_login import current_user
        
        print(f"🔧 Session Debug: {dict(session)}")
        print(f"🔧 Auth Debug: Authenticated={current_user.is_authenticated}")
        if current_user.is_authenticated:
            print(f"🔧 Auth Debug: User={current_user.email}, Role={current_user.role}")
    
    @app.context_processor
    def inject_auth():
        """Inject authentication state into templates"""
        from flask_login import current_user
        return dict(current_user=current_user)
    
    # Create database tables
    with app.app_context():
        import models  # Import models to ensure tables are created
        db.create_all()
    
    # Register all blueprints
    from admin_working import init_admin_routes
    init_admin_routes(app)
    
    # Register the blueprints from blueprint modules
    from auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from problems.routes import problems_bp
    app.register_blueprint(problems_bp, url_prefix='/problems')
    
    from business.routes import business_bp
    app.register_blueprint(business_bp, url_prefix='/business')
    
    from projects.routes import projects_bp
    app.register_blueprint(projects_bp)
    
    from solutions.routes import solutions_bp
    app.register_blueprint(solutions_bp, url_prefix='/solutions')
    
    from dept.routes import dept
    app.register_blueprint(dept, url_prefix='/dept')
    
    from predict.routes import predict_bp
    app.register_blueprint(predict_bp)
    
    from reports.routes import reports_bp
    app.register_blueprint(reports_bp)
    
    from notifications.config_routes import notifications_config_bp
    app.register_blueprint(notifications_config_bp)
    
    from ai.routes import ai_bp
    app.register_blueprint(ai_bp)
    
    # Import blueprints that exist and comment out missing ones
    try:
        from review.routes import review_bp
        app.register_blueprint(review_bp, url_prefix='/review')
    except ImportError as e:
        logging.warning(f"Review blueprint not found: {e}")
    
    try:
        from search.routes import search_bp
        app.register_blueprint(search_bp, url_prefix='/search')
    except ImportError as e:
        logging.warning(f"Search blueprint not found: {e}")
    
    try:
        from help.routes import help_bp
        app.register_blueprint(help_bp, url_prefix='/help')
    except ImportError as e:
        logging.warning(f"Help blueprint not found: {e}")
    
    try:
        from waitlist.routes import waitlist_bp
        app.register_blueprint(waitlist_bp, url_prefix='/waitlist')
    except ImportError as e:
        logging.warning(f"Waitlist blueprint not found: {e}")
    
    try:
        from public import bp as public_bp
        app.register_blueprint(public_bp)
    except ImportError as e:
        logging.warning(f"Public blueprint not found: {e}")
    
    try:
        from dashboards.routes import dash_bp
        app.register_blueprint(dash_bp)
    except ImportError as e:
        logging.warning(f"Dashboards blueprint not found: {e}")
    
    try:
        from monitoring.dashboard import monitoring_bp
        app.register_blueprint(monitoring_bp)
    except ImportError as e:
        logging.warning(f"Monitoring blueprint not found: {e}")
    
    try:
        from settings.routes import settings_bp
        app.register_blueprint(settings_bp, url_prefix='/settings')
    except ImportError as e:
        logging.warning(f"Settings blueprint not found: {e}")
    
    # Note: scheduled doesn't have a routes.py, only send_exec_report.py
    
    # Initialize workflow automation and scheduled tasks
    try:
        from workflows.integration import initialize_workflow_integrations
        initialize_workflow_integrations()
        logging.info("✓ Workflow automation initialized")
    except Exception as e:
        logging.warning(f"⚠️ Workflow automation initialization failed: {e}")
    
    # Initialize machine learning training scheduler
    try:
        from analytics.scheduler import init_ml_scheduler
        init_ml_scheduler()
        logging.info("✓ ML training scheduler initialized")
    except Exception as e:
        logging.warning(f"⚠️ ML training scheduler initialization failed: {e}")
    
    # Initialize automated report scheduler
    try:
        from reports.scheduler import init_report_scheduler
        init_report_scheduler()
        logging.info("✓ Report scheduler initialized")
    except Exception as e:
        logging.warning(f"⚠️ Report scheduler initialization failed: {e}")
    
    # Initialize notifications configuration check
    try:
        from notifications.service import initialize_default_templates
        initialize_default_templates()
        logging.info("✓ Notification templates initialized")
    except Exception as e:
        logging.warning(f"⚠️ Notification templates initialization failed: {e}")
    
    logging.info("✓ Application initialized successfully")
    
    return app

# Create app instance
app = create_app()

# Main route
@app.route('/')
def index():
    """Main application landing page"""
    from flask_login import current_user
    from flask import render_template, redirect, url_for
    
    if current_user.is_authenticated:
        # Redirect authenticated users to their appropriate dashboard
        if current_user.role.value in ['Director', 'CEO', 'Admin']:
            return redirect(url_for('dashboards.executive_dashboard'))
        else:
            return redirect(url_for('dashboard.user_dashboard'))
    else:
        # Show landing page for unauthenticated users
        return render_template('landing.html')

@app.route('/debug-session')
def debug_session():
    """Debug route to check session state"""
    from flask import session
    from flask_login import current_user
    
    return {
        'session': dict(session),
        'user_authenticated': current_user.is_authenticated,
        'user_id': getattr(current_user, 'id', None),
        'user_email': getattr(current_user, 'email', None)
    }

@app.route('/sync-logs/<int:epic_id>')
def sync_logs(epic_id):
    """Development helper to synchronize epic sync logs"""
    from models import Epic, EpicSyncLog
    from datetime import datetime
    
    epic = Epic.query.get_or_404(epic_id)
    
    # Create sync log entry
    sync_log = EpicSyncLog(
        epic_id=epic.id,
        action='manual_sync',
        details=f'Manual sync triggered for epic: {epic.title}',
        timestamp=datetime.utcnow()
    )
    
    db.session.add(sync_log)
    db.session.commit()
    
    from flask import flash, redirect, url_for
    flash('Epic sync log created successfully', 'success')
    return redirect(url_for('business.view_epic', id=epic_id))

@app.route('/unsync-epic/<int:epic_id>')
def unsync_epic(epic_id):
    """Remove epic sync status (development helper)"""
    from models import Epic
    
    epic = Epic.query.get_or_404(epic_id)
    epic.is_synced = False
    db.session.commit()
    
    from flask import flash, redirect, url_for
    flash('Epic sync status removed', 'info')
    return redirect(url_for('business.view_epic', id=epic_id))

@app.route('/dropdown-demo')
def dropdown_demo():
    """Demonstration of reusable dropdown macros"""
    from flask import render_template
    return render_template('demo/dropdown_demo.html')

@app.route('/thank-you')
def thank_you():
    """Thank you page after waitlist signup"""
    from flask import render_template
    return render_template('waitlist/thank_you.html')

@app.route('/logout-demo')
def logout_demo():
    """Simple logout for demo purposes"""
    from flask_login import logout_user
    from flask import redirect, url_for, flash
    
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)