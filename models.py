from flask import current_app
from flask_login import current_user
from datetime import datetime
from app import db

import app.files

class Consultation (db.Model):
	__table_args__ = {'sqlite_autoincrement': True}
	id = db.Column(db.Integer, primary_key=True)
	date = db.Column(db.Date)
	start_time = db.Column(db.Time)
	end_time = db.Column(db.Time)
	teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	
	def __repr__(self):
		return '<Consultation {}>'.format(self.id)

	def delete (self):
		db.session.delete (self)
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

def new_prereading_file (file, consultation_id):
	random_filename = app.files.models.save_file(file)
	original_filename = app.files.models.get_secure_filename(file.filename)
	assignment_task_file = ConsultationPrereadingFile (
		original_filename=original_filename,
		filename = random_filename,
		uploader_id = current_user.id,
		consultation_id = consultation_id,
		timestamp = datetime.now ())
	db.session.add(assignment_task_file)
	db.session.commit ()

def delete_consultation_from_id (consultation_id):
	consultation = Consultation.query.get(consultation_id)
	if consultation is not None:
		prereading_files = ConsultationPrereadingFile.query.filter_by(consultation_id = consultation.id).all()
		for prereading_file in prereading_files:
			prereading_file.delete ()
		
		consultation.delete()
		return True
	else:
		return False