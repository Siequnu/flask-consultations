from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, DateField, SelectMultipleField, BooleanField, FormField, TextAreaField
from wtforms.validators import ValidationError, DataRequired, Length
from flask_wtf.file import FileField, FileRequired
from app import db


class ConsultationTimeForm(FlaskForm):
    datefield = DateField('Pick a date', format="%Y-%m-%d",
                          validators=[DataRequired()])
    start_time = StringField('Start time', validators=[DataRequired()])
    end_time = StringField('End time', validators=[DataRequired()])
    submit = SubmitField('Add time slot')


class ConsultationDetailsForm(FlaskForm):
    title = StringField('Consultation title:', validators=[
                        DataRequired(), Length(max=300)])
    description = StringField('Consultation description:', validators=[
                              DataRequired(), Length(max=2000)])
    submit = SubmitField('Save consultation details')


class ConsultationReportForm(FlaskForm):
    summary = StringField('Summary of the situation:', validators=[
        DataRequired(), Length(max=250)])
    report = TextAreaField('Consultation report:', validators=[
        DataRequired(), Length(max=2000)])
    submit = SubmitField('Save consultation report')
