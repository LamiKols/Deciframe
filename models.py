"""
DeciFrame Database Models
Comprehensive models for problem and business case management
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Enum as SQLEnum, Enum as SAEnum
import enum
import pytz

from app import db

# Enums for consistent data validation
class UserRoleEnum(enum.Enum):
    Staff = "Staff"
    Manager = "Manager"
    BA = "BA"  # Business Analyst
    Director = "Director"
    CEO = "CEO"
    PM = "PM"  # Project Manager
    Admin = "Admin"

RoleEnum = UserRoleEnum  # Alias for backward compatibility

class StatusEnum(enum.Enum):
    Open = "Open"
    In_Progress = "In Progress"
    InProgress = "InProgress"  # Database compatibility
    Resolved = "Resolved"
    On_Hold = "On Hold"
    OnHold = "OnHold"  # Database compatibility
    Approved = "Approved"
    Submitted = "Submitted"  # For review workflows
    Rejected = "Rejected"  # For review workflows
    Changes_Requested = "Changes Requested"  # For review workflows

class PriorityEnum(enum.Enum):
    High = "High"
    Medium = "Medium"
    Low = "Low"

class ImpactEnum(enum.Enum):
    High = "High"
    Medium = "Medium"
    Low = "Low"

class UrgencyEnum(enum.Enum):
    High = "High"
    Medium = "Medium"
    Low = "Low"

class IssueTypeEnum(enum.Enum):
    SYSTEM = "SYSTEM"
    PROCESS = "PROCESS" 
    OTHER = "OTHER"

class CaseTypeEnum(enum.Enum):
    Reactive = "Reactive"    # Problem-driven
    Proactive = "Proactive"  # Initiative-driven

class CaseDepthEnum(enum.Enum):
    Light = "Light"  # Basic cost/benefit analysis
    Full = "Full"    # Comprehensive business case

class NotificationEventEnum(enum.Enum):
    BUSINESS_CASE_APPROVED = "business_case_approved"
    PROBLEM_CREATED = "problem_created"
    PROJECT_CREATED = "project_created"
    MILESTONE_DUE_SOON = "milestone_due_soon"
    MILESTONE_OVERDUE = "milestone_overdue"
    TRIAGE_RULE_TRIGGERED = "triage_rule_triggered"
    ESCALATION = "escalation"

class ReportFrequencyEnum(enum.Enum):
    Daily = "Daily"
    Weekly = "Weekly"
    Monthly = "Monthly"
    Quarterly = "Quarterly"

class ReportTypeEnum(enum.Enum):
    DashboardSummary = "DashboardSummary"
    TrendReport = "TrendReport"
    RiskReport = "RiskReport"
    Custom = "Custom"

# Core Models
class Organization(db.Model):
    """
    Organization model for multi-tenant support
    Each organization has its own isolated data and settings
    """
    __tablename__ = 'organizations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    domain = db.Column(db.String(100), unique=True, nullable=False)  # Email domain for auto-assignment
    is_active = db.Column(db.Boolean, default=True)
    subscription_plan = db.Column(db.String(50), default='basic')  # basic, premium, enterprise
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', backref='organization', lazy=True)
    
    def __repr__(self):
        return f'<Organization {self.name}>'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.Enum(UserRoleEnum), default=UserRoleEnum.Staff)
    
    # Multi-tenant organization assignment
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    
    dept_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    department_status = db.Column(db.String(20), default='assigned')  # assigned, pending, requested
    
    # OAuth/SSO fields
    oauth_provider = db.Column(db.String(50), nullable=True)  # google, azure, okta, auth0
    oauth_sub = db.Column(db.String(200), nullable=True)  # OAuth subject identifier
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    profile_image_url = db.Column(db.String(500), nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Timezone settings - user-level timezone override
    timezone = db.Column(db.String(100), nullable=True)  # IANA timezone (e.g. 'America/New_York')
    
    # Theme settings - user-level theme preference
    theme = db.Column(db.String(10), default='light')  # 'light' or 'dark'
    
    # Onboarding status - tracks if user has completed welcome flow
    onboarded = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    department = db.relationship('Department', backref='users')
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    @property
    def manager(self):
        """Get the user's manager (user they report to)"""
        if hasattr(self, 'reports_to') and self.reports_to:
            return User.query.get(self.reports_to)
        return None
    
    @property
    def has_pending_department(self):
        """Check if user has pending department assignment"""
        return self.department_status == 'pending'
    
    @property
    def can_create_content(self):
        """Check if user can create problems, business cases, projects"""
        return self.dept_id is not None and self.department_status == 'assigned'
    
    def set_pending_department(self):
        """Set user to pending department status"""
        self.department_status = 'pending'
        self.dept_id = None
    
    def assign_department(self, dept_id):
        """Assign department and activate user"""
        self.dept_id = dept_id
        self.department_status = 'assigned'
    
    def get_effective_timezone(self):
        """Get user's effective timezone (user override > org default > UTC)"""
        if self.timezone:
            return self.timezone
        
        # Get organization timezone
        from models import OrganizationSettings
        org_timezone = OrganizationSettings.get_organization_timezone()
        return org_timezone or 'UTC'
    
    def get_effective_theme(self):
        """Get user's effective theme (user preference > org default > light)"""
        if hasattr(self, 'theme') and self.theme:
            return self.theme
        
        # Get organization default theme
        from models import OrganizationSettings
        org_settings = OrganizationSettings.get_organization_settings()
        return org_settings.default_theme if org_settings else 'light'
    
    def localize_datetime(self, utc_datetime):
        """Convert UTC datetime to user's local timezone"""
        if not utc_datetime:
            return None
            
        import pytz
        user_tz = pytz.timezone(self.get_effective_timezone())
        
        # Ensure UTC datetime is timezone-aware
        if utc_datetime.tzinfo is None:
            utc_datetime = pytz.UTC.localize(utc_datetime)
        
        return utc_datetime.astimezone(user_tz)
    
    def format_local_datetime(self, utc_datetime, format_string=None):
        """Format datetime in user's local timezone"""
        if not utc_datetime:
            return "Date unknown"
            
        local_dt = self.localize_datetime(utc_datetime)
        if not format_string:
            # Use ISO format as default to match organization preferences
            format_string = "%Y-%m-%d %H:%M:%S"
        
        return local_dt.strftime(format_string)
    
    def __repr__(self):
        return f'<User {self.id}: {self.name}>'

class Department(db.Model):
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    level = db.Column(db.Integer, default=1)  # Hierarchy level (1-5)
    parent_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Self-referencing relationship for hierarchy
    parent = db.relationship('Department', remote_side=[id], backref='children')
    
    def get_descendant_ids(self, include_self=True):
        """Get IDs of this department and all its sub-departments recursively"""
        ids = [self.id] if include_self else []
        for child in self.children:
            ids.extend(child.get_descendant_ids(include_self=True))
        return ids
    
    @staticmethod
    def get_hierarchical_choices():
        """Get all departments formatted for dropdown with hierarchy indentation"""
        def build_hierarchy(dept, level=0):
            """Recursively build hierarchical list"""
            indent = "—" * level
            display_name = f"{indent} {dept.name}" if level > 0 else dept.name
            choices = [(dept.id, display_name)]
            
            # Add children sorted by name
            for child in sorted(dept.children, key=lambda x: x.name):
                choices.extend(build_hierarchy(child, level + 1))
            return choices
        
        # Get all top-level departments (no parent)
        top_level = Department.query.filter_by(parent_id=None).order_by(Department.name).all()
        
        choices = []
        for dept in top_level:
            choices.extend(build_hierarchy(dept))
        
        return choices
    
    def __repr__(self):
        return f'<Department {self.id}: {self.name}>'

class Problem(db.Model):
    __tablename__ = 'problems'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=True)  # Auto-generated P0001, P0002...
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum(StatusEnum), default=StatusEnum.Open)
    priority = db.Column(db.Enum(PriorityEnum), default=PriorityEnum.Medium)
    impact = db.Column(db.Enum(ImpactEnum), default=ImpactEnum.Medium)
    urgency = db.Column(db.Enum(UrgencyEnum), default=UrgencyEnum.Medium)
    reported_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # AI Classification fields
    issue_type = db.Column(
        SQLEnum('SYSTEM', 'PROCESS', 'OTHER', name='issue_type_enum'),
        nullable=False,
        default='PROCESS'
    )
    ai_confidence = db.Column(db.Float, nullable=True)
    
    # Full-text search vector
    search_vector = db.Column(db.Text)  # tsvector for full-text search
    
    # Relationships
    reporter = db.relationship('User', foreign_keys=[reported_by])
    assignee = db.relationship('User', foreign_keys=[assigned_to])
    department = db.relationship('Department')
    
    def __repr__(self):
        return f'<Problem {self.code}: {self.title}>'

class BusinessCase(db.Model):
    __tablename__ = 'business_cases'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=True)  # Auto-generated C0001, C0002...
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    summary = db.Column(db.Text, nullable=True)  # AI-generated executive summary
    status = db.Column(db.Enum(StatusEnum), default=StatusEnum.Open)
    case_type = db.Column(db.Enum(CaseTypeEnum), default=CaseTypeEnum.Reactive)
    case_depth = db.Column(db.Enum(CaseDepthEnum), default=CaseDepthEnum.Light)
    
    # Financial data
    cost_estimate = db.Column(db.Float, nullable=False)
    benefit_estimate = db.Column(db.Float, nullable=False)
    roi = db.Column(db.Float)  # Calculated automatically
    
    # Full Case fields
    strategic_alignment = db.Column(db.Text, nullable=True)
    benefit_breakdown = db.Column(db.Text, nullable=True)
    risk_mitigation = db.Column(db.Text, nullable=True)
    stakeholder_analysis = db.Column(db.Text, nullable=True)
    dependencies = db.Column(db.Text, nullable=True)
    roadmap = db.Column(db.Text, nullable=True)
    sensitivity_analysis = db.Column(db.Text, nullable=True)
    initiative_name = db.Column(db.String(200), nullable=True)
    
    # Full case request tracking
    full_case_requested = db.Column(db.Boolean, default=False)
    full_case_requested_at = db.Column(db.DateTime, nullable=True)
    full_case_requested_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Submission tracking
    submitted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    submitted_at = db.Column(db.DateTime, nullable=True)
    
    # Approval tracking
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), nullable=True)
    solution_id = db.Column(db.Integer, db.ForeignKey('solutions.id'), nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)  # Set when approved and project created
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    dept_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    assigned_ba = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    assigned_ba_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Legacy field
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Full-text search vector
    search_vector = db.Column(db.Text)  # tsvector for full-text search
    
    # Relationships
    problem = db.relationship('Problem', backref='business_cases')
    solution = db.relationship('Solution', backref='business_cases')
    project = db.relationship('Project', foreign_keys=[project_id])
    department = db.relationship('Department')
    creator = db.relationship('User', foreign_keys=[created_by])
    business_analyst = db.relationship('User', foreign_keys=[assigned_ba])
    submitter = db.relationship('User', foreign_keys=[submitted_by])
    approver = db.relationship('User', foreign_keys=[approved_by])
    
    def calculate_roi(self):
        """Calculate ROI as (benefit - cost) / cost * 100"""
        if self.cost_estimate and self.cost_estimate > 0:
            self.roi = ((self.benefit_estimate - self.cost_estimate) / self.cost_estimate) * 100
        else:
            self.roi = 0

class BusinessCaseComment(db.Model):
    __tablename__ = 'business_case_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('business_cases.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    case = db.relationship('BusinessCase', backref='comments')
    author = db.relationship('User')
    
    def __repr__(self):
        return f'<BusinessCaseComment {self.id}: {self.content[:50]}...>'

class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    budget = db.Column(db.Float)
    status = db.Column(db.Enum(StatusEnum), default=StatusEnum.Open)
    priority = db.Column(db.Enum(PriorityEnum), default=PriorityEnum.Medium)
    business_case_id = db.Column(db.Integer, db.ForeignKey('business_cases.id'), nullable=True)
    project_manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Review fields
    submitted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    submitted_at = db.Column(db.DateTime, nullable=True)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    
    # Full-text search vector
    search_vector = db.Column(db.Text)  # tsvector for full-text search
    
    # Relationships
    business_case = db.relationship('BusinessCase', foreign_keys=[business_case_id], backref='projects')
    project_manager = db.relationship('User', foreign_keys=[project_manager_id])
    department = db.relationship('Department')
    creator = db.relationship('User', foreign_keys=[created_by])
    submitter = db.relationship('User', foreign_keys=[submitted_by])
    approver = db.relationship('User', foreign_keys=[approved_by])
    epics = db.relationship('Epic', backref='project')
    stories = db.relationship('Story', backref='project')
    
    @classmethod
    def upcoming_milestones(cls, days=30):
        """Fetch milestones due in next N days"""
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.utcnow().date() + timedelta(days=days)
        today = datetime.utcnow().date()
        
        return ProjectMilestone.query.filter(
            ProjectMilestone.due_date >= today,
            ProjectMilestone.due_date <= cutoff_date,
            ProjectMilestone.completed == False
        ).order_by(ProjectMilestone.due_date).all()

class ProjectMilestone(db.Model):
    __tablename__ = 'project_milestones'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.Date, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    completion_date = db.Column(db.Date)
    completion_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', backref='milestones')
    owner = db.relationship('User')

class ProjectComment(db.Model):
    __tablename__ = 'project_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', backref='comments')
    author = db.relationship('User')
    
    def __repr__(self):
        return f'<ProjectComment {self.id}: {self.content[:50]}...>'

# Auto-generate problem code using SQLAlchemy event
from sqlalchemy import event

@event.listens_for(Problem, 'before_insert')
def generate_problem_code(mapper, connection, target):
    """Auto-generate problem code in format P0001, P0002, etc."""
    if not target.code:
        # Get the next sequence number based on existing problems
        result = connection.execute(
            db.text("SELECT COUNT(*) + 1 FROM problems")
        ).scalar()
        target.code = "P%04d" % result

# Notification Models
class NotificationTemplate(db.Model):
    __tablename__ = 'notification_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    event = db.Column(db.Enum(NotificationEventEnum), nullable=False, unique=True)
    subject = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    email_enabled = db.Column(db.Boolean, default=True)
    in_app_enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<NotificationTemplate {self.event.value}>'

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(200), nullable=True)
    read_flag = db.Column(db.Boolean, default=False)
    event_type = db.Column(db.Enum(NotificationEventEnum), nullable=False)
    email_sent = db.Column(db.Boolean, default=False)
    email_sent_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='notifications')
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.read_flag = True
        db.session.commit()
    
    def __repr__(self):
        return f'<Notification {self.id}: {self.event_type.value}>'

from flask_login import LoginManager
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    print(f"🔍 User loader called with ID: {user_id}")
    try:
        user = User.query.get(int(user_id))
        print(f"🔍 User loader found user: {user is not None}")
        if user:
            print(f"🔍 User loader returning: {user.name} ({user.email})")
        return user
    except Exception as e:
        print(f"🔍 User loader error: {e}")
        return None

class ReportTemplate(db.Model):
    __tablename__ = 'report_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    frequency = db.Column(db.Enum(ReportFrequencyEnum), nullable=False)
    template_type = db.Column(db.Enum(ReportTypeEnum), nullable=False)
    last_run_at = db.Column(db.DateTime, nullable=True)
    mailing_list = db.Column(db.Text, nullable=True)  # JSON list of user IDs/roles
    filters = db.Column(db.Text, nullable=True)  # JSON filters for report data
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)
    
    creator = db.relationship('User', foreign_keys=[created_by])
    
    def __repr__(self):
        return f'<ReportTemplate {self.id}: {self.name}>'

class RequirementsBackup(db.Model):
    """Store successful AI-generated requirements to prevent data loss"""
    __tablename__ = 'requirements_backups'
    
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('business_cases.id'), nullable=False)
    answers_json = db.Column(db.Text, nullable=False)  # JSON-encoded 8 answers
    epics_json = db.Column(db.Text, nullable=False)    # JSON-encoded generated epics
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    business_case = db.relationship('BusinessCase', backref='requirements_backups')
    creator = db.relationship('User', foreign_keys=[created_by])
    
    def __repr__(self):
        return f'<RequirementsBackup {self.id}: Case {self.case_id}>'

class ReportRun(db.Model):
    __tablename__ = 'report_runs'
    
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('report_templates.id'), nullable=False)
    run_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='Success')
    file_path = db.Column(db.String(500), nullable=True)
    email_recipients = db.Column(db.Text, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    
    template = db.relationship('ReportTemplate', backref='runs')
    
    def __repr__(self):
        return f'<ReportRun {self.id}: {self.template.name} at {self.run_date}>'

# Epic and Story models for AI-generated requirements
class Epic(db.Model):
    __tablename__ = 'epics'
    
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('business_cases.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)  # Set when case approved
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Draft')  # Draft, Submitted, Approved, Rejected
    comments = db.Column(db.Text)
    assigned_by = db.Column(db.String(100))  # Placeholder for now (name or email)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Review workflow fields
    submitted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    submitted_at = db.Column(db.DateTime, nullable=True)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    business_case = db.relationship('BusinessCase', backref='epics')
    creator = db.relationship('User', foreign_keys=[creator_id])
    submitter = db.relationship('User', foreign_keys=[submitted_by])
    approver = db.relationship('User', foreign_keys=[approved_by])
    
    @property
    def comments(self):
        """Get comments for this epic"""
        return self.epic_comments
    
    def to_dict(self, include_stories=False):
        """Convert epic to dictionary with optional stories"""
        result = {
            'id': self.id,
            'case_id': self.case_id,
            'project_id': self.project_id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'comments': self.comments,
            'assigned_by': self.assigned_by,
            'creator_id': self.creator_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_stories:
            result['stories'] = [story.to_dict() for story in self.stories]
        return result
    
    def __repr__(self):
        return f'<Epic {self.id}: {self.title}>'

class EpicComment(db.Model):
    __tablename__ = 'epic_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    epic_id = db.Column(db.Integer, db.ForeignKey('epics.id', ondelete='CASCADE'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Legacy field for backwards compatibility
    author = db.Column(db.String(100), nullable=True)
    message = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    epic = db.relationship('Epic', backref=db.backref('epic_comments', cascade='all, delete-orphan'))
    author_user = db.relationship('User', foreign_keys=[author_id])
    
    def to_dict(self):
        """Convert comment to dictionary"""
        return {
            'id': self.id,
            'epic_id': self.epic_id,
            'author_id': self.author_id,
            'author_name': self.author_user.name if self.author_user else self.author,
            'content': self.content or self.message,
            'created_at': self.created_at.isoformat() if self.created_at else (self.timestamp.isoformat() if self.timestamp else None)
        }
    
    def __repr__(self):
        return f'<EpicComment {self.id} by {self.author_user.name if self.author_user else self.author}>'

class EpicSyncLog(db.Model):
    __tablename__ = 'epic_sync_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    epic_id = db.Column(db.Integer, db.ForeignKey('epics.id', ondelete='CASCADE'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    action = db.Column(db.String(50), nullable=False)  # 'synced', 'unsynced', 'rollback'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    epic = db.relationship('Epic', backref=db.backref('sync_logs', cascade='all, delete-orphan'))
    project = db.relationship('Project', backref='epic_sync_logs')
    
    def to_dict(self):
        """Convert sync log to dictionary"""
        return {
            'id': self.id,
            'epic_id': self.epic_id,
            'project_id': self.project_id,
            'action': self.action,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
    
    def __repr__(self):
        return f'<EpicSyncLog {self.id}: Epic {self.epic_id} {self.action} to Project {self.project_id}>'

class Story(db.Model):
    __tablename__ = 'stories'
    
    id = db.Column(db.Integer, primary_key=True)
    epic_id = db.Column(db.Integer, db.ForeignKey('epics.id', ondelete='CASCADE'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    acceptance_criteria = db.Column(db.Text, nullable=True)  # JSON-encoded list
    priority = db.Column(db.String(20), default='Medium')
    effort_estimate = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    epic = db.relationship('Epic', backref=db.backref('stories', cascade='all, delete-orphan'))
    
    def to_dict(self):
        """Convert story to dictionary"""
        return {
            'id': self.id,
            'epic_id': self.epic_id,
            'project_id': self.project_id,
            'title': self.title,
            'description': self.description,
            'acceptance_criteria': self.acceptance_criteria,
            'priority': self.priority,
            'effort_estimate': self.effort_estimate,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Story {self.id}: {self.title}>'

# Solution model for problem-solution tracking
class Solution(db.Model):
    __tablename__ = 'solutions'
    
    id = db.Column(db.Integer, primary_key=True)
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), nullable=False)
    name = db.Column(db.String(200), nullable=True)  # Database field for compatibility
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum(StatusEnum), default=StatusEnum.Open)
    priority = db.Column(db.Enum(PriorityEnum), default=PriorityEnum.Medium)
    estimated_cost = db.Column(db.Float, nullable=True)
    estimated_effort = db.Column(db.String(50), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    problem = db.relationship('Problem', backref='solutions')
    creator = db.relationship('User', foreign_keys=[created_by])
    assignee = db.relationship('User', foreign_keys=[assigned_to])
    
    def __repr__(self):
        return f'<Solution {self.id}: {self.title}>'


class PredictionFeedback(db.Model):
    """Feedback for ML prediction accuracy tracking"""
    __tablename__ = 'prediction_feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    prediction_type = db.Column(db.String(50), nullable=False)  # 'success', 'cycle_time', 'anomaly'
    entity_id = db.Column(db.Integer, nullable=False)  # Project/Case ID
    predicted_value = db.Column(db.Float, nullable=True)
    actual_value = db.Column(db.Float, nullable=True)
    feedback_score = db.Column(db.Integer, nullable=True)  # 1-5 rating
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    creator = db.relationship('User', foreign_keys=[created_by])


class AIThresholdSettings(db.Model):
    """AI service threshold and configuration settings"""
    __tablename__ = 'ai_threshold_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    setting_name = db.Column(db.String(100), unique=True, nullable=False)
    threshold_value = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    updater = db.relationship('User', foreign_keys=[updated_by])

class OrgUnit(db.Model):
    __tablename__ = 'org_units'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('org_units.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Self-referential relationship for hierarchy
    children = db.relationship(
        'OrgUnit',
        backref=db.backref('parent', remote_side=[id]),
        cascade='all, delete-orphan'
    )
    
    # Manager relationship
    manager = db.relationship('User', foreign_keys=[manager_id])
    
    # Organization relationship
    organization = db.relationship('Organization', foreign_keys=[organization_id])
    
    def __repr__(self):
        return f'<OrgUnit {self.name}>'
    
    def get_hierarchy_level(self):
        """Return the depth level in the org chart (0 = root)"""
        level = 0
        current = self.parent
        while current:
            level += 1
            current = current.parent
        return level
    
    def get_level(self):
        """Alias for get_hierarchy_level() for form compatibility"""
        return self.get_hierarchy_level()
    
    def get_full_path(self):
        """Return full organizational path (e.g., 'Company > IT > Development')"""
        path = [self.name]
        current = self.parent
        while current:
            path.insert(0, current.name)
            current = current.parent
        return ' > '.join(path)
    
    def get_all_descendants(self):
        """Return all descendant org units recursively"""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants

class Setting(db.Model):
    __tablename__ = 'settings'
    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.String(500), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class RolePermission(db.Model):
    __tablename__ = 'role_permissions'
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.Enum(RoleEnum), nullable=False)
    module = db.Column(db.String(50), nullable=False)  # e.g. 'BusinessCase'
    can_create = db.Column(db.Boolean, default=False)
    can_read = db.Column(db.Boolean, default=False)
    can_update = db.Column(db.Boolean, default=False)
    can_delete = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('role', 'module', name='_role_module_uc'),
    )

class WorkflowTemplate(db.Model):
    __tablename__ = 'workflow_templates'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=True)
    definition = db.Column(db.JSON, nullable=False)  # JSON array of steps
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    creator = db.relationship('User', backref='workflow_templates')

class WorkflowLibrary(db.Model):
    __tablename__ = 'workflow_library'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(200))
    definition = db.Column(db.JSON, nullable=False)
    category = db.Column(db.String(50))  # e.g. "Problem Management", "Case Approval"

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(200), nullable=False)
    module = db.Column(db.String(100), nullable=True)  # Module/blueprint name
    target = db.Column(db.String(200), nullable=True)
    target_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.JSON, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='audit_logs')

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    status = db.Column(db.Enum(StatusEnum), default=StatusEnum.Open)
    priority = db.Column(db.Enum(PriorityEnum), default=PriorityEnum.Medium)
    due_date = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    assignee = db.relationship('User', foreign_keys=[assigned_to], backref='assigned_tasks')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_tasks')

class ScheduledTask(db.Model):
    __tablename__ = 'scheduled_tasks'
    id = db.Column(db.Integer, primary_key=True)
    task_type = db.Column(db.String(100), nullable=False)
    scheduled_for = db.Column(db.DateTime, nullable=False)
    context_data = db.Column(db.JSON, nullable=True)
    status = db.Column(db.String(20), default='Pending')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    executed_at = db.Column(db.DateTime, nullable=True)
    result = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    creator = db.relationship('User', backref='scheduled_tasks')

class WorkflowExecution(db.Model):
    __tablename__ = 'workflow_executions'
    id = db.Column(db.Integer, primary_key=True)
    workflow_template_id = db.Column(db.Integer, db.ForeignKey('workflow_templates.id'), nullable=False)
    event_name = db.Column(db.String(100), nullable=False)
    context_data = db.Column(db.JSON, nullable=True)
    status = db.Column(db.String(20), default='Started')
    steps_executed = db.Column(db.JSON, nullable=True)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    
    workflow_template = db.relationship('WorkflowTemplate', backref='executions')

class ImportJob(db.Model):
    __tablename__ = 'import_jobs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    data_type = db.Column(db.Enum('Problem', 'BusinessCase', 'Project', name='data_type'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    status = db.Column(db.Enum('Pending', 'Mapping', 'Importing', 'Complete', 'Failed', name='import_status'), default='Pending')
    mapping = db.Column(db.JSON, nullable=True)  # { model_field: column_name }
    rows_success = db.Column(db.Integer, default=0)
    rows_failed = db.Column(db.Integer, default=0)
    error_details = db.Column(db.JSON, nullable=True)  # [{row: int, error: str}, ...]
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='import_jobs')

class HelpCategory(db.Model):
    __tablename__ = 'help_categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<HelpCategory {self.name}>'

class HelpArticle(db.Model):
    __tablename__ = 'help_articles'
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('help_categories.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)  # Store Markdown or HTML
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    category = db.relationship('HelpCategory', backref='articles')
    author = db.relationship('User', backref='help_articles')
    
    def generate_slug(self):
        """Auto-generate slug from title"""
        import re
        # Convert to lowercase and replace spaces/special chars with hyphens
        slug = re.sub(r'[^a-zA-Z0-9\s-]', '', self.title.lower())
        slug = re.sub(r'[\s-]+', '-', slug).strip('-')
        
        # Ensure uniqueness
        base_slug = slug
        counter = 1
        while HelpArticle.query.filter_by(slug=slug).filter(HelpArticle.id != self.id).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug
    
    def __repr__(self):
        return f'<HelpArticle {self.title}>'


class FrequencyEnum(enum.Enum):
    immediate = "immediate"
    hourly = "hourly"
    daily = "daily"
    weekly = "weekly"


class NotificationSetting(db.Model):
    __tablename__ = 'notification_settings'
    id = db.Column(db.Integer, primary_key=True)
    event_name = db.Column(db.String(100), unique=True, nullable=False)
    frequency = db.Column(db.Enum(FrequencyEnum), nullable=False, default=FrequencyEnum.immediate)
    threshold_hours = db.Column(db.Integer, nullable=True)  # for escalation after X hours
    channel_email = db.Column(db.Boolean, default=True)
    channel_in_app = db.Column(db.Boolean, default=True)
    channel_push = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<NotificationSetting {self.event_name}: {self.frequency.value}>'


# Data Export & Retention Models

class RetentionLog(db.Model):
    __tablename__ = 'retention_logs'
    id = db.Column(db.Integer, primary_key=True)
    table_name = db.Column(db.String(50), nullable=False)
    cutoff = db.Column(db.DateTime, nullable=False)
    row_count = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    creator = db.relationship('User', backref='retention_logs')
    
    def __repr__(self):
        return f'<RetentionLog {self.table_name}: {self.row_count} rows archived>'


class ExportJob(db.Model):
    __tablename__ = 'export_jobs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    table_name = db.Column(db.String(50), nullable=False)
    format = db.Column(db.String(10), nullable=False)  # 'csv', 'json', 'excel'
    filters = db.Column(db.JSON, nullable=True)  # Filter criteria applied
    status = db.Column(db.String(20), default='Pending')  # Pending, Processing, Complete, Failed
    file_path = db.Column(db.String(500), nullable=True)  # Path to generated file
    row_count = db.Column(db.Integer, nullable=True)
    file_size = db.Column(db.Integer, nullable=True)  # Size in bytes
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    user = db.relationship('User', backref='export_jobs')
    
    def __repr__(self):
        return f'<ExportJob {self.table_name} ({self.format}): {self.status}>'


# Archived Data Tables - Mirror schemas of main tables

class ArchivedProblem(db.Model):
    __tablename__ = 'archived_problems'
    id = db.Column(db.Integer, primary_key=True)
    original_id = db.Column(db.Integer, nullable=False)  # Reference to original problem ID
    problem_code = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum(StatusEnum), nullable=False)
    priority = db.Column(db.Enum(PriorityEnum), nullable=False)
    impact = db.Column(db.Enum(ImpactEnum), nullable=False)
    urgency = db.Column(db.Enum(UrgencyEnum), nullable=False)
    dept_id = db.Column(db.Integer, nullable=True)
    created_by = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)
    resolved_at = db.Column(db.DateTime, nullable=True)
    archived_at = db.Column(db.DateTime, default=datetime.utcnow)
    archived_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    archiver = db.relationship('User', backref='archived_problems')


class ArchivedBusinessCase(db.Model):
    __tablename__ = 'archived_business_cases'
    id = db.Column(db.Integer, primary_key=True)
    original_id = db.Column(db.Integer, nullable=False)
    case_code = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    status = db.Column(db.Enum(StatusEnum), nullable=False)
    problem_id = db.Column(db.Integer, nullable=True)
    solution = db.Column(db.Text, nullable=True)
    business_value = db.Column(db.Numeric(12, 2), nullable=True)
    estimated_cost = db.Column(db.Numeric(12, 2), nullable=True)
    roi_percentage = db.Column(db.Numeric(5, 2), nullable=True)
    created_by = db.Column(db.Integer, nullable=False)
    assigned_to = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)
    approved_at = db.Column(db.DateTime, nullable=True)
    approved_by = db.Column(db.Integer, nullable=True)
    archived_at = db.Column(db.DateTime, default=datetime.utcnow)
    archived_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    archiver = db.relationship('User', backref='archived_business_cases')


class ArchivedProject(db.Model):
    __tablename__ = 'archived_projects'
    id = db.Column(db.Integer, primary_key=True)
    original_id = db.Column(db.Integer, nullable=False)
    project_code = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.Enum(StatusEnum), nullable=False)
    priority = db.Column(db.Enum(PriorityEnum), nullable=False)
    case_id = db.Column(db.Integer, nullable=True)
    budget = db.Column(db.Numeric(12, 2), nullable=True)
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    completion_percentage = db.Column(db.Integer, default=0)
    department_id = db.Column(db.Integer, nullable=True)
    project_manager_id = db.Column(db.Integer, nullable=True)
    created_by = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    archived_at = db.Column(db.DateTime, default=datetime.utcnow)
    archived_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    archiver = db.relationship('User', backref='archived_projects')


class DataRetentionPolicy(db.Model):
    __tablename__ = 'data_retention_policies'
    id = db.Column(db.Integer, primary_key=True)
    table_name = db.Column(db.String(50), unique=True, nullable=False)
    retention_months = db.Column(db.Integer, nullable=False)  # How long to keep data
    archive_enabled = db.Column(db.Boolean, default=True)  # Whether to archive before deletion
    auto_cleanup = db.Column(db.Boolean, default=False)  # Automatic scheduled cleanup
    last_cleanup = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    updater = db.relationship('User', backref='retention_policies')
    
    def __repr__(self):
        return f'<DataRetentionPolicy {self.table_name}: {self.retention_months} months>'


class Waitlist(db.Model):
    """Model for storing landing page waitlist signups"""
    __tablename__ = 'waitlist'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    company = db.Column(db.String(100), nullable=True)
    role = db.Column(db.String(50), nullable=True)
    company_size = db.Column(db.String(50), nullable=True)
    use_case = db.Column(db.Text, nullable=True)
    
    # Legacy fields for backward compatibility
    name = db.Column(db.String(100), nullable=True)  # Computed from first_name + last_name
    phone = db.Column(db.String(20), nullable=True)
    message = db.Column(db.Text, nullable=True)  # Alias for use_case
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 support
    user_agent = db.Column(db.String(500), nullable=True)
    
    # Status tracking
    contacted = db.Column(db.Boolean, default=False)
    contacted_at = db.Column(db.DateTime, nullable=True)
    contacted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    contact_user = db.relationship('User', backref='waitlist_contacts')
    
    @property
    def full_name(self):
        """Get full name from first_name and last_name"""
        return f"{self.first_name} {self.last_name}".strip()
    
    def __repr__(self):
        return f'<Waitlist {self.full_name} <{self.email}>>'

# Timezone and Regional Settings
class OrganizationSettings(db.Model):
    """
    Organization-level settings for timezone, currency, and regional preferences
    """
    __tablename__ = 'organization_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    
    # Timezone and regional settings
    timezone = db.Column(db.String(100), default='UTC')  # IANA timezone (e.g. 'America/New_York')
    currency = db.Column(db.String(10), default='USD')  # ISO currency code
    date_format = db.Column(db.String(20), default='ISO')  # strftime format or 'ISO'
    time_format = db.Column(db.String(20), default='%H:%M:%S')  # strftime format
    
    # Theme settings - organization-level default theme
    default_theme = db.Column(db.String(10), default='light')  # 'light' or 'dark'
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    updater = db.relationship('User', backref='organization_settings_updates')
    
    @classmethod
    def get_organization_timezone(cls, organization_id=None):
        """Get the organization's default timezone"""
        if not organization_id and hasattr(current_user, 'organization_id'):
            organization_id = current_user.organization_id
        if not organization_id:
            organization_id = 1  # Fallback for backwards compatibility
        settings = cls.query.filter_by(organization_id=organization_id).first()
        return settings.timezone if settings else 'UTC'
    
    @classmethod
    def get_organization_settings(cls, organization_id=None):
        """Get or create organization settings"""
        from flask_login import current_user
        if not organization_id and hasattr(current_user, 'organization_id') and current_user.organization_id:
            organization_id = current_user.organization_id
        if not organization_id:
            organization_id = 1  # Fallback for backwards compatibility
            
        settings = cls.query.filter_by(organization_id=organization_id).first()
        if not settings:
            # Create default settings for this organization
            settings = cls(
                organization_id=organization_id,
                timezone='UTC',
                currency='USD',
                date_format='ISO',
                time_format='%H:%M:%S',
                default_theme='light'
            )
            db.session.add(settings)
            db.session.commit()
        return settings
    
    def get_currency_symbol(self):
        """Get currency symbol for the current currency setting"""
        currency_symbols = {
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
            'CAD': 'C$',
            'AUD': 'A$',
            'JPY': '¥',
            'CNY': '¥',
            'INR': '₹'
        }
        return currency_symbols.get(self.currency, '$')
    
    @classmethod
    def get_current(cls):
        """Get current organization settings (alias for get_organization_settings)"""
        return cls.get_organization_settings()
    
    def __repr__(self):
        return f'<OrganizationSettings organization_id={self.organization_id} timezone={self.timezone}>'


class TriageRule(db.Model):
    """
    Automated triage rules for workflow management.
    Allows admins to define conditions that trigger automated actions.
    """
    __tablename__ = 'triage_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    target = db.Column(db.String(50), nullable=False)  # 'Epic', 'BusinessCase', 'Project'
    field = db.Column(db.String(50), nullable=False)   # e.g. 'estimated_cost', 'classification', 'created_at'
    operator = db.Column(db.String(10), nullable=False)  # '=', '>', '<', 'contains', 'days_ago'
    value = db.Column(db.String(100), nullable=False)    # '5000', 'System', '7'
    action = db.Column(db.String(50), nullable=False)    # 'auto_approve', 'flag', 'notify_admin'
    message = db.Column(db.String(255))  # Custom message/log entry
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    creator = db.relationship('User', backref='created_triage_rules')
    
    def __repr__(self):
        return f'<TriageRule {self.name}: {self.target}.{self.field} {self.operator} {self.value} -> {self.action}>'
    
    @classmethod
    def get_active_rules(cls):
        """Get all active triage rules"""
        return cls.query.filter_by(active=True).all()
    
    def to_dict(self):
        """Convert rule to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'target': self.target,
            'field': self.field,
            'operator': self.operator,
            'value': self.value,
            'action': self.action,
            'message': self.message,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by
        }