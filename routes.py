from flask import render_template, flash, redirect, url_for, request, abort, current_app, session, Response, send_from_directory
from flask_login import current_user, login_required

from . import bp, models
from .forms import ConsultationTimeForm, ConsultationDetailsForm

from .models import Consultation, ConsultationPrereadingFile
import app.models
from app.models import User

import os
import arrow


# Render this blueprint's javascript
@bp.route("/js/<filename>")
@login_required
def js(filename):
	filepath = 'js/' + filename
	# is send_from_directory('/templates/js/', path) a safer approach?
	return render_template(filepath)


# Consultations home page
@bp.route("/")
@login_required
def view_consultations():
	if current_user.is_authenticated and app.models.is_admin(current_user.username):

		# Get all consultations
		consultations = Consultation.query.all()

		# For each consultation, append additional information
		consultations_array = []
		for consultation in consultations:
			consultation_dict = consultation.__dict__
			consultation_dict['student'] = User.query.get(
				consultation.student_id)
			consultation_dict['humanized_date'] = arrow.get(
				consultation_dict['date']).humanize()
			consultations_array.append(consultation_dict)
		return render_template('view_consultations.html', consultations=consultations_array)


# View a single consultation
@bp.route("/view/<int:consultation_id>")
@login_required
def view_consultation(consultation_id):
	# View a list of consultations
	if current_user.is_authenticated and app.models.is_admin(current_user.username):

		# Get the consultation
		consultation = Consultation.query.get(consultation_id)
		if consultation is None:
			abort(404)

		# Append humanized timestamp
		consultation_dict = consultation.__dict__
		consultation_dict['humanized_date'] = arrow.get(
			consultation_dict['date']).humanize()

		# Append other information
		student = User.query.get(consultation.student_id)
		prereading_files = ConsultationPrereadingFile.query.filter_by(
			consultation_id=consultation.id).all()

		return render_template('view_consultation.html', consultation=consultation, student=student, prereading_files=prereading_files)


# Search for a student
@bp.route("/book/search")
@login_required
def book_consultation_find_student():
	# View a list of consultations
	if current_user.is_authenticated and app.models.is_admin(current_user.username):
		students = User.query.filter_by(is_admin=False).all()
		return render_template('search_student.html', students=students)


# Book a consultation
@bp.route("/book/<student_id>/calendar")
@login_required
def book_consultation_set_time(student_id):
	# View a list of consultations
	if current_user.is_authenticated and app.models.is_admin(current_user.username):
		student = User.query.get(student_id)
		if student is None:
			abort(404)
		form = ConsultationTimeForm()
		return render_template('book_time.html', form=form, student=student)


# Redirect after booking consultation
@bp.route("/book/<student_id>/redirect")
@login_required
def book_consultation_redirect(student_id):
	return redirect(url_for('consultations.view_consultations'))


# Delete a consultation from ID
@bp.route('/delete/<consultation_id>')
@login_required
def delete_consultation(consultation_id):
	if current_user.is_authenticated and app.models.is_admin(current_user.username):
		try:
			consultation = Consultation.query.get(consultation_id)
		except:
			flash('This consultation could not be found.', 'error')
			return redirect(url_for('consultations.view_consultations'))
		if consultation is None:
			flash('This consultation could not be found.', 'error')
			return redirect(url_for('consultations.view_consultations'))
		if models.delete_consultation_from_id(consultation_id):
			flash('Successfully deleted the consultation', 'success')
			return redirect(url_for('consultations.view_consultations'))
		else:
			flash('This consultation could not be deleted.', 'error')
			return redirect(url_for('consultations.view_consultations'))
	abort(403)


# Add or edit consultation details
@bp.route('/details/<consultation_id>/edit', methods=['GET', 'POST'])
@login_required
def save_consultation_details(consultation_id):
	if app.models.is_admin(current_user.username):
		consultation = Consultation.query.get(consultation_id)
		if consultation is not None:
			form = ConsultationDetailsForm(obj=consultation)
			if form.validate_on_submit():
				consultation.save_consultation_details(
					form.title.data, form.description.data)
				flash('Saved the consultation details', 'success')
				return redirect(url_for('consultations.view_consultation', consultation_id=consultation_id))
			return render_template('save_consultation_details.html', title='Save consultation details', form=form, consultation_id=consultation_id)
		abort (404)
	abort(403)


# Add a pre-reading file
@bp.route('/<consultation_id>/prereading/add', methods=['GET', 'POST'])
@login_required
def upload_prereading_file(consultation_id):
	if request.method == 'POST':
		file_obj = request.files
		for f in file_obj:
			file = request.files.get(f)
			models.new_prereading_file(file, consultation_id)

	if current_user.is_authenticated and app.models.is_admin(current_user.username):
		consultation = Consultation.query.get(consultation_id)
		if consultation is None:
			flash('This consultation could not be found.', 'error')
			return redirect(url_for('consultations.view_consultations'))
		else:
			return render_template('upload_prereading.html', consultation=consultation)
	else:
		abort(403)


# Route to download a prereading file
@bp.route('/download/prereading/<prereading_file_id>')
@login_required
def download_prereading_file(prereading_file_id):

	# Get the prereading file and consultation	
	prereading_file = ConsultationPrereadingFile.query.get(prereading_file_id)
	if prereading_file is not None:
		consultation = prereading_file.consultation_id
	
		# Only admin or consultation file receiver can access this file 
		if app.models.is_admin(current_user.username) or consultation.student_id == current_user.id:
			return send_from_directory(filename = prereading_file.filename,
								   directory=current_app.config['UPLOAD_FOLDER'],
								   as_attachment = True,
								   attachment_filename = prereading_file.original_filename)
	abort (403)

# Delete a pre-reading file
@bp.route('/<consultation_id>/prereading/delete/<prereading_file_id>', methods=['GET', 'POST'])
@login_required
def delete_prereading_file(consultation_id, prereading_file_id):
	prereading_file = ConsultationPrereadingFile.query.get(prereading_file_id)
	if prereading_file is not None:
		prereading_file.delete()
	flash('Deleted the file successfully', 'success')
	return redirect(url_for('consultations.view_consultation', consultation_id=consultation_id))


