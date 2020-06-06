from flask import render_template, flash, redirect, url_for, request, abort, current_app, session, Response
from flask_login import current_user, login_required

from . import bp, models
from .forms import ConsultationTimeForm

from .models import Consultation, ConsultationPrereadingFile
import app.models
from app.models import User

import os

# Render this blueprint's javascript
@bp.route("/js/<filename>")
@login_required
def js(filename):
	filepath = 'js/' + filename
	return render_template(filepath) # is send_from_directory('/templates/js/', path) a safer approach?

# Consultations home page
@bp.route("/")
@login_required
def view_consultations():
	# View a list of consultations 
	if current_user.is_authenticated and app.models.is_admin(current_user.username):
		consultations = Consultation.query.all()
		consultations_array = []
		for consultation in consultations:
			consultation_dict = consultation.__dict__
			consultation_dict['student'] = User.query.get(consultation.student_id)
			consultations_array.append (consultation_dict)
		return render_template('view_consultations.html', consultations = consultations_array)
	
@bp.route("/view/<int:consultation_id>")
@login_required
def view_consultation(consultation_id):
	# View a list of consultations 
	if current_user.is_authenticated and app.models.is_admin(current_user.username):
		consultation = Consultation.query.get(consultation_id)
		if consultation is None:
			abort (404)
		student = User.query.get(consultation.student_id)	
		prereading_files = ConsultationPrereadingFile.query.filter_by(consultation_id = consultation.id).all()
		return render_template('view_consultation.html', consultation = consultation, student = student, prereading_files = prereading_files)
	

# Search for a student
@bp.route("/book/search")
@login_required
def book_consultation_find_student():
	# View a list of consultations 
	if current_user.is_authenticated and app.models.is_admin(current_user.username):
		students = User.query.filter_by(is_admin = False).all()
		return render_template('search_student.html', students = students)
	
# Book a consultation
@bp.route("/book/<student_id>/calendar")
@login_required
def book_consultation_set_time(student_id):
	# View a list of consultations 
	if current_user.is_authenticated and app.models.is_admin(current_user.username):
		student = User.query.get(student_id)
		if student is None:
			abort (404)
		form = ConsultationTimeForm()
		return render_template('book_time.html', form = form, student = student)
	
# Redirect after booking consultation
@bp.route("/book/<student_id>/redirect")
@login_required
def book_consultation_redirect(student_id):
	return redirect (url_for ('consultations.view_consultations'))

# Delete a consultation from ID	
@bp.route('/delete/<consultation_id>')
@login_required
def delete_consultation(consultation_id):
	if current_user.is_authenticated and app.models.is_admin(current_user.username):
		try:
			consultation = Consultation.query.get(consultation_id)
		except:
			flash ('This consultation could not be found.', 'error')
			return redirect(url_for('consultations.view_consultations'))
		if consultation is None:
			flash ('This consultation could not be found.', 'error')
			return redirect(url_for('consultations.view_consultations'))
		if models.delete_consultation_from_id(consultation_id):
			flash ('Successfully deleted the consultation', 'success')
			return redirect(url_for('consultations.view_consultations'))
		else:
			flash ('This consultation could not be deleted.', 'error')
			return redirect(url_for('consultations.view_consultations'))
	abort (403)

# Add a pre-reading file
@bp.route('/<consultation_id>/prereading/add', methods=['GET', 'POST'])
@login_required
def upload_prereading_file(consultation_id):
	if request.method == 'POST':
		file_obj = request.files
		for f in file_obj:
			file = request.files.get(f)
			models.new_prereading_file (file, consultation_id)

	if current_user.is_authenticated and app.models.is_admin(current_user.username):
		consultation = Consultation.query.get(consultation_id)
		if consultation is None:
			flash('This consultation could not be found.', 'error')
			return redirect(url_for('consultations.view_consultations'))	
		else:
			return render_template ('upload_prereading.html', consultation = consultation)
	else:
		abort (403)

# Delete a pre-reading file
@bp.route('/<consultation_id>/prereading/delete/<prereading_file_id>', methods=['GET', 'POST'])
@login_required
def delete_prereading_file (consultation_id, prereading_file_id):
	prereading_file = ConsultationPrereadingFile.query.get(prereading_file_id)
	if prereading_file is not None:
		prereading_file.delete ()
	flash ('Deleted the file successfully', 'success')
	return redirect(url_for('consultations.view_consultation', consultation_id = consultation_id))	