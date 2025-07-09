from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, SelectField, SubmitField, BooleanField, DecimalField
from wtforms.validators import DataRequired, Length, Optional
from models import StatusEnum, PriorityEnum, RoleEnum, User, Department, BusinessCase, OrgUnit
from app import db

def safe_int_coerce(value):
    """Safely coerce values to int, handling None and empty strings"""
    if value is None or value == '' or value == 'None':
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


class ProjectForm(FlaskForm):
    """Form for creating and editing projects"""
    class Meta:
        csrf = False
    
    name = StringField('Project Name', validators=[
        DataRequired(), 
        Length(min=3, max=200, message='Project name must be between 3 and 200 characters')
    ])
    description = TextAreaField('Description', validators=[Optional()])
    start_date = DateField('Start Date', validators=[Optional()])
    end_date = DateField('End Date', validators=[Optional()])
    budget = DecimalField('Budget', validators=[Optional()])
    status = SelectField('Status', validators=[DataRequired()], 
                        choices=[(status.value, status.value) for status in StatusEnum])
    priority = SelectField('Priority', validators=[DataRequired()], 
                          choices=[(priority.value, priority.value) for priority in PriorityEnum])
    business_case_id = SelectField('Linked Business Case', coerce=safe_int_coerce, validators=[Optional()])
    project_manager_id = SelectField('Project Manager', validators=[DataRequired()], coerce=safe_int_coerce)
    department_id = SelectField('Department', validators=[DataRequired()], coerce=safe_int_coerce)
    org_unit_id = SelectField('Organizational Unit', coerce=safe_int_coerce, validators=[Optional()])

    submit = SubmitField('Save Project')
    
    def __init__(self, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)
        
        # Populate business cases
        business_cases = BusinessCase.query.all()
        self.business_case_id.choices = [(0, 'No Business Case')] + [
            (bc.id, f"{bc.code} - {bc.title}") for bc in business_cases
        ]
        
        # Populate project managers (managers and above)
        managers = User.query.filter(
            User.role.in_([RoleEnum.Manager, RoleEnum.Director, RoleEnum.CEO, RoleEnum.PM])
        ).all()
        self.project_manager_id.choices = [
            (user.id, f"{user.name} ({user.role.value})") for user in managers
        ]
        
        # Populate departments with hierarchy - will be restricted by route logic
        self.department_id.choices = Department.get_hierarchical_choices()
        
        # Populate organizational units
        org_units = OrgUnit.query.all()
        self.org_unit_id.choices = [(0, 'No Organizational Unit')] + [
            (unit.id, unit.name) for unit in org_units
        ]



class MilestoneForm(FlaskForm):
    """Form for creating and editing project milestones"""
    class Meta:
        csrf = False
    
    name = StringField('Milestone Name', validators=[
        DataRequired(), 
        Length(min=3, max=200, message='Milestone name must be between 3 and 200 characters')
    ])
    description = TextAreaField('Description', validators=[Optional()])
    due_date = DateField('Due Date', validators=[DataRequired()])
    owner_id = SelectField('Owner', validators=[DataRequired()], coerce=safe_int_coerce)
    status = SelectField('Status', validators=[DataRequired()], choices=[
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold')
    ], default='open')
    completion_date = DateField('Completion Date', validators=[Optional()])
    completion_notes = TextAreaField('Completion Notes', validators=[Optional()])
    submit = SubmitField('Save Milestone')
    
    def __init__(self, project_id=None, *args, **kwargs):
        super(MilestoneForm, self).__init__(*args, **kwargs)
        
        # Populate milestone owners (all users) - filter by organization
        from flask_login import current_user
        users = User.query.filter_by(organization_id=current_user.organization_id).all()
        self.owner_id.choices = [
            (user.id, f"{user.name} ({user.org_unit.name if user.org_unit else 'No Unit'})") 
            for user in users
        ]


class ProjectFilterForm(FlaskForm):
    """Form for filtering projects"""
    class Meta:
        csrf = False
    
    status = SelectField('Filter by Status', choices=[('', 'All Statuses')] + 
                        [(status.value, status.value) for status in StatusEnum])
    priority = SelectField('Filter by Priority', choices=[('', 'All Priorities')] + 
                          [(priority.value, priority.value) for priority in PriorityEnum])
    department_id = SelectField('Filter by Department', coerce=safe_int_coerce, choices=[])
    project_manager_id = SelectField('Filter by Project Manager', coerce=safe_int_coerce, choices=[])

    submit = SubmitField('Filter')
    
    def __init__(self, *args, **kwargs):
        super(ProjectFilterForm, self).__init__(*args, **kwargs)
        
        # Populate departments with hierarchy
        self.department_id.choices = [(0, 'All Departments')] + Department.get_hierarchical_choices()
        
        # Populate project managers
        managers = User.query.filter(
            User.role.in_([RoleEnum.Manager, RoleEnum.Director, RoleEnum.CEO, RoleEnum.PM])
        ).all()
        self.project_manager_id.choices = [(0, 'All Project Managers')] + [
            (user.id, user.name) for user in managers
        ]
        
        # Populate organizational units
