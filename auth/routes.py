from flask import render_template, redirect, url_for, flash, request, session, current_app, make_response, Blueprint, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse
from auth import bp
from auth.forms import LoginForm, RegistrationForm, ProfileForm
from auth.oauth import oauth_manager, UserManager, OAuthError
from auth.oidc import oauth, get_oidc_client
from models import User, Organization, RoleEnum
from app import db
from utils.email_validation import extract_domain, is_new_organization_domain
import logging

# Create test blueprint for development and debugging
test_bp = Blueprint('test', __name__, url_prefix='/test')

logger = logging.getLogger(__name__)

def is_first_user_in_org(user):
    """Check if the current user is the first and only user in their organization"""
    if not user or not user.organization_id:
        return False
    org_users = User.query.filter_by(organization_id=user.organization_id).count()
    return org_users == 1 and user.role == RoleEnum.Admin

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login route"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        print(f"🔍 Login attempt for: {form.email.data}")
        print(f"🔍 User found: {user is not None}")
        
        if user:
            password_valid = user.check_password(form.password.data)
            print(f"🔍 Password valid: {password_valid}")
            if password_valid:
                # Use session-based authentication with Flask-Login
                from flask_login import login_user
                
                # Store user_id in session and login with Flask-Login
                session['user_id'] = user.id
                login_user(user, remember=form.remember_me.data)
                
                print(f"🔍 Session login - User ID: {user.id}, Session stored")
                
                # Handle next parameter for redirect after login
                next_page = request.args.get('next')
                if not next_page or urlparse(next_page).netloc != '':
                    next_page = url_for('dashboards.dashboard_home')
                
                flash(f'Welcome back, {user.name}!', 'success')
                return redirect(next_page)
        
        flash('Invalid email or password', 'danger')
    
    return render_template('auth/login.html', title='Sign In', form=form)

@bp.route('/logout')
def logout():
    """User logout route"""
    from flask_login import logout_user
    
    # Clear session and logout with Flask-Login
    session.pop('user_id', None)
    logout_user()
    
    flash('You have been logged out!', 'info')
    return redirect(url_for('index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route"""
    from flask_login import current_user, login_user
    
    # Check if user is already authenticated
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    # Clear any existing flash messages on GET request to prevent unwanted messages from showing
    if request.method == 'GET':
        session.pop('_flashes', None)
    
    # Get email domain to determine organization
    email_domain = None
    if request.method == 'POST':
        email_domain = request.form.get('email', '').split('@')[1].lower() if '@' in request.form.get('email', '') else None
    
    form = RegistrationForm(email_domain=email_domain)
    if form.validate_on_submit():
        # Check Terms of Use and Privacy Policy acceptance
        if 'agree_terms' not in request.form:
            flash("You must accept the Terms of Use and Privacy Policy to create an account.", "danger")
            return render_template('auth/register.html', title='Register', form=form)
        
        from models import RoleEnum, Organization
        
        # Extract email domain for organization assignment
        email_domain = extract_domain(form.email.data)
        
        # Find or create organization based on email domain
        organization = Organization.query.filter_by(domain=email_domain).first()
        if not organization:
            # This is a new organization - validate required fields
            if not form.organization_name.data:
                flash("Organization name is required for new organizations.", "danger")
                return render_template('auth/register.html', title='Register', form=form)
            
            # Create new organization with provided details
            organization = Organization(
                name=form.organization_name.data,
                domain=email_domain,
                industry=form.industry.data if form.industry.data else None,
                size=form.organization_size.data if form.organization_size.data else None,
                country=form.country.data if form.country.data else None
            )
            db.session.add(organization)
            db.session.flush()  # Get the organization ID before committing
            print(f"🏢 Created new organization: {organization.name} for domain: {email_domain}")
        
        # Check if this is the first user in this organization (auto-assign Admin role)
        existing_users_count = User.query.filter_by(organization_id=organization.id).count()
        is_first_user_in_org = existing_users_count == 0
        
        user = User()
        user.name = form.name.data
        user.email = form.email.data
        user.organization_id = organization.id
        
        # Assign role: Admin if first user in organization, otherwise use form selection
        if is_first_user_in_org:
            user.role = RoleEnum.Admin
            print(f"🔧 First user in organization {organization.name} - automatically assigned Admin role to {user.email}")
        else:
            user.role = RoleEnum(form.role.data)
        
        user.reports_to = form.reports_to.data if form.reports_to.data != 0 else None
        user.set_password(form.password.data)
        
        # Handle department assignment
        if form.department_id.data == -1:  # "My department isn't listed"
            user.set_pending_department()
        elif form.department_id.data != 0:
            user.assign_department(form.department_id.data)
        else:
            user.org_unit_id = None
        
        try:
            db.session.add(user)
            db.session.commit()
            
            if user.has_pending_department:
                flash(f'Registration successful! Welcome to DeciFrame, {user.name}!', 'success')
                if is_first_user_in_org:
                    flash('As the first user in your organization, you have been automatically assigned Administrator privileges to set up the system.', 'info')
                flash('Your department assignment is pending. Please contact an administrator to complete your setup. You have limited access until your department is assigned.', 'warning')
            else:
                flash(f'Registration successful! Welcome to DeciFrame, {user.name}!', 'success')
                if is_first_user_in_org:
                    flash('As the first user in your organization, you have been automatically assigned Administrator privileges to set up the system.', 'info')
            
            # Store user_id in session and login with Flask-Login
            session['user_id'] = user.id
            login_user(user)
            print(f"🟢 User {user.name} registered and logged in via session")
            
            return redirect(url_for('dashboards.dashboard_home'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Registration error: {str(e)}')
            flash('Registration failed. Please try again.', 'danger')
    else:
        if request.method == 'POST':
            print("🔴 Registration form errors:", form.errors)
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{field}: {error}', 'danger')
    
    return render_template('auth/register.html', title='Register', form=form)

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile management route"""
    form = ProfileForm(original_email=current_user.email)
    
    if form.validate_on_submit():
        from models import RoleEnum
        current_user.name = form.name.data
        current_user.email = form.email.data
        current_user.role = RoleEnum(form.role.data)
        current_user.org_unit_id = form.org_unit_id.data if form.org_unit_id.data != 0 else None
        current_user.reports_to = form.reports_to.data if form.reports_to.data != 0 else None
        current_user.timezone = form.timezone.data if form.timezone.data else None
        
        try:
            db.session.commit()
            flash('Your profile has been updated!', 'success')
            return redirect(url_for('auth.profile'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Profile update error: {str(e)}')
            flash('Profile update failed. Please try again.', 'danger')
    
    elif request.method == 'GET':
        # Pre-populate form with current user data
        form.name.data = current_user.name
        form.email.data = current_user.email
        form.role.data = current_user.role.value if current_user.role else None
        form.org_unit_id.data = current_user.org_unit_id
        form.timezone.data = current_user.timezone
        # reports_to field not available in current User model
    
    return render_template('auth/profile.html', title='Profile', form=form)

# OAuth/SSO Routes
@bp.route('/sso/<provider>')
def sso_login(provider):
    """Initiate SSO login with specified provider"""
    try:
        if not oauth_manager.get_provider(provider):
            flash(f'Authentication provider {provider} is not configured', 'danger')
            return redirect(url_for('auth.login'))
        
        # Store the next URL for post-login redirect
        if 'next' in request.args:
            session['oauth_next_url'] = request.args.get('next')
        
        return oauth_manager.authorize_redirect(provider)
        
    except Exception as e:
        logger.error(f"SSO login failed for {provider}: {e}")
        flash('Authentication service temporarily unavailable', 'danger')
        return redirect(url_for('auth.login'))

@bp.route('/oauth/callback/<provider>')
def oauth_callback(provider):
    """Handle OAuth callback from provider"""
    try:
        # Parse the OAuth token and user info
        token, user_info = oauth_manager.parse_token(provider)
        
        if not user_info or not user_info.get('email'):
            flash('Authentication failed: Email not provided by provider', 'danger')
            return redirect(url_for('auth.login'))
        
        # Create or update user from OAuth info
        user = UserManager.create_or_update_user(user_info, provider)
        
        if not user.is_active:
            flash('Your account has been deactivated. Please contact an administrator.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Create JWT token for stateless authentication
        from stateless_auth import create_auth_token
        auth_token = create_auth_token(user.id)
        
        # Determine redirect URL
        next_url = session.pop('oauth_next_url', None)
        if not next_url or urlparse(next_url).netloc != '':
            next_url = url_for('index')
        
        # Create response with secure HttpOnly cookie
        resp = make_response(redirect(next_url))
        resp.set_cookie(
            'auth_token', auth_token,
            httponly=True,
            max_age=12*3600,  # 12 hours
            samesite='Lax',
            secure=False  # Set to True for HTTPS in production
        )
        
        flash(f'Welcome {user.name}! Logged in via {provider.title()}', 'success')
        logger.info(f"OAuth login successful: {user.email} via {provider}")
        
        return resp
        
    except OAuthError as e:
        logger.error(f"OAuth callback error for {provider}: {e}")
        flash('Authentication failed. Please try again.', 'danger')
        return redirect(url_for('auth.login'))
    except Exception as e:
        logger.error(f"Unexpected error in OAuth callback for {provider}: {e}")
        flash('An unexpected error occurred during authentication', 'danger')
        return redirect(url_for('auth.login'))

@bp.route('/oidc/login')
def oidc_login():
    """Clean OIDC login using Authlib client"""
    try:
        oidc_client = get_oidc_client()
        if not oidc_client:
            flash('OIDC authentication not configured', 'danger')
            return redirect(url_for('auth.login'))
        
        # Store the next URL for post-login redirect
        if 'next' in request.args:
            session['oauth_next_url'] = request.args.get('next')
        
        redirect_uri = url_for('auth.oidc_callback', _external=True)
        return oidc_client.authorize_redirect(redirect_uri)
        
    except Exception as e:
        logger.error(f"OIDC login failed: {e}")
        flash('Authentication service temporarily unavailable', 'danger')
        return redirect(url_for('auth.login'))

@bp.route('/oidc/callback')
def oidc_callback():
    """Handle OIDC callback"""
    try:
        oidc_client = get_oidc_client()
        if not oidc_client:
            flash('OIDC authentication not configured', 'danger')
            return redirect(url_for('auth.login'))
        
        # Get the token and parse user info
        token = oidc_client.authorize_access_token()
        user_info = oidc_client.parse_id_token(token)
        
        if not user_info or not user_info.get('email'):
            flash('Authentication failed: Email not provided by provider', 'danger')
            return redirect(url_for('auth.login'))
        
        # Create or update user
        user = UserManager.create_or_update_user(user_info, 'oidc')
        
        # Log the user in
        login_user(user, remember=True)
        
        # Redirect to intended destination
        next_url = session.pop('oauth_next_url', None)
        if next_url and urlparse(next_url).netloc == '':
            return redirect(next_url)
        
        flash(f'Successfully logged in with OIDC', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        logger.error(f"OIDC callback failed: {e}")
        flash('Authentication failed. Please try again.', 'danger')
        return redirect(url_for('auth.login'))

@bp.route('/sso/providers')
def sso_providers():
    """API endpoint to get enabled SSO providers"""
    try:
        providers = oauth_manager.get_enabled_providers()
        provider_list = [
            {
                'name': provider,
                'display_name': provider.title(),
                'login_url': url_for('auth.sso_login', provider=provider)
            }
            for provider in providers
        ]
        
        # Add clean OIDC if configured
        oidc_client = get_oidc_client()
        if oidc_client:
            provider_list.append({
                'name': 'oidc',
                'display_name': 'Enterprise SSO',
                'login_url': url_for('oidc.login')
            })
        
        return {'providers': provider_list}
    except Exception as e:
        logger.error(f"Error getting SSO providers: {e}")
        return {'providers': []}

@bp.route('/toggle-theme', methods=['POST'])
@login_required
def toggle_theme():
    """Toggle user theme preference between light and dark"""
    try:
        # Toggle between light and dark
        current_user.theme = 'dark' if current_user.theme == 'light' else 'light'
        db.session.commit()
        
        flash(f"Theme changed to {current_user.theme} mode", "info")
        return redirect(request.referrer or url_for('dashboards.dashboard_home'))
    except Exception as e:
        logger.error(f"Error toggling theme: {e}")
        flash("Failed to update theme", "error")
        return redirect(request.referrer or url_for('dashboards.dashboard_home'))

@bp.route('/update-theme', methods=['POST'])
@login_required
def update_theme():
    """Update user's theme preference"""
    try:
        from flask import jsonify, request
        data = request.get_json()
        if not data or 'theme' not in data:
            return jsonify({'error': 'Theme not provided'}), 400
        
        theme = data['theme']
        if theme not in ['light', 'dark']:
            return jsonify({'error': 'Invalid theme'}), 400
        
        # Update user's theme preference
        current_user.theme = theme
        db.session.commit()
        
        return jsonify({'success': True, 'theme': theme})
    except Exception as e:
        logger.error(f"Error updating theme: {e}")
        return jsonify({'error': 'Failed to update theme'}), 500

@bp.route('/mark-onboarded', methods=['POST'])
@login_required
def mark_onboarded():
    """Mark user as onboarded after welcome modal"""
    try:
        current_user.onboarded = True
        db.session.commit()
        flash("Welcome! You're ready to go.", "success")
        return redirect(request.referrer or url_for('dashboards.dashboard_home'))
    except Exception as e:
        logger.error(f"Error marking user as onboarded: {e}")
        flash("Error completing onboarding", "error")
        return redirect(request.referrer or url_for('index'))

@bp.route('/check-domain', methods=['POST'])
def check_domain():
    """AJAX endpoint to check if email domain is new"""
    try:
        data = request.get_json()
        domain = data.get('domain', '').lower()
        
        if not domain:
            return {'is_new_domain': False}
        
        is_new = is_new_organization_domain(domain)
        return {'is_new_domain': is_new}
    except Exception as e:
        logger.error(f"Error checking domain: {e}")
        return {'is_new_domain': False}

# Test routes for development and debugging
@test_bp.route('/')
def test_home():
    """Test route home page"""
    return jsonify({
        'message': 'Test blueprint is working',
        'user': current_user.email if current_user.is_authenticated else 'Anonymous',
        'role': current_user.role.value if current_user.is_authenticated and current_user.role else None,
        'authenticated': current_user.is_authenticated
    })

@test_bp.route('/session')
def test_session():
    """Debug session information"""
    return jsonify({
        'session': dict(session),
        'user_authenticated': current_user.is_authenticated,
        'user_email': current_user.email if current_user.is_authenticated else None,
        'user_role': current_user.role.value if current_user.is_authenticated and current_user.role else None
    })

@test_bp.route('/first-user')
def test_first_user():
    """Test first user admin logic"""
    if not current_user.is_authenticated:
        return jsonify({'error': 'Not authenticated'})
    
    from models import User
    org_users = User.query.filter_by(organization_id=current_user.organization_id).count()
    is_first_user = org_users == 1 and current_user.role.value == 'Admin'
    
    return jsonify({
        'user_email': current_user.email,
        'organization_id': current_user.organization_id,
        'org_users_count': org_users,
        'user_role': current_user.role.value,
        'is_first_user': is_first_user,
        'unrestricted_admin': is_first_user
    })
