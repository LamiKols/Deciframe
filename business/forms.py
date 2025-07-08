from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DecimalField, SubmitField, RadioField, HiddenField
from wtforms.validators import DataRequired, Length, Optional
from models import Problem, StatusEnum, CaseTypeEnum, CaseDepthEnum, OrgUnit

class BusinessCaseForm(FlaskForm):
    case_type = RadioField(
        'Case Type',
        choices=[('Reactive', 'Reactive'), ('Proactive', 'Proactive')],
        default='Reactive'
    )
    case_depth = RadioField(
        'Case Depth',
        choices=[('Light', 'Light Case'), ('Full', 'Full Case')],
        default='Light'
    )
    
    # Core fields (Light case)
    initiative_name = StringField('Initiative Name')
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    summary = TextAreaField('Summary', validators=[Optional()])
    description = TextAreaField('Description', validators=[DataRequired()])
    problem = SelectField('From Problem', coerce=int, choices=[])

    cost_estimate = DecimalField('Cost Estimate', validators=[DataRequired()])
    benefit_estimate = DecimalField('Benefit Estimate', validators=[DataRequired()])
    
    # Solution integration fields
    solution_id = HiddenField()
    solution_description = TextAreaField('Solution Description', render_kw={'readonly': True})
    
    # Full case elaboration fields
    strategic_alignment = TextAreaField('Strategic Alignment', validators=[Optional()])
    benefit_breakdown = TextAreaField('Benefit Breakdown', validators=[Optional()])
    risk_mitigation = TextAreaField('Risk & Mitigation', validators=[Optional()])
    stakeholder_analysis = TextAreaField('Stakeholder Analysis', validators=[Optional()])
    dependencies = TextAreaField('Dependencies', validators=[Optional()])
    roadmap = TextAreaField('Implementation Roadmap', validators=[Optional()])
    sensitivity_analysis = TextAreaField('Sensitivity Analysis', validators=[Optional()])
    
    submit = SubmitField('Create Business Case')


class AssignBAForm(FlaskForm):
    assigned_ba = SelectField(
        'Assign Business Analyst',
        coerce=int,
        validators=[DataRequired()]
    )
    submit = SubmitField('Assign to BA')
        # Don't populate choices here - they're set in the route handler

class BusinessCaseFilterForm(FlaskForm):
    status = SelectField('Filter by Status', choices=[('', 'All Statuses')] + 
                        [(status.value, status.value) for status in StatusEnum])
    problem_id = SelectField('Filter by Problem', coerce=int, choices=[])

    submit = SubmitField('Filter')
    
    def __init__(self, *args, **kwargs):
        super(BusinessCaseFilterForm, self).__init__(*args, **kwargs)
        # Add "All Problems" option and populate choices
        self.problem_id.choices = [(0, 'All Problems')] + [(p.id, f"{p.code}: {p.title}") for p in Problem.query.all()]
