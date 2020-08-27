// Hide the submit button on load
$('#submit-all').hide();

// Enable the datefield to use UI datepicker
$('#datefield').datepicker({ dateFormat: 'yy-mm-dd' });

// Enable timepicker
$('#start_time, #end_time').timepicker({
	'timeFormat': 'H:i',
	'minTime': '07:00am',
	'step': 15
});

$('#end_time').timepicker('option', 'showDuration', true)

// On updating the start time, change the end_time to 15 minutes after
$(document).on('change', '#start_time', function (e) {
	// Get the date object
	var dateObject = $('#start_time').timepicker('getTime');

	// Add 15 minutes, using moment library
	//var newTime = moment(dateObject).add(15, 'm').toDate();

	// Update end_time timepicker
	$('#end_time').timepicker('option', 'minTime', dateObject);
});

// On submitting a time-slot, add this to the right column
$(':submit').click(function (event) {
	var datefield = $.trim($('#datefield').val());
	var start_time = $.trim($('#start_time').val());
	var end_time = $.trim($('#end_time').val());

	$('.bookings').append(
		'<div class="booking">' +
		'<i class="fa fa-calendar-day"></i> <label class="date">' + datefield +
		'</label><br><i class="fa fa-clock"></i><label class="start_time"> ' + start_time +
		'</label> to <label class="end_time">' + end_time + '</label><hr> </div>'

	);
	event.preventDefault();

	// Change the add time slot button text
	$('#submit').prop('value', 'Add another time slot');

	// If there is more than one time set, allow the user to proceed
	var numItems = $('.booking').length;
	if (numItems == 1) {
		$('#submit-all').show();
	}
});

// Handle pushing the data to the API
$('#submit-all').click(function () {

	$(".booking").each(function () {
		var datefield = $(this).find('.date').text().trim();
		var start_time = $(this).find('.start_time').text().trim();
		var end_time = $(this).find('.end_time').text().trim();

		// Get the csrf token
		const csrftoken = Cookies.get('_csrf_token');
		
		// Send data via AJAX
		$.ajax({
			type: "POST",
			url: "/api/v1/consultation/schedule",
			contentType: 'application/json',
			headers: { 'key': config.apiKey, 'X-CSRFToken': csrftoken },
			data: JSON.stringify({
				consultation_id: consultation_id,
				date: datefield,
				start_time: start_time,
				end_time: end_time
			}),
			error: function (jqXHR, textStatus, errorThrown) {
				toastr.error(errorThrown);
				toastr.error(textStatus);
			},
			success: function () {
				toastr.success('Scheduling options saved successfully.');
				window.location.replace('/consultations/' + consultation_id + '/book/calendar');
			}
		});

	});

});