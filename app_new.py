from flask import Flask, request, session
from config import Config
import os
import logging
import json
import secrets
import uuid
from datetime import datetime
from sqlalchemy import text
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# Import shared extensions to avoid circular imports
from app import db, login_manager
migrate = Migrate()

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from prometheus_flask_exporter import PrometheusMetrics
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

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
    
    # Register preference-based formatting functions
    from utils.preferences import (
        get_org_preferences, get_user_preferences, get_currency_symbol,
        format_currency_value, format_date_value, format_datetime_value
    )
    app.jinja_env.globals.update(
        get_org_preferences=get_org_preferences,
        get_user_preferences=get_user_preferences,
        get_currency_symbol=get_currency_symbol
    )
    
    # Enhanced preference-aware template filters using org_prefs
    @app.template_filter('format_currency')
    def format_currency_filter(value, currency_code=None, include_symbol=True):
        """Format a value as currency using organization preferences"""
        from flask_login import current_user
        from flask import current_app
        
        if not currency_code:
            # Get currency from org_prefs context or fallback
            if current_user.is_authenticated:
                org = getattr(current_user, 'organization', None)
                currency_code = getattr(org, 'currency', current_app.config.get('DEFAULT_CURRENCY', 'USD'))
            else:
                currency_code = current_app.config.get('DEFAULT_CURRENCY', 'USD')
        
        try:
            return format_currency_value(float(value), currency_code, include_symbol)
        except (ValueError, TypeError):
            return value
    
    @app.template_filter('format_org_date')
    def format_org_date_filter(value, format_override=None):
        """Format a date using organization preferences"""
        from flask_login import current_user
        from flask import current_app
        
        if not value:
            return ""
        
        if current_user.is_authenticated:
            org = getattr(current_user, 'organization', None)
            date_format = getattr(org, 'date_format', current_app.config.get('DEFAULT_DATE_FORMAT', '%Y-%m-%d'))
        else:
            date_format = current_app.config.get('DEFAULT_DATE_FORMAT', '%Y-%m-%d')
        
        try:
            return format_date_value(value, format_override or date_format)
        except (ValueError, TypeError):
            return str(value)
    
    @app.template_filter('format_org_datetime')
    def format_org_datetime_filter(value, format_override=None, include_time=True):
        """Format a datetime using organization preferences with timezone support"""
        from flask_login import current_user
        from flask import current_app
        
        if not value:
            return ""
        
        if current_user.is_authenticated:
            org = getattr(current_user, 'organization', None)
            date_format = getattr(org, 'date_format', current_app.config.get('DEFAULT_DATE_FORMAT', '%Y-%m-%d'))
            timezone = getattr(org, 'timezone', current_app.config.get('DEFAULT_TIMEZONE', 'UTC'))
        else:
            date_format = current_app.config.get('DEFAULT_DATE_FORMAT', '%Y-%m-%d')
            timezone = current_app.config.get('DEFAULT_TIMEZONE', 'UTC')
        
        try:
            return format_datetime_value(value, format_override or date_format, timezone, include_time)
        except (ValueError, TypeError):
            return str(value)
    
    # Template context processors for global data
    @app.context_processor
    def inject_org_preferences():
        """Inject organization preferences into all templates"""
        from flask_login import current_user
        from flask import current_app
        
        # Create org_settings object with currency method
        class OrgSettings:
            def __init__(self, currency, date_format, timezone, theme):
                self.currency = currency
                self.date_format = date_format
                self.timezone = timezone
                self.theme = theme
            
            def get_currency_symbol(self):
                currency_symbols = {
                    'USD': '$',
                    'EUR': '€',
                    'GBP': '£',
                    'JPY': '¥',
                    'CAD': 'C$',
                    'AUD': 'A$'
                }
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
        from flask_login import current_user
        
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
                # Ensure session is properly set for dashboard routes
                if 'user_id' not in session:
                    session['user_id'] = user.id
                    session.permanent = True
                return user
        except (ValueError, TypeError):
            pass
        
        # Fallback to JWT authentication for backward compatibility
        try:
            from stateless_auth import get_current_user
            jwt_user = get_current_user()
            if jwt_user:
                # Sync JWT user to session
                session['user_id'] = jwt_user.id
                session.permanent = True
                return jwt_user
        except Exception as e:
            print(f"JWT fallback failed: {e}")
        
        return None
    
    # Global template functions for AI confidence scoring
    from utils.ai_review_insights import get_confidence_label, get_confidence_badge_class
    app.jinja_env.globals.update(
        get_confidence_label=get_confidence_label,
        get_confidence_badge_class=get_confidence_badge_class
    )
    
    # Routes
    @app.route('/health')
    def health():
        """Health check endpoint for monitoring systems"""
        try:
            # Test database connection
            db.session.execute(text('SELECT 1'))
            db.session.commit()
            return {'status': 'healthy', 'database': 'connected'}, 200
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}, 503
    
    @app.route('/trigger-error')
    def trigger_error():
        """Test route to trigger an error for Sentry validation"""
        raise Exception("This is a test error for Sentry validation")
    
    @app.before_request
    def before_request():
        session.permanent = True
        
        # Generate CSRF token for forms
        if '_csrf_token' not in session:
            session['_csrf_token'] = secrets.token_hex(16)
        
        # Debug session and authentication state
        print(f"🔧 Session Debug: {dict(session)}")
        
        from flask_login import current_user
        print(f"🔧 Auth Debug: Authenticated={current_user.is_authenticated}")
        if current_user.is_authenticated:
            print(f"🔧 Auth Debug: User={current_user.email}, Role={current_user.role}")
    
    @app.context_processor
    def inject_auth():
        from flask_login import current_user
        return {'current_user': current_user}
    
    @app.route('/')
    def index():
        from flask_login import current_user
        from flask import redirect, url_for, render_template
        
        # Redirect authenticated users to appropriate dashboard
        if current_user.is_authenticated:
            return redirect(url_for('dashboards.dashboard_home'))
        
        # Show landing page for anonymous users
        return render_template('landing.html')
    
    @app.route('/debug-session')
    def debug_session():
        from flask import jsonify
        from flask_login import current_user
        
        return jsonify({
            'session': dict(session),
            'user_authenticated': current_user.is_authenticated,
            'user_id': getattr(current_user, 'id', None),
            'user_email': getattr(current_user, 'email', None)
        })
    
    @app.route('/sync-logs')
    def sync_logs():
        """Development helper to synchronize epic sync logs"""
        from models import Epic, EpicSyncLog
        from datetime import datetime
        
        try:
            # Get all epics
            epics = Epic.query.all()
            
            for epic in epics:
                # Check if sync log already exists
                existing_log = EpicSyncLog.query.filter_by(epic_id=epic.id).first()
                
                if not existing_log:
                    # Create sync log entry
                    sync_log = EpicSyncLog(
                        epic_id=epic.id,
                        sync_type='manual_creation',
                        sync_status='completed',
                        created_at=datetime.utcnow()
                    )
                    db.session.add(sync_log)
            
            db.session.commit()
            return {'status': 'success', 'message': 'Epic sync logs synchronized'}
        
        except Exception as e:
            db.session.rollback()
            return {'status': 'error', 'message': str(e)}, 500
    
    @app.route('/epic/<int:epic_id>/unsync', methods=['POST'])
    def unsync_epic(epic_id):
        """Remove epic sync status (development helper)"""
        from models import Epic, EpicSyncLog
        from flask import redirect, url_for, flash
        
        try:
            # Remove sync logs for this epic
            EpicSyncLog.query.filter_by(epic_id=epic_id).delete()
            
            # Update epic to show it's no longer synced
            epic = Epic.query.get_or_404(epic_id)
            epic.sync_status = 'not_synced'  # assuming this field exists
            
            db.session.commit()
            flash('Epic sync status removed successfully', 'success')
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error removing sync status: {str(e)}', 'error')
        
        return redirect(url_for('business.epic_detail', id=epic_id))
    
    @app.route('/dropdown-demo')
    def dropdown_demo():
        """Demonstration of reusable dropdown macros"""
        from flask import render_template
        from models import Department, User
        
        # Sample data for demonstration
        departments = Department.query.all()
        users = User.query.all()
        
        return render_template('demo/dropdown_demo.html', 
                             departments=departments,
                             users=users)
    
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
        flash('You have been logged out successfully', 'info')
        return redirect(url_for('index'))
    
    # Register blueprints
    with app.app_context():
        # Import models to ensure tables are created
        import models
        db.create_all()
        
        # Seed default departments if none exist
        from models import Department, User, NotificationSetting, EpicSyncLog
        
        if Department.query.count() == 0:
            print("Creating default departments...")
            
            # Create default departments
            corp = Department(name="Corporate", level=1)
            eng = Department(name="Engineering", level=1)
            marketing = Department(name="Marketing", level=1)
            sales = Department(name="Sales", level=1)
            hr = Department(name="Human Resources", level=1)
            finance = Department(name="Finance", level=1)
            ops = Department(name="Operations", level=1)
            
            db.session.add_all([corp, eng, marketing, sales, hr, finance, ops])
            db.session.commit()
            
            print("✓ Default departments created")
        
        # Create default notification settings if none exist
        if NotificationSetting.query.count() == 0:
            print("Creating default notification settings...")
            
            default_settings = [
                NotificationSetting(
                    event_type='EPIC_SUBMITTED',
                    email_enabled=True,
                    in_app_enabled=True,
                    digest_frequency='immediate',
                    escalation_threshold=24
                ),
                NotificationSetting(
                    event_type='BUSINESS_CASE_SUBMITTED',
                    email_enabled=True,
                    in_app_enabled=True,
                    digest_frequency='immediate',
                    escalation_threshold=48
                ),
                NotificationSetting(
                    event_type='PROJECT_MILESTONE_DUE',
                    email_enabled=True,
                    in_app_enabled=True,
                    digest_frequency='daily',
                    escalation_threshold=12
                ),
            ]
            
            for setting in default_settings:
                db.session.add(setting)
            
            db.session.commit()
            print("✓ Default notification settings created")
        
        # Register OAuth blueprint first
        try:
            from auth.oauth import oauth_bp
            app.register_blueprint(oauth_bp, url_prefix='/auth')
            print("✓ OAuth blueprint registered")
        except Exception as e:
            print(f"⚠️ OAuth blueprint registration failed: {e}")
        
        # Register other blueprints
        try:
            from auth import bp as auth_bp
            app.register_blueprint(auth_bp, url_prefix='/auth')
            print("✓ Auth blueprint registered")
            # Debug: List auth routes
            with app.app_context():
                for rule in app.url_map.iter_rules():
                    if rule.endpoint.startswith('auth.'):
                        print(f"  Auth route: {rule.rule} -> {rule.endpoint}")
        except Exception as e:
            print(f"⚠️ Auth blueprint registration failed: {e}")
            import traceback
            traceback.print_exc()
        
        try:
            from dept.routes import dept_bp
            app.register_blueprint(dept_bp, url_prefix='/dept')
            print("✓ Department blueprint registered")
        except Exception as e:
            print(f"⚠️ Department blueprint registration failed: {e}")
        
        try:
            from problems.routes import problems_bp
            app.register_blueprint(problems_bp, url_prefix='/problems')
            print("✓ Problems blueprint registered")
        except Exception as e:
            print(f"⚠️ Problems blueprint registration failed: {e}")
        
        try:
            from business.routes import business_bp
            app.register_blueprint(business_bp, url_prefix='/business')
            print("✓ Business blueprint registered")
        except Exception as e:
            print(f"⚠️ Business blueprint registration failed: {e}")
        
        try:
            from projects.routes import projects_bp
            app.register_blueprint(projects_bp, url_prefix='/projects')
            print("✓ Projects blueprint registered")
        except Exception as e:
            print(f"⚠️ Projects blueprint registration failed: {e}")
        
        try:
            from notifications.routes import notifications_bp
            app.register_blueprint(notifications_bp, url_prefix='/notifications')
            print("✓ Notifications blueprint registered")
        except Exception as e:
            print(f"⚠️ Notifications blueprint registration failed: {e}")
        
        try:
            from notifications.config_routes import notifications_config_bp
            app.register_blueprint(notifications_config_bp)
            print("✓ Notifications config blueprint registered")
        except Exception as e:
            print(f"⚠️ Notifications config blueprint registration failed: {e}")
        
        try:
            from dashboard.routes import dashboard_bp
            app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
            print("✓ Dashboard blueprint registered")
        except Exception as e:
            print(f"⚠️ Dashboard blueprint registration failed: {e}")
        
        try:
            from reports.routes import reports_bp
            app.register_blueprint(reports_bp, url_prefix='/reports')
            print("✓ Reports blueprint registered")
        except Exception as e:
            print(f"⚠️ Reports blueprint registration failed: {e}")
        
        try:
            from admin_working import init_admin_routes
            init_admin_routes(app)
            print("✓ Admin routes initialized")
        except Exception as e:
            print(f"⚠️ Admin routes initialization failed: {e}")
        
        try:
            from admin.routes import admin_bp
            app.register_blueprint(admin_bp, url_prefix='/admin')
            print("✓ Admin blueprint registered")
        except Exception as e:
            print(f"⚠️ Admin blueprint registration failed: {e}")
        
        try:
            from search.routes import search_bp
            app.register_blueprint(search_bp, url_prefix='/search')
            print("✓ Search blueprint registered")
        except Exception as e:
            print(f"⚠️ Search blueprint registration failed: {e}")
        
        try:
            from ai.routes import ai_bp
            app.register_blueprint(ai_bp, url_prefix='/ai')
            print("✓ AI blueprint registered")
        except Exception as e:
            print(f"⚠️ AI blueprint registration failed: {e}")
        
        try:
            from predict.routes import predict_bp
            app.register_blueprint(predict_bp, url_prefix='/predict')
            print("✓ Predict blueprint registered")
        except Exception as e:
            print(f"⚠️ Predict blueprint registration failed: {e}")
        
        try:
            from workflows.routes import workflows_bp
            app.register_blueprint(workflows_bp, url_prefix='/workflows')
            print("✓ Workflows blueprint registered")
        except Exception as e:
            print(f"⚠️ Workflows blueprint registration failed: {e}")
        
        try:
            from review.routes import review_bp
            app.register_blueprint(review_bp, url_prefix='/review')
            print("✓ Review blueprint registered")
        except Exception as e:
            print(f"⚠️ Review blueprint registration failed: {e}")
        
        try:
            from help.routes import help_bp
            app.register_blueprint(help_bp, url_prefix='/help')
            print("✓ Help blueprint registered")
        except Exception as e:
            print(f"⚠️ Help blueprint registration failed: {e}")
        
        try:
            from analytics.routes import analytics_bp
            app.register_blueprint(analytics_bp, url_prefix='/analytics')
            print("✓ Analytics blueprint registered")
        except Exception as e:
            print(f"⚠️ Analytics blueprint registration failed: {e}")
        
        try:
            from dashboards.routes import dash_bp
            app.register_blueprint(dash_bp)
            print("✓ Dashboards blueprint registered")
            # Debug: Print available routes
            with app.app_context():
                for rule in app.url_map.iter_rules():
                    if 'dashboard' in rule.endpoint:
                        print(f"  Dashboard route: {rule.rule} -> {rule.endpoint}")
        except Exception as e:
            print(f"⚠️ Dashboards blueprint registration failed: {e}")
        
        try:
            from settings.routes import settings_bp
            app.register_blueprint(settings_bp, url_prefix='/settings')
            print("✓ Settings blueprint registered")
        except Exception as e:
            print(f"⚠️ Settings blueprint registration failed: {e}")
        
        try:
            from waitlist.routes import waitlist_bp
            app.register_blueprint(waitlist_bp, url_prefix='/waitlist')
            print("✓ Waitlist blueprint registered")
        except Exception as e:
            print(f"⚠️ Waitlist blueprint registration failed: {e}")
        
        try:
            from solutions.routes import solutions_bp
            app.register_blueprint(solutions_bp, url_prefix='/solutions')
            print("✓ Solutions blueprint registered")
        except Exception as e:
            print(f"⚠️ Solutions blueprint registration failed: {e}")
        
        try:
            from monitoring.dashboard import monitoring_bp
            app.register_blueprint(monitoring_bp)
            print("✓ Monitoring blueprint registered")
        except Exception as e:
            print(f"⚠️ Monitoring blueprint registration failed: {e}")
        
        try:
            from public import bp as public_bp
            app.register_blueprint(public_bp)
            print("✓ Public blueprint registered")
        except Exception as e:
            print(f"⚠️ Public blueprint registration failed: {e}")
        
        # Initialize notification templates and report scheduler on startup
        from notifications.service import initialize_default_templates
        initialize_default_templates()
        
        # Initialize report scheduler
        try:
            from reports.scheduler import init_report_scheduler
            init_report_scheduler()
            print("✓ Report scheduler initialized")
        except Exception as e:
            print(f"⚠️ Report scheduler initialization failed: {e}")
        
        # Initialize ML training scheduler
        try:
            from analytics.scheduler import init_ml_scheduler
            init_ml_scheduler()
            print("✓ ML training scheduler initialized")
            
            # Initialize workflow processor
            try:
                from workflows.integration import initialize_workflow_integrations
                workflow_integrations = initialize_workflow_integrations()
                print("🔄 Workflow processor initialized")
            except Exception as e:
                print(f"⚠️ Workflow processor initialization failed: {e}")
        except Exception as e:
            print(f"⚠️ ML training scheduler initialization failed: {e}")
    
    return app

# Create the app instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)