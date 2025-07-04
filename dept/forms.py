from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired

class DepartmentForm(FlaskForm):
    class Meta:
        csrf = False
    
    name = StringField('Name', validators=[DataRequired()])
    parent = SelectField('Parent Department', coerce=int, choices=[])
    submit = SubmitField('Save')