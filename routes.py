from flask import render_template, flash, redirect, url_for, request, abort, current_app, session, Response, send_from_directory
from flask_login import current_user, login_required

from . import bp, models
from .forms import ConsultationTimeForm, ConsultationDetailsForm, ConsultationReportForm

from .models import Consultation, ConsultationPrereadingFile, ConsultationReport, ConsultationReportFile, ConsultationSchedulingOption
import app.models
from app.models import User

import os, arrow, json


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
	if app.models.is_admin(current_user.username):
		consultations_array = models.get_consultation_info_array ()
		#¡# This should be filtered by teacher_id?
	else: 
		consultations_array = models.get_consultation_info_array (student_id = current_user.id)
	return render_template('view_consultations.html', consultations=consultations_array)


# Consultations home page
@bp.route("/calendar")
@login_required
def view_calendar():
	if app.models.is_admin(current_user.username):
		consultations = Consultation.query.filter(Consultation.date.isnot(None)).all()
	else:
		consultations = Consultation.query.filter(Consultation.date.isnot(None)).filter_by(student_id = current_user.id).all()
	return render_template('view_calendar.html', consultations = consultations)

# View a single consultation
@bp.route("/view/<int:consultation_id>")
@login_required
def view_consultation(consultation_id):
	if current_user.is_authenticated:
		
		# Get the consultation
		consultation = Consultation.query.get(consultation_id)
		if consultation is None:
			abort(404)

		# Only the student or admin can view this page
		if app.models.is_admin(current_user.username) or current_user.id == consultation.student_id:
			# Append humanized timestamp
			consultation_dict = consultation.__dict__
			consultation_dict['humanized_date'] = arrow.get(
				consultation_dict['date']).humanize()

			# Append other information
			student = User.query.get(consultation.student_id)
			prereading_files = ConsultationPrereadingFile.query.filter_by(
				consultation_id = consultation.id).all()
			consultation_reports = models.get_consultation_reports_with_files (consultation_id)

			return render_template(
				'view_consultation.html', 
				consultation=consultation, 
				student=student, 
				prereading_files=prereading_files,
				consultation_reports = consultation_reports)
		else:
			abort (403)


# Search for a student
@bp.route("/book/search")
@login_required
def book_consultation_find_student():
	# View a list of consultations
	if current_user.is_authenticated and app.models.is_admin(current_user.username):
		students = User.query.filter_by(is_admin=False).all()
		return render_template('search_student.html', students=students)

# Create a new consultation, and redirect to the details edit page
@bp.route("/book/<student_id>")
@login_required
def book_new_consultation(student_id):
	# View a list of consultations
	if current_user.is_authenticated and app.models.is_admin(current_user.username):
		student = User.query.filter_by(id = student_id).first ()
		if student is None:
			flash ('Could not locate this student.', 'error')
			return redirect(url_for('consultations.view_consultations'))
		else:
			new_consultation = Consultation (
				teacher_id = current_user.id,
				student_id = student_id
			)
			new_consultation.save ()
			
		return redirect(url_for(
			'consultations.save_consultation_details', 
			consultation_id = new_consultation.id
			))


# Display a page to add time slots to a consultation
@bp.route("/book/schedule/<consultation_id>/")
@login_required
def book_consultation_add_time(consultation_id):
	consultation = Consultation.query.get (consultation_id)

	# Check if consultation and student exist 
	if consultation is None:
		flash ('Could not find the consultation.', 'error')
		return redirect(url_for('consultations.view_consultations'))
	student = User.query.get(consultation.student_id)
	if student is None:
		flash ('Could not locate this student.', 'error')
		return redirect(url_for('consultations.view_consultations'))
	teacher = User.query.get(consultation.teacher_id)
	if teacher is None:
		flash ('Could not locate the teacher responsible for this appointment.', 'error')
		return redirect(url_for('consultations.view_consultations'))
	if app.models.is_admin(current_user.username) or current_user.id == consultation.student_id:
		form = ConsultationTimeForm()
		return render_template(
			'book_time.html', 
			form = form, 
			student = student,
			teacher = teacher,
			consultation = consultation)


# Set the time for a consultation
@bp.route("/book/schedule/set/<consultation_scheduling_option_id>/")
@login_required
def book_consultation_set_time(consultation_scheduling_option_id):
	# Retrieve the scheduling option and the corresponding Consultation
	scheduling_option = ConsultationSchedulingOption.query.get (consultation_scheduling_option_id)
	if scheduling_option is None:
		flash ('Could not find the scheduling option.', 'error')
		return redirect(url_for('consultations.view_consultations'))
	
	consultation = Consultation.query.get (scheduling_option.consultation_id)
	if consultation is None:
		flash ('Could not find the consultation.', 'error')
		return redirect(url_for('consultations.view_consultations'))

	# Only admin or student can get past this point
	if app.models.is_admin(current_user.username) or current_user.id == consultation.student_id:
		if scheduling_option.set_as_consultation_schedule () == True:
			flash ('Time slot saved.', 'success')
			return redirect(url_for('consultations.view_consultation', consultation_id = scheduling_option.consultation_id))
		else: 
			flash ('An error occured while changing the time slot.', 'error')
			return redirect(url_for('consultations.view_consultations'))


# View scheduling options
@bp.route("/<consultation_id>/book/calendar")
@login_required
def view_scheduling_options(consultation_id):
	# View consultation scheduling options
	consultation = Consultation.query.get (consultation_id)
	if consultation is None:
		flash ('Could not find the consultation.', 'error')
		return redirect(url_for('consultations.view_consultations'))

	if app.models.is_admin(current_user.username) or current_user.id == consultation.student_id:
		student = User.query.get(consultation.student_id)
		if student is None:
			flash ('Could not locate this student.', 'error')
			return redirect(url_for('consultations.view_consultations'))

		teacher = User.query.get(consultation.teacher_id)
		if teacher is None:
			flash ('Could not locate the teacher responsible for this appointment.', 'error')
			return redirect(url_for('consultations.view_consultations'))
		
		scheduling_options = consultation.get_scheduling_options ()
		return render_template(
			'schedule_appointment.html', 
			scheduling_options = scheduling_options,
			student = student, 
			teacher = teacher,
			consultation = consultation)
	else: abort (403)


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
			return render_template(
				'save_consultation_details.html', 
				title='Save consultation details', 
				form=form, 
				consultation_id = consultation_id)
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



# Add or edit consultation details
@bp.route('/<consultation_id>/report/add', methods=['GET', 'POST'])
@bp.route('/<consultation_id>/report/view/<consultation_report_id>', methods=['GET', 'POST'])
@login_required
def save_consultation_report(consultation_id, consultation_report_id = False):
	if app.models.is_admin(current_user.username):
		
		consultation = Consultation.query.get(consultation_id)
		if consultation is not None:
			
			# Define the consultation form
			form = ConsultationReportForm()
			
			# If we are editing the file, redefine the form and fill it with object
			if consultation_report_id:
				create_new = False

				# Get the existing report
				consultation_report = ConsultationReport.query.get(consultation_report_id)
				if consultation_report is not None: 
					form = ConsultationReportForm(obj=consultation_report)
			else:

				# Initialise a new report
				consultation_report = ConsultationReport()
				create_new = True	

			# Save the details if submitting form
			if form.validate_on_submit():
				consultation_report.save_report_details(
					consultation_id = consultation.id,
					teacher_id = current_user.id,
					summary = form.summary.data,
					report = form.report.data,
					create_new = create_new
					)
				flash('Added the consultation report.', 'success')
				return redirect(url_for('consultations.view_consultation', consultation_id=consultation_id))
			return render_template('save_consultation_details.html', title='Save report details', form=form, consultation_id=consultation_id)
		abort (404)
	abort(403)

# Delete a consultation report
@bp.route('/<consultation_id>/report/<consultation_report_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_consultation_report(consultation_id, consultation_report_id):
	consultation_report = ConsultationReport.query.get(consultation_report_id)
	if consultation_report is not None:
		consultation_report.delete()
	flash('Deleted the report successfully', 'success')
	return redirect(url_for('consultations.view_consultation', consultation_id=consultation_id))


# Add a report file
@bp.route('/<consultation_report_id>/report/file/add', methods=['GET', 'POST'])
@login_required
def upload_report_file(consultation_report_id):
	# Get the report
	consultation_report = ConsultationReport.query.get(consultation_report_id)
	if consultation_report is None:
		flash('This report could not be found.', 'error')
		return redirect(url_for('consultations.view_consultations'))

	# Load the consultation
	consultation = Consultation.query.get(consultation_report.consultation_id)
	if consultation is None:
		flash('This consultation could not be found.', 'error')
		return redirect(url_for('consultations.view_consultations'))

	# Upload files (used by dropzone)
	#¡# Can this be wrapped behind admin privileges?
	if request.method == 'POST':
		file_obj = request.files
		for f in file_obj:
			file = request.files.get(f)
			models.new_report_file(file, consultation_report_id)

	# IF admin, return the upload form
	if current_user.is_authenticated and app.models.is_admin(current_user.username):
		return render_template(
			'upload_report_files.html', 
			consultation=consultation, 
			consultation_report = consultation_report
		)
	else:
		abort(403)


# Route to download a prereading file
@bp.route('/download/report/file/<report_file_id>')
@login_required
def download_report_file(report_file_id):

	# Get the prereading file and consultation	
	report_file = ConsultationReportFile.query.get(report_file_id)
	if report_file is not None:
		report = ConsultationReport.query.get(report_file.consultation_report_id)
		consultation = Consultation.query.get(report.consultation_id)
	
		# Only admin or consultation file receiver can access this file 
		if app.models.is_admin(current_user.username) or consultation.student_id == current_user.id:
			return send_from_directory(
				filename = report_file.filename,
				directory=current_app.config['UPLOAD_FOLDER'],
				as_attachment = True,
				attachment_filename = report_file.original_filename)
	abort (403)

# Delete a report file
@bp.route('/<consultation_id>/file/delete/<report_file_id>', methods=['GET', 'POST'])
@login_required
def delete_report_file(consultation_id, report_file_id):
	report = ConsultationReportFile.query.get(report_file_id)
	if report is not None:
		report.delete()
	flash('Deleted the file successfully', 'success')
	return redirect(url_for('consultations.view_consultation', consultation_id=consultation_id))