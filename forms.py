"""
Main application forms for DeciFrame
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional


class WaitlistForm(FlaskForm):
    """Form for waitlist signups on the landing page"""
    
    first_name = StringField('First Name', [
        DataRequired(message='First name is required'),
        Length(min=1, max=50, message='First name must be between 1 and 50 characters')
    ])
    
    last_name = StringField('Last Name', [
        DataRequired(message='Last name is required'),
        Length(min=1, max=50, message='Last name must be between 1 and 50 characters')
    ])
    
    email = StringField('Email Address', [
        DataRequired(message='Email address is required'),
        Email(message='Please enter a valid email address'),
        Length(max=120, message='Email address must not exceed 120 characters')
    ])
    
    company = StringField('Company', [
        Optional(),
        Length(max=100, message='Company name must not exceed 100 characters')
    ])
    
    role = SelectField('Role', [
        DataRequired(message='Please select your role')
    ], choices=[
        ('', 'Select Your Role'),
        ('ceo', 'CEO / Executive'),
        ('cto', 'CTO / Technical Leader'),
        ('director', 'Director'),
        ('manager', 'Manager'),
        ('business_analyst', 'Business Analyst'),
        ('project_manager', 'Project Manager'),
        ('consultant', 'Consultant'),
        ('other', 'Other')
    ])
    
    company_size = SelectField('Company Size', [
        DataRequired(message='Please select your company size')
    ], choices=[
        ('', 'Select Company Size'),
        ('startup', 'Startup (1-10 employees)'),
        ('small', 'Small (11-50 employees)'),
        ('medium', 'Medium (51-200 employees)'),
        ('large', 'Large (201-1000 employees)'),
        ('enterprise', 'Enterprise (1000+ employees)')
    ])
    
    use_case = TextAreaField('Primary Use Case', [
        Optional(),
        Length(max=500, message='Use case description must not exceed 500 characters')
    ], description='Tell us about your biggest decision-making challenges and how you plan to use DeciFrame')
    
    class Meta:
        csrf = True