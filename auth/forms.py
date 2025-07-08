from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
from models import User, RoleEnum, Department
from flask_login import current_user
from utils.email_validation import validate_business_email, is_new_organization_domain, extract_domain
import pytz

class LoginForm(FlaskForm):
    """Login form"""
    class Meta:
        csrf = False
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    """Registration form"""
    class Meta:
        csrf = False
    name = StringField('Full Name', validators=[
        DataRequired(), 
        Length(min=2, max=100, message='Name must be between 2 and 100 characters')
    ])
    email = StringField('Email', validators=[
        DataRequired(), 
        Email(message='Please enter a valid email address'),
        Length(max=120)
    ])
    role = SelectField('Role', validators=[DataRequired()], 
                      choices=[
                          (RoleEnum.Staff.value, RoleEnum.Staff.value),
                          (RoleEnum.Manager.value, RoleEnum.Manager.value),
                          (RoleEnum.BA.value, RoleEnum.BA.value),
                          (RoleEnum.Director.value, RoleEnum.Director.value),
                          (RoleEnum.PM.value, RoleEnum.PM.value),
                          (RoleEnum.CEO.value, RoleEnum.CEO.value)
                          # Admin role excluded from registration for security
                      ])
    department_id = SelectField('Department', validators=[DataRequired()], coerce=int)
    reports_to = SelectField('Reports To', coerce=int, validators=[])
    
    # Organization fields (shown only for new email domains)
    organization_name = StringField('Organization Name', validators=[])
    industry = SelectField('Industry', validators=[], choices=[
        ('', 'Select Industry'),
        ('Technology', 'Technology'),
        ('Healthcare', 'Healthcare'),
        ('Finance', 'Finance & Banking'),
        ('Manufacturing', 'Manufacturing'),
        ('Retail', 'Retail & E-commerce'),
        ('Education', 'Education'),
        ('Government', 'Government & Public Sector'),
        ('Non-profit', 'Non-profit'),
        ('Consulting', 'Consulting'),
        ('Real Estate', 'Real Estate'),
        ('Other', 'Other')
    ])
    organization_size = SelectField('Organization Size', validators=[], choices=[
        ('', 'Select Size'),
        ('1-10', '1-10 employees'),
        ('11-50', '11-50 employees'),
        ('51-200', '51-200 employees'),
        ('201-1000', '201-1000 employees'),
        ('1000+', '1000+ employees')
    ])
    country = SelectField('Country', validators=[], choices=[
        ('', 'Select Country'),
        ('United States', 'United States'),
        ('United Kingdom', 'United Kingdom'),
        ('Canada', 'Canada'),
        ('Australia', 'Australia'),
        ('Germany', 'Germany'),
        ('France', 'France'),
        ('Netherlands', 'Netherlands'),
        ('Singapore', 'Singapore'),
        ('Japan', 'Japan'),
        ('Other', 'Other')
    ])
    
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    password2 = PasswordField('Repeat Password', validators=[
        DataRequired(), 
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Register')

    def __init__(self, email_domain=None, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        
        # Get organization_id for filtering based on email domain
        organization_id = None
        if email_domain:
            try:
                from models import Organization
                organization = Organization.query.filter_by(domain=email_domain).first()
                if organization:
                    organization_id = organization.id
            except Exception as e:
                # Handle database schema issues gracefully
                print(f"Warning: Could not check organization domain: {e}")
                organization_id = None
        
        # Populate department choices - filter by organization if available
        if organization_id:
            # Filter departments by organization (when Department model has organization_id)
            dept_choices = [(0, 'Select Department')] + [(-1, 'My department isn\'t listed - Contact Admin')]
        else:
            # For new organizations, show basic options
            dept_choices = [(0, 'Select Department')] + [(-1, 'My department isn\'t listed - Contact Admin')]
        
        self.department_id.choices = dept_choices
        
        # Populate reports_to choices - filter by organization if available  
        if organization_id:
            # Only show users from the same organization
            managers = User.query.filter_by(organization_id=organization_id).all()
            self.reports_to.choices = [(0, 'No Manager')] + [(u.id, u.name) for u in managers]
        else:
            # For new organizations, no existing managers
            self.reports_to.choices = [(0, 'No Manager')]

    def validate_email(self, email):
        """Check if email is already registered and is a valid business email"""
        # Check if email is already registered
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Email already registered. Please use a different email address.')
        
        # Validate business email
        is_valid, error_message = validate_business_email(email.data)
        if not is_valid:
            raise ValidationError(error_message)
        
        # If this is a new organization domain, require organization fields
        domain = extract_domain(email.data)
        if is_new_organization_domain(domain):
            # This validation will be checked in the route after form submission
            # to avoid circular dependency issues with form initialization
            pass

class ProfileForm(FlaskForm):
    """Profile management form"""
    class Meta:
        csrf = False
    name = StringField('Full Name', validators=[
        DataRequired(), 
        Length(min=2, max=100, message='Name must be between 2 and 100 characters')
    ])
    email = StringField('Email', validators=[
        DataRequired(), 
        Email(message='Please enter a valid email address'),
        Length(max=120)
    ])
    role = SelectField('Role', validators=[DataRequired()], 
                      choices=[
                          (RoleEnum.Staff.value, RoleEnum.Staff.value),
                          (RoleEnum.Manager.value, RoleEnum.Manager.value),
                          (RoleEnum.BA.value, RoleEnum.BA.value),
                          (RoleEnum.Director.value, RoleEnum.Director.value),
                          (RoleEnum.PM.value, RoleEnum.PM.value),
                          (RoleEnum.CEO.value, RoleEnum.CEO.value)
                          # Admin role excluded from profile changes for security
                      ])
    department_id = SelectField('Department', validators=[DataRequired()], coerce=int)
    reports_to = SelectField('Reports To', coerce=int, validators=[])
    timezone = SelectField('Timezone', validators=[], choices=[])
    theme = SelectField('Theme Preference', validators=[], 
                       choices=[
                           ('', 'Use Organization Default'),
                           ('light', 'Light Theme'),
                           ('dark', 'Dark Theme')
                       ])
    submit = SubmitField('Update Profile')

    def __init__(self, original_email=None, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.original_email = original_email
        # Filter departments and users by organization for existing users
        try:
            if current_user.is_authenticated and hasattr(current_user, 'organization_id') and current_user.organization_id:
                org_id = current_user.organization_id
                # Get departments used by users in the same organization
                dept_ids_in_org = db.session.query(User.dept_id).filter(
                    User.organization_id == org_id,
                    User.dept_id.isnot(None)
                ).distinct().all()
                dept_ids = [dept_id[0] for dept_id in dept_ids_in_org]
                departments = Department.query.filter(Department.id.in_(dept_ids)).all() if dept_ids else []
                self.department_id.choices = [(0, 'Select Department')] + [(d.id, d.name) for d in departments]
                self.reports_to.choices = [(0, 'No Manager')] + [(u.id, u.name) for u in User.query.filter_by(organization_id=org_id).all()]
            else:
                # For unauthenticated users or users without org, show empty lists
                self.department_id.choices = [(0, 'Select Department')]
                self.reports_to.choices = [(0, 'No Manager')]
        except Exception as e:
            # Fallback in case of any database errors
            print(f"ProfileForm initialization error: {e}")
            self.department_id.choices = [(0, 'Select Department')]
            self.reports_to.choices = [(0, 'No Manager')]
        
        # Populate timezone choices
        self.timezone.choices = self.get_timezone_choices()
    
    def get_timezone_choices(self):
        """Get list of timezone choices grouped by region"""
        common_timezones = [
            ('UTC', 'UTC (Coordinated Universal Time)'),
            ('US/Eastern', 'US Eastern Time'),
            ('US/Central', 'US Central Time'),
            ('US/Mountain', 'US Mountain Time'),
            ('US/Pacific', 'US Pacific Time'),
            ('Europe/London', 'London (GMT/BST)'),
            ('Europe/Paris', 'Paris (CET/CEST)'),
            ('Europe/Berlin', 'Berlin (CET/CEST)'),
            ('Asia/Tokyo', 'Tokyo (JST)'),
            ('Asia/Shanghai', 'Shanghai (CST)'),
            ('Asia/Kolkata', 'India (IST)'),
            ('Australia/Sydney', 'Sydney (AEST/AEDT)'),
        ]
        
        # Add blank option for "use organization default"
        choices = [('', 'Use Organization Default')] + common_timezones
        
        # Add all available timezones for advanced users
        all_timezones = [(tz, tz) for tz in pytz.common_timezones if tz not in [choice[0] for choice in common_timezones]]
        all_timezones.sort(key=lambda x: x[1])
        
        return choices + [('---', '--- All Timezones ---')] + all_timezones


class OrganizationSettingsForm(FlaskForm):
    """Organization-level regional settings form"""
    class Meta:
        csrf = False
    
    timezone = SelectField('Organization Default Timezone', validators=[DataRequired()], choices=[])
    currency = SelectField('Default Currency', validators=[DataRequired()], 
                          choices=[
                              ('USD', 'US Dollar (USD)'),
                              ('EUR', 'Euro (EUR)'),
                              ('GBP', 'British Pound (GBP)'),
                              ('CAD', 'Canadian Dollar (CAD)'),
                              ('AUD', 'Australian Dollar (AUD)'),
                              ('JPY', 'Japanese Yen (JPY)'),
                              ('CNY', 'Chinese Yuan (CNY)'),
                              ('INR', 'Indian Rupee (INR)'),
                          ])
    date_format = SelectField('Date Format', validators=[DataRequired()],
                             choices=[
                                 ('ISO', '2024-12-31 (ISO format)'),
                                 ('%m/%d/%Y', '12/31/2024 (US format)'),
                                 ('%d/%m/%Y', '31/12/2024 (EU format)'),
                                 ('%d-%m-%Y', '31-12-2024 (EU dashes)'),
                                 ('%B %d, %Y', 'December 31, 2024 (Full month)'),
                             ])
    time_format = SelectField('Time Format', validators=[DataRequired()],
                             choices=[
                                 ('%H:%M:%S', '23:59:59 (24-hour)'),
                                 ('%H:%M', '23:59 (24-hour, no seconds)'),
                                 ('%I:%M:%S %p', '11:59:59 PM (12-hour)'),
                                 ('%I:%M %p', '11:59 PM (12-hour, no seconds)'),
                             ])
    default_theme = SelectField('Organization Default Theme', validators=[DataRequired()],
                               choices=[
                                   ('light', 'Light Theme'),
                                   ('dark', 'Dark Theme')
                               ])
    submit = SubmitField('Update Organization Settings')
    
    def __init__(self, *args, **kwargs):
        super(OrganizationSettingsForm, self).__init__(*args, **kwargs)
        
        # Populate timezone choices (same as ProfileForm)
        self.timezone.choices = self.get_timezone_choices()
    
    def get_timezone_choices(self):
        """Get list of timezone choices grouped by region"""
        common_timezones = [
            ('UTC', 'UTC (Coordinated Universal Time)'),
            ('US/Eastern', 'US Eastern Time'),
            ('US/Central', 'US Central Time'),
            ('US/Mountain', 'US Mountain Time'),
            ('US/Pacific', 'US Pacific Time'),
            ('Europe/London', 'London (GMT/BST)'),
            ('Europe/Paris', 'Paris (CET/CEST)'),
            ('Europe/Berlin', 'Berlin (CET/CEST)'),
            ('Asia/Tokyo', 'Tokyo (JST)'),
            ('Asia/Shanghai', 'Shanghai (CST)'),
            ('Asia/Kolkata', 'India (IST)'),
            ('Australia/Sydney', 'Sydney (AEST/AEDT)'),
        ]
        
        # Add all available timezones for advanced users
        all_timezones = [(tz, tz) for tz in pytz.common_timezones if tz not in [choice[0] for choice in common_timezones]]
        all_timezones.sort(key=lambda x: x[1])
        
        return common_timezones + [('---', '--- All Timezones ---')] + all_timezones

    def validate_email(self, email):
        """Check if email is already registered (excluding current user)"""
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError('Email already registered. Please use a different email address.')
