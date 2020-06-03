from flask import current_app
from flask_login import current_user
from datetime import datetime
from app import db

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
	
def delete_consultation_from_id (id):
	consultation = Consultation.query.get(id)
	if consultation is not None:
		db.session.delete(consultation)
		db.session.commit
		return True
	else:
		return False
		
