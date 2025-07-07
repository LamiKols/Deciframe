from flask import Flask, request, session
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate  
from flask_login import LoginManager, current_user
from sqlalchemy.orm import DeclarativeBase
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

def generate_csrf_token():
    """Generate a CSRF token for forms"""
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(16)
    return session['_csrf_token']
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)  # ← CORRECT: Outside class
    db = SQLAlchemy(model_class=Base)
# Initialize Flask extensions
db = SQLAlchemy(model_class=Base)
migrate = Migrate()
login_manager = LoginManager()
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

app = Flask(__name__)
app.config.from_object(Config)

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
    
    # Currency symbol mapping
    symbols = {
        'USD': '$', 'EUR': '€', 'GBP': '£', 'CAD': 'C$', 
        'AUD': 'A$', 'JPY': '¥', 'CNY': '¥', 'INR': '₹'
    }
    
    if value is None:
        return ''
    
    try:
        amount = float(value)
        if include_symbol:
            symbol = symbols.get(currency_code, currency_code)
            return f"{symbol}{amount:,.2f}"
        else:
            return f"{amount:,.2f}"
    except (ValueError, TypeError):
        return str(value)

@app.template_filter('format_org_date')
def format_org_date_filter(value, format_override=None):
    """Format a date using organization preferences"""
    from flask_login import current_user
    from flask import current_app
    
    if not value:
        return ''
    
    if not format_override:
        # Get date format from org_prefs context or fallback
        if current_user.is_authenticated:
            org = getattr(current_user, 'organization', None)
            date_format = getattr(org, 'date_format', current_app.config.get('DEFAULT_DATE_FORMAT', 'ISO'))
        else:
            date_format = current_app.config.get('DEFAULT_DATE_FORMAT', 'ISO')
    else:
        date_format = format_override
    
    # Convert ISO format to actual strftime format
    if date_format == 'ISO':
        date_format = '%Y-%m-%d'
    
    try:
        if hasattr(value, 'strftime'):
            return value.strftime(date_format)
        else:
            return str(value)
    except (AttributeError, ValueError):
        return str(value)

@app.template_filter('format_org_datetime')
def format_org_datetime_filter(value, format_override=None, include_time=True):
    """Format a datetime using organization preferences with timezone support"""
    from flask_login import current_user
    from flask import current_app
    import pytz
    
    if not value:
        return ''
    
    if not format_override:
        # Get preferences from org_prefs context or fallback
        if current_user.is_authenticated:
            org = getattr(current_user, 'organization', None)
            date_format = getattr(org, 'date_format', current_app.config.get('DEFAULT_DATE_FORMAT', 'ISO'))
            timezone_name = getattr(org, 'timezone', current_app.config.get('DEFAULT_TIMEZONE', 'UTC'))
        else:
            date_format = current_app.config.get('DEFAULT_DATE_FORMAT', 'ISO')
            timezone_name = current_app.config.get('DEFAULT_TIMEZONE', 'UTC')
    else:
        date_format = format_override
        timezone_name = current_app.config.get('DEFAULT_TIMEZONE', 'UTC')
    
    # Convert ISO format to actual strftime format
    if date_format == 'ISO':
        date_format = '%Y-%m-%d'
    
    # Add time component if requested
    if include_time:
        date_format += ' %H:%M:%S'
    
    try:
        # Convert to organization timezone if needed
        if hasattr(value, 'astimezone') and timezone_name != 'UTC':
            try:
                org_tz = pytz.timezone(timezone_name)
                if value.tzinfo is None:
                    # Assume UTC if no timezone info
                    value = pytz.utc.localize(value)
                value = value.astimezone(org_tz)
            except (pytz.exceptions.UnknownTimeZoneError, AttributeError):
                pass  # Fall back to original value
        
        if hasattr(value, 'strftime'):
            return value.strftime(date_format)
        else:
            return str(value)
    except (AttributeError, ValueError):
        return str(value)

# Register timezone utility filters
from utils.timezone_utils import register_timezone_filters
register_timezone_filters(app)

# Register AI review insights helper functions
from utils.ai_review_insights import get_confidence_badge_class, get_confidence_label
app.jinja_env.globals['get_confidence_badge_class'] = get_confidence_badge_class
app.jinja_env.globals['get_confidence_label'] = get_confidence_label

# Global context processor for organization preferences
@app.context_processor
def inject_org_preferences():
    """Inject organization preferences into all templates"""
    from flask_login import current_user
    from flask import current_app
    
    if not current_user.is_authenticated:
        return {
            'org_prefs': {
                'currency': current_app.config.get('DEFAULT_CURRENCY', 'USD'),
                'date_format': current_app.config.get('DEFAULT_DATE_FORMAT', 'ISO'),
                'timezone': current_app.config.get('DEFAULT_TIMEZONE', 'UTC'),
                'theme': 'light'
            }
        }
    
    org = getattr(current_user, 'organization', None)
    # Use user theme preference first, then organization default, then 'light'
    user_theme = getattr(current_user, 'theme', None)
    org_theme = getattr(org, 'default_theme', 'light') if org else 'light'
    theme = user_theme if user_theme else org_theme
    
    print(f"🔧 Context Processor Debug:")
    print(f"   User Theme: {user_theme}")
    print(f"   Org Theme: {org_theme}")
    print(f"   Final Theme: {theme}")
    
    return {
        'org_prefs': {
            'currency': getattr(org, 'currency', current_app.config.get('DEFAULT_CURRENCY', 'USD')),
            'date_format': getattr(org, 'date_format', current_app.config.get('DEFAULT_DATE_FORMAT', 'ISO')),
            'timezone': getattr(org, 'timezone', current_app.config.get('DEFAULT_TIMEZONE', 'UTC')),
            'theme': theme
        }
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

db.init_app(app)
migrate.init_app(app, db)

# Initialize Flask-Login with proper user loader
from flask_login import LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

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
    except:
        pass
    
    return None

# Health check route for uptime monitoring
@app.route('/health')
def health():
    """Health check endpoint for monitoring systems"""
    try:
        # Check database connectivity
        db_status = db.session.execute(text('SELECT 1')).scalar()
        return {
            'status': 'ok',
            'database': 'connected' if db_status == 1 else 'error',
            'timestamp': datetime.now().isoformat()
        }, 200
    except Exception as e:
        return {
            'status': 'error',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, 500

# Error test route for Sentry validation
@app.route('/error')
def trigger_error():
    """Test route to trigger an error for Sentry validation"""
    if app.config.get('DEBUG'):
        raise Exception("Test error for monitoring validation")
    return {'error': 'Error testing only available in debug mode'}, 403

# Initialize OAuth manager for SSO/OIDC authentication
try:
    from auth.oauth import oauth_manager
    oauth_manager.init_app(app)
    print("✓ OAuth manager initialized for SSO/OIDC authentication")
except Exception as e:
    print(f"⚠️ OAuth manager initialization failed: {e}")

# Initialize clean OIDC client with factory pattern
try:
    from auth.oidc import init_oidc
    init_oidc(app)
except Exception as e:
    print(f"⚠️ OIDC client initialization failed: {e}")

# Import and register blueprints after app initialization
from auth import bp as auth_bp
from dept import dept as dept_bp
from problems.routes import problems
from business.routes import business_bp
from projects.routes import projects_bp
from help.routes import help_bp
from help.chat_assistant import help_chat_bp
from waitlist import waitlist_bp
from platform_admin import platform_admin_bp
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(dept_bp, url_prefix='/dept')
app.register_blueprint(problems, url_prefix='/problems')
app.register_blueprint(business_bp)
app.register_blueprint(projects_bp)
app.register_blueprint(help_bp)
app.register_blueprint(help_chat_bp)
app.register_blueprint(waitlist_bp)
app.register_blueprint(platform_admin_bp)

# Register Review blueprint
try:
    from review import review_bp
    app.register_blueprint(review_bp)
    print("✓ Review blueprint registered")
except Exception as e:
    print(f"⚠️ Review blueprint registration failed: {e}")

# Register OIDC blueprint
try:
    from auth.routes_oidc import oidc_bp
    app.register_blueprint(oidc_bp)
    print("✓ OIDC blueprint registered")
except Exception as e:
    print(f"⚠️ OIDC blueprint registration failed: {e}")

# Add JWT authentication debugging
@app.before_request
def before_request():
    from flask import request, session
    from flask_login import current_user
    from stateless_auth import get_current_user
    
    # Debug both session and JWT authentication
    session_auth = current_user.is_authenticated and 'user_id' in session
    jwt_user = get_current_user()
    
    print(f"🔧 Request to: {request.endpoint}")
    print(f"🔧 Session Auth: {current_user.name if session_auth else 'Not authenticated'}")
    print(f"🔧 JWT Auth: {jwt_user.name if jwt_user else 'Not authenticated'}")
    
    # For dashboard routes, ensure proper authentication sync
    if request.endpoint and request.endpoint.startswith('dashboards.'):
        from flask_login import login_user
        if jwt_user and not session_auth:
            session['user_id'] = jwt_user.id
            session.permanent = True
            login_user(jwt_user)
        elif 'user_id' in session and not current_user.is_authenticated:
            # Sync session user to Flask-Login
            try:
                from models import User
                user = User.query.get(session['user_id'])
                if user:
                    login_user(user)
            except:
                pass

# Context processor to make auth variables and organization settings available to all templates
@app.context_processor
def inject_auth():
    from flask_login import current_user
    from stateless_auth import get_current_user
    from models import OrganizationSettings
    
    # Get organization settings for global access
    try:
        org_settings = OrganizationSettings.get_organization_settings()
    except Exception as e:
        db.session.rollback()  # Rollback failed transaction
        org_settings = None
    
    # Check Flask-Login session first, then JWT fallback
    if current_user.is_authenticated:
        # Get user's effective theme
        user_theme = getattr(current_user, 'theme', None)
        org_default_theme = getattr(org_settings, 'default_theme', 'light') if org_settings else 'light'
        effective_theme = user_theme if user_theme else org_default_theme
        
        return {
            'logged_in': True,
            'user': current_user,
            'org_settings': org_settings,
            'currency_symbol': org_settings.get_currency_symbol() if org_settings else '$',
            'user_theme': user_theme,
            'org_default_theme': org_default_theme,
            'effective_theme': effective_theme,
            'csrf_token': generate_csrf_token,
        }
    
    # Fallback to JWT authentication
    jwt_user = get_current_user()
    if jwt_user:
        user_theme = getattr(jwt_user, 'theme', None)
        org_default_theme = getattr(org_settings, 'default_theme', 'light') if org_settings else 'light'
        effective_theme = user_theme if user_theme else org_default_theme
        
        return {
            'logged_in': True,
            'user': jwt_user,
            'org_settings': org_settings,
            'currency_symbol': org_settings.get_currency_symbol() if org_settings else '$',
            'user_theme': user_theme,
            'org_default_theme': org_default_theme,
            'effective_theme': effective_theme
        }
    
    # Not authenticated - use organization default or light theme
    org_default_theme = getattr(org_settings, 'default_theme', 'light') if org_settings else 'light'
    return {
        'logged_in': False,
        'user': None,
        'org_settings': org_settings,
        'currency_symbol': org_settings.get_currency_symbol() if org_settings else '$',
        'user_theme': None,
        'org_default_theme': org_default_theme,
        'effective_theme': org_default_theme
    }

# Create database tables and sample data
with app.app_context():
    import models
    import simple_session  # Import to register SimpleSessionData model
    db.create_all()
    
    # Create sample departments if they don't exist
    from models import Department
    if Department.query.count() == 0:
        departments = [
            Department(name='Executive', level=1),
            Department(name='Engineering', level=1),
            Department(name='Sales', level=1),
            Department(name='Marketing', level=1),
            Department(name='Human Resources', level=1),
            Department(name='Finance', level=1),
            Department(name='Operations', level=1),
        ]
        for dept in departments:
            db.session.add(dept)
        db.session.commit()
    
    # Initialize notification settings with default configuration
    from models import NotificationSetting, FrequencyEnum
    core_events = [
        ('problem_created', FrequencyEnum.immediate, True, True, False, None),
        ('case_approved', FrequencyEnum.immediate, True, True, False, None), 
        ('project_created', FrequencyEnum.daily, True, True, False, 24),
        ('milestone_due', FrequencyEnum.immediate, True, True, True, 2),
        ('milestone_overdue', FrequencyEnum.immediate, True, True, True, 1)
    ]
    
    for event_name, frequency, email, in_app, push, threshold in core_events:
        if not NotificationSetting.query.filter_by(event_name=event_name).first():
            ns = NotificationSetting(
                event_name=event_name,
                frequency=frequency,
                channel_email=email,
                channel_in_app=in_app,
                channel_push=push,
                threshold_hours=threshold
            )
            db.session.add(ns)
    
    db.session.commit()

@app.route('/')
def index():
    from flask import render_template
    from flask_login import current_user
    
    # Show landing page for unauthenticated users
    if not current_user.is_authenticated:
        return render_template('landing.html')
    
    # Show role-based home page for authenticated users
    from flask import redirect, url_for
    logged_in = current_user.is_authenticated
    print(f"🏠 Index route - Session login status: {logged_in}")
    if logged_in:
        print(f"🏠 Current user: {current_user.name} ({current_user.email})")
        # Show home page instead of redirecting to dashboard
        return render_template('index.html', user=current_user, logged_in=True)
    else:
        # Redirect unauthenticated users to login
        return redirect(url_for('auth.login'))

@app.route('/debug-session')
def debug_session():
    from flask import jsonify, session, request
    from stateless_auth import get_current_user
    
    user = get_current_user()
    debug_info = {
        'flask_session': dict(session),
        'jwt_user': {
            'authenticated': user is not None,
            'name': user.name if user else None,
            'email': user.email if user else None,
            'id': user.id if user else None
        },
        'request_args': dict(request.args),
        'auth_token_present': 'auth_token' in request.args
    }
    return jsonify(debug_info)

@app.route('/sync-logs')
def sync_logs():
    from flask import render_template
    from flask_login import login_required
    from models import EpicSyncLog
    
    logs = EpicSyncLog.query.order_by(EpicSyncLog.timestamp.desc()).all()
    return render_template('sync_logs.html', logs=logs)

@app.route('/epic/<int:epic_id>/unsync', methods=['POST'])
def unsync_epic(epic_id):
    from flask import redirect, url_for
    from flask_login import login_required
    from models import Epic, EpicSyncLog
    from app import db
    
    epic = Epic.query.get_or_404(epic_id)
    project_id = epic.project_id  # Store current project_id for logging
    epic.project_id = None
    
    # Log the unsync action
    log = EpicSyncLog(epic_id=epic_id, project_id=project_id, action='unsynced')
    db.session.add(log)
    db.session.commit()
    
    return redirect(url_for('index'))

@app.route('/demo/dropdowns')
def dropdown_demo():
    """Demonstration of reusable dropdown macros"""
    from flask import render_template
    from models import Department, User
    
    # Get sample data for demonstration
    departments = Department.query.all()
    users = User.query.limit(10).all()
    
    return render_template('macros/demo.html', 
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
    from flask import session, redirect, url_for
    from flask_login import logout_user
    session.clear()
    logout_user()
    return redirect(url_for('index'))

# Register blueprints (avoiding conflicts with existing registrations)
try:
    from notifications.routes import notifications_bp
    app.register_blueprint(notifications_bp)
    print("✓ Notifications blueprint registered")
except Exception as e:
    print(f"⚠️ Notifications blueprint registration failed: {e}")

# Register notification configuration blueprint
try:
    from notifications.config_routes import notifications_config_bp
    app.register_blueprint(notifications_config_bp)
    print("✓ Notification configuration blueprint registered")
except Exception as e:
    print(f"⚠️ Notification configuration blueprint registration failed: {e}")

# Register dashboards blueprint
try:
    from dashboards.routes import dash_bp
    app.register_blueprint(dash_bp)
    print("✓ Dashboards blueprint registered")
except Exception as e:
    print(f"⚠️ Dashboards blueprint registration failed: {e}")

# Register settings blueprint
try:
    from settings import settings_bp
    app.register_blueprint(settings_bp)
    print("✓ Settings blueprint registered")
except Exception as e:
    print(f"⚠️ Settings blueprint registration failed: {e}")

# Note: Dashboard blueprint removed to avoid conflicts with dashboards blueprint

# Register reports blueprint
try:
    from reports.routes import reports_bp
    app.register_blueprint(reports_bp)
    print("✓ Reports blueprint registered")
except Exception as e:
    print(f"⚠️ Reports blueprint registration failed: {e}")

# Register predict blueprint
try:
    from predict.routes import predict_bp
    app.register_blueprint(predict_bp)
    print("✓ Predict blueprint registered")
except Exception as e:
    print(f"⚠️ Predict blueprint registration failed: {e}")

# Register Admin blueprint
try:
    from admin.routes import admin_bp
    app.register_blueprint(admin_bp)
    print("✓ Admin blueprint registered")
except Exception as e:
    print(f"⚠️ Admin blueprint registration failed: {e}")
    import traceback
    traceback.print_exc()

# Initialize Admin routes (legacy)
try:
    from admin_working import init_admin_routes
    init_admin_routes(app)
    print("✓ Admin routes initialized")
except Exception as e:
    print(f"⚠️ Admin routes failed: {e}")
    import traceback
    traceback.print_exc()

# Register Data Management blueprint
try:
    from admin.data_management import init_data_management_routes
    init_data_management_routes(app)
    print("✓ Data management routes initialized")
except Exception as e:
    print(f"⚠️ Data management routes failed: {e}")
    import traceback
    traceback.print_exc()

# Register AI blueprint  
try:
    from ai.routes import ai_bp
    app.register_blueprint(ai_bp)
    print("✓ AI blueprint registered")
except Exception as e:
    print(f"⚠️ AI blueprint registration failed: {e}")

# Register Search blueprints
try:
    from search.routes import search_bp
    from search.api_routes import search_api_bp
    app.register_blueprint(search_bp)
    app.register_blueprint(search_api_bp)
    print("✓ Search blueprints registered")
except Exception as e:
    print(f"⚠️ Search blueprint registration failed: {e}")

# Register Solutions blueprint
try:
    from solutions.routes import solutions_bp
    app.register_blueprint(solutions_bp, url_prefix='/solutions')
    print("✓ Solutions blueprint registered")
except Exception as e:
    print(f"⚠️ Solutions blueprint registration failed: {e}")

# Register monitoring blueprint
try:
    from monitoring.dashboard import monitoring_bp
    app.register_blueprint(monitoring_bp)
    print("✓ Monitoring blueprint registered")
except Exception as e:
    print(f"⚠️ Monitoring blueprint registration failed: {e}")

# Register public blueprint
try:
    from public import bp as public_bp
    app.register_blueprint(public_bp)
    print("✓ Public blueprint registered")
except Exception as e:
    print(f"⚠️ Public blueprint registration failed: {e}")

# Initialize notification templates and report scheduler on startup
with app.app_context():
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

if __name__ == '__main__':
    app.run(debug=True)
