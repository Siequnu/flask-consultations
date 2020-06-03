// Hide the submit button on load
$('#submit-all').hide();

// Enable the datefield to use UI datepicker
$('#datefield').datepicker ({dateFormat: 'yy-mm-dd'});

// On submitting a time-slot, add this to the right column
$(':submit').click (function (event) {
  var datefield = $.trim( $('#datefield').val() );
  var start_time = $.trim( $('#start_time').val() );
  var end_time = $.trim( $('#end_time').val() );
  
  $('.bookings').append (
    '<div class="booking">' +
	'<i class="fa fa-calendar-day"></i> <label class="date">' + datefield +
	'</label><br><i class="fa fa-clock"></i><label class="start_time"> ' + start_time +
	'</label> to <label class="end_time">' + end_time + '</label><hr> </div>'
	
	);
	event.preventDefault();
	
	// If there is more than one time set, allow the user to proceed
	var numItems = $('.booking').length;
	if (numItems == 1) {
		$('#submit-all').show();
	}
});

// Handle pushing the data to the API
$('#submit-all').click (function () {
	
 $(".booking").each(function(){
	var datefield = $(this).find('.date').text();
	var start_time = $(this).find('.start_time').text();
	var end_time = $(this).find('.end_time').text();
	
	// Send data via AJAX
		$.ajax({
			type: "POST",
			url: "/api/v1/consultation/",
			contentType: 'application/json',
			headers: {'key': config.apiKey},
			data: JSON.stringify({
				date: datefield,
				start_time: start_time,
				end_time: end_time,
				teacher_id: current_user_id,
				student_id: student_id
			}),
			error: function(jqXHR, textStatus, errorThrown) {
				toastr.error(errorThrown);
				toastr.error(textStatus);
			},
			success: function() {
				toastr.success('Appointment created successfully.');
				window.location.replace('/consultations/');
			}
		});
		
 });
	
});