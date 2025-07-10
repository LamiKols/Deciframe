from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length
from models import Department, PriorityEnum, StatusEnum

def safe_int_coerce(value):
    """Safely coerce to int, handling None values"""
    if value is None or value == '' or value == 'None':
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

class ProblemForm(FlaskForm):
    class Meta:
        csrf = False
    
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[DataRequired()])
    priority = SelectField('Priority', coerce=str, choices=[(p.name, p.value) for p in PriorityEnum])
    department_id = SelectField('Department', coerce=safe_int_coerce, choices=[])

    status = SelectField('Status', coerce=str, choices=[
        (StatusEnum.Open.name, StatusEnum.Open.value),
        (StatusEnum.InProgress.name, StatusEnum.InProgress.value),
        (StatusEnum.Resolved.name, StatusEnum.Resolved.value),
        (StatusEnum.OnHold.name, StatusEnum.OnHold.value)
    ])
    issue_type = SelectField('Issue Type', coerce=str, choices=[
        ('PROCESS', 'Process Issue'),
        ('SYSTEM', 'System Issue'),
        ('OTHER', 'Other Issue')
    ], default='PROCESS')
    submit = SubmitField('Submit Problem')

    def __init__(self, *args, **kwargs):
        super(ProblemForm, self).__init__(*args, **kwargs)
        from flask_login import current_user
        
        # Populate department choices - filter by organization
        if current_user.is_authenticated:
            departments = Department.query.filter_by(organization_id=current_user.organization_id).all()
            self.department_id.choices = [(dept.id, dept.name) for dept in departments]
            
        else:
            self.department_id.choices = []

class ProblemFilterForm(FlaskForm):
    class Meta:
        csrf = False
    
    status = SelectField('Filter by Status', choices=[
        ('', 'All Statuses'),
        ('Open', 'Open'),
        ('In_Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
        ('On_Hold', 'On Hold')
    ])
    priority = SelectField('Filter by Priority', choices=[('', 'All Priorities')] + 
                          [(priority.value, priority.value) for priority in PriorityEnum])
    department_id = SelectField('Filter by Department', coerce=safe_int_coerce, choices=[])

    submit = SubmitField('Filter')

    def __init__(self, *args, **kwargs):
        super(ProblemFilterForm, self).__init__(*args, **kwargs)
        from flask_login import current_user
        
        # Populate department choices - filter by organization
        if current_user.is_authenticated:
            departments = Department.query.filter_by(organization_id=current_user.organization_id).all()
            self.department_id.choices = [(0, 'All Departments')] + [(dept.id, dept.name) for dept in departments]
            
        else:
            self.department_id.choices = [(0, 'All Departments')]