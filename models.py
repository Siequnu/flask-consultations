from flask import current_app
from flask_login import current_user
from datetime import datetime
from app import db

from app.models import User
import app.files

import arrow

class Consultation (db.Model):
	__table_args__ = {'sqlite_autoincrement': True}
	id = db.Column(db.Integer, primary_key=True)
	date = db.Column(db.Date)
	start_time = db.Column(db.DateTime)
	end_time = db.Column(db.DateTime)
	teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	title = db.Column(db.String(300), default='Add a consultation title')
	description = db.Column(db.String(2000), default='Add a description')
	
	def __repr__(self):
		return '<Consultation {}>'.format(self.id)

	def delete (self):
		db.session.delete (self)
		db.session.commit ()

	def save (self):
		db.session.add (self)
		db.session.flush () 
		db.session.commit ()
	
	def save_consultation_details (self, title, description):
		self.title = title
		self.description = description
		db.session.commit ()

	def get_scheduling_options (self):
		scheduling_options = ConsultationSchedulingOption.query.filter_by(consultation_id = self.id).all()
		scheduling_options_array = []
		for option in scheduling_options:
			option_dict = option.__dict__
			# Calculate the dt object of start_time and end_time, as these are being saved as timedelta rather than datetime
			# #¡# This turned out to be error with SQL alchemy not saving in the correct format
			#option_dict['start_time_dt'] = datetime.strptime(str(option_dict['start_time']),'%H:%M:%S').time()
			#option_dict['end_time_dt'] = datetime.strptime(str(option_dict['end_time']),'%H:%M:%S').time()
			option_dict['humanized_date'] = arrow.get(option_dict['date']).humanize()
			scheduling_options_array.append(option_dict)
		return scheduling_options_array


class ConsultationSchedulingOption (db.Model):
	__table_args__ = {'sqlite_autoincrement': True}
	id = db.Column(db.Integer, primary_key=True)
	consultation_id = db.Column(db.Integer, db.ForeignKey('consultation.id'))
	date = db.Column(db.Date)
	start_time = db.Column(db.DateTime)
	end_time = db.Column(db.DateTime)
	
	def __repr__(self):
		return '<Consultation scheduling option {}>'.format(self.id)

	def delete (self):
		db.session.delete (self)
		db.session.commit ()
	
	def set_as_consultation_schedule (self):
		consultation = Consultation.query.get (self.consultation_id)
		if consultation is None: 
			return False
		consultation.date = self.date
		consultation.start_time = self.start_time
		consultation.end_time = self.end_time
		db.session.commit()
		return True


class ConsultationPrereadingFile (db.Model):
	__table_args__ = {'sqlite_autoincrement': True}
	id = db.Column(db.Integer, primary_key=True)
	timestamp = db.Column(db.DateTime, index=True, default=datetime.now())
	uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	consultation_id = db.Column(db.Integer, db.ForeignKey('consultation.id'))
	original_filename = db.Column(db.String(140))
	filename = db.Column(db.String(140))
	description = db.Column(db.String(1000))
	
	def __repr__(self):
		return '<Pre-reading file {}>'.format(self.id)

	def delete (self):
		db.session.delete (self)
		db.session.commit ()

class ConsultationReport (db.Model):
	__table_args__ = {'sqlite_autoincrement': True}
	id = db.Column(db.Integer, primary_key=True)
	consultation_id = db.Column(db.Integer, db.ForeignKey('consultation.id'))
	teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	summary = db.Column(db.String(250))
	report = db.Column(db.String(2000))
	
	def __repr__(self):
		return '<Consultation report {}>'.format(self.id)

	def delete (self):
		db.session.delete (self)
		db.session.commit ()

	def save_report_details (self, consultation_id, teacher_id, summary, report, create_new = False):
		self.consultation_id = consultation_id
		self.teacher_id = teacher_id
		self.summary = summary
		self.report = report
		if create_new:
			db.session.add(self)
		db.session.commit ()

class ConsultationReportFile (db.Model):
	__table_args__ = {'sqlite_autoincrement': True}
	id = db.Column(db.Integer, primary_key=True)
	timestamp = db.Column(db.DateTime, index=True, default=datetime.now())
	uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	consultation_report_id = db.Column(db.Integer, db.ForeignKey('consultation_report.id'))
	original_filename = db.Column(db.String(140))
	filename = db.Column(db.String(140))
	
	def __repr__(self):
		return '<Consultation report file {}>'.format(self.id)

	def delete (self):
		db.session.delete (self)
		db.session.commit ()



def get_consultation_info_array (student_id = False):
	if student_id:
		consultations = Consultation.query.filter_by(student_id = student_id).all()
	else:
		consultations = Consultation.query.all()
	
	# For each consultation, append additional information
	consultations_array = []
	for consultation in consultations:
		consultation_dict = consultation.__dict__
		consultation_dict['student'] = User.query.get(
			consultation.student_id)
		consultation_dict['teacher'] = User.query.get(
			consultation.teacher_id)
		consultation_dict['humanized_date'] = arrow.get(consultation_dict['date']).humanize()
		consultation_dict['scheduling_options'] = consultation.get_scheduling_options ()
		consultations_array.append(consultation_dict)

	return consultations_array

def get_consultation_reports_with_files (consultation_id):
	consultation_reports = ConsultationReport.query.filter_by(consultation_id = consultation_id).all()
	consultation_reports_array = []
	for report in consultation_reports:
		report_dict = report.__dict__
		report_dict['report_files'] = ConsultationReportFile.query.filter_by(consultation_report_id = report.id).all()
		report_dict['user'] = User.query.filter_by(id = report.teacher_id).one()
		consultation_reports_array.append(report_dict)

	return consultation_reports_array

def new_prereading_file (file, consultation_id):
	random_filename = app.files.models.save_file(file)
	original_filename = app.files.models.get_secure_filename(file.filename)
	prereading_file = ConsultationPrereadingFile (
		original_filename=original_filename,
		filename = random_filename,
		uploader_id = current_user.id,
		consultation_id = consultation_id,
		timestamp = datetime.now ())
	db.session.add(prereading_file)
	db.session.commit ()

def new_report_file (file, consultation_report_id):
	random_filename = app.files.models.save_file(file)
	original_filename = app.files.models.get_secure_filename(file.filename)
	report_file = ConsultationReportFile (
		original_filename=original_filename,
		filename = random_filename,
		uploader_id = current_user.id,
		consultation_report_id = consultation_report_id,
		timestamp = datetime.now ())
	db.session.add(report_file)
	db.session.commit ()

def delete_consultation_from_id (consultation_id):
	consultation = Consultation.query.get(consultation_id)
	if consultation is not None:
		# Delete any pre-reading files
		prereading_files = ConsultationPrereadingFile.query.filter_by(consultation_id = consultation.id).all()
		for prereading_file in prereading_files:
			prereading_file.delete ()

		# Delete any reports, after deleting any uploaded report files
		consultation_reports = ConsultationReport.query.filter_by(consultation_id = consultation.id).all()
		for report in consultation_reports:
			report_files = ConsultationReportFile.query.filter_by(consultation_report_id = report.id).all()
			for file in report_files:
				file.delete()
			
			report.delete()
		
		# Delete any consultation schedules
		consultation_schedules = ConsultationSchedulingOption.query.filter_by(consultation_id = consultation.id).all()
		for schedule in consultation_schedules:
			schedule.delete ()
		
		consultation.delete()
		return True
	else:
		return False