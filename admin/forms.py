"""
Admin forms for DeciFrame
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, PasswordField, BooleanField, TextAreaField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange
from models import Department, RoleEnum

class UserForm(FlaskForm):
    """Form for creating and editing users"""
    name = StringField('Full Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    department = SelectField('Department', coerce=int, validators=[DataRequired()])
    role = SelectField('Role', choices=[(r.name, r.value) for r in RoleEnum], validators=[DataRequired()])
    password = PasswordField('Password', validators=[Optional(), Length(min=8)])
    is_active = BooleanField('Active')
    submit = SubmitField('Save')
    
    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        # Populate department choices with hierarchical structure
        self.department.choices = Department.get_hierarchical_choices()

class WorkflowTemplateForm(FlaskForm):
    """Form for creating and editing workflow templates"""
    name = StringField('Template Name', validators=[DataRequired(), Length(min=3, max=200)])
    description = TextAreaField('Description', validators=[DataRequired()])
    category = SelectField('Category', validators=[DataRequired()], choices=[
        ('Problem Management', 'Problem Management'),
        ('Case Management', 'Case Management'),
        ('Project Management', 'Project Management'),
        ('Human Resources', 'Human Resources'),
        ('IT Operations', 'IT Operations'),
        ('Finance', 'Finance'),
        ('Quality Assurance', 'Quality Assurance'),
        ('Communication', 'Communication'),
        ('Compliance', 'Compliance'),
        ('Procurement', 'Procurement'),
        ('Customer Service', 'Customer Service'),
        ('Security', 'Security')
    ])
    trigger_events = StringField('Trigger Events (comma-separated)', validators=[DataRequired()])
    is_active = BooleanField('Active Template', default=True)
    priority = IntegerField('Priority', validators=[DataRequired(), NumberRange(min=1, max=10)], default=5)

class SystemSettingForm(FlaskForm):
    """Form for system settings"""
    key = StringField('Setting Key', validators=[DataRequired(), Length(min=2, max=100)])
    value = TextAreaField('Setting Value', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    is_active = BooleanField('Active Setting', default=True)