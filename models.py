from flask import current_app
from flask_login import current_user
from datetime import datetime
from app import db

from app.models import User

import app.files

class Consultation (db.Model):
	__table_args__ = {'sqlite_autoincrement': True}
	id = db.Column(db.Integer, primary_key=True)
	date = db.Column(db.Date)
	start_time = db.Column(db.Time)
	end_time = db.Column(db.Time)
	teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	title = db.Column(db.String(300), default='Add a consultation title')
	description = db.Column(db.String(2000), default='Add a description')
	
	def __repr__(self):
		return '<Consultation {}>'.format(self.id)

	def delete (self):
		db.session.delete (self)
		db.session.commit ()
	
	def save_consultation_details (self, title, description):
		self.title = title
		self.description = description
		db.session.commit ()

	def update_scheduling_option (self, ConsultationSchedulingOption):
		self.date = ConsultationSchedulingOption.date
		self.start_time = ConsultationSchedulingOption.start_time
		self.end_time = ConsultationSchedulingOption.end_time
		db.session.commit()

class ConsultationSchedulingOption (db.Model):
	__table_args__ = {'sqlite_autoincrement': True}
	id = db.Column(db.Integer, primary_key=True)
	consultation_id = db.Column(db.Integer, db.ForeignKey('consultation.id'))
	date = db.Column(db.Date)
	start_time = db.Column(db.Time)
	end_time = db.Column(db.Time)
	
	
	def __repr__(self):
		return '<Consultation scheduling option {}>'.format(self.id)

	def delete (self):
		db.session.delete (self)
		db.session.commit ()
	
	def save_consultation_details (self, title, description):
		self.title = title
		self.description = description
		db.session.commit ()


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
		prereading_files = ConsultationPrereadingFile.query.filter_by(consultation_id = consultation.id).all()
		for prereading_file in prereading_files:
			prereading_file.delete ()

		consultation_reports = ConsultationReport.query.filter_by(consultation_id = consultation.id).all()
		for report in consultation_reports:
			report_files = ConsultationReportFile.query.filter_by(consultation_report_id = report.id).all()
			for file in report_files:
				file.delete()
			
			report.delete()
		
		consultation.delete()
		return True
	else:
		return False