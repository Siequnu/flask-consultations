from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, DateField, SelectMultipleField, BooleanField, FormField, TextAreaField
from wtforms.validators import ValidationError, DataRequired
from flask_wtf.file import FileField, FileRequired
from app import db


class ConsultationTimeForm(FlaskForm):
	datefield = DateField('Pick a date', format="%Y-%m-%d", validators=[DataRequired()])
	start_time = StringField('Start time', validators=[DataRequired()])
	end_time = StringField('End time', validators=[DataRequired()])
	submit = SubmitField('Add time slot')
