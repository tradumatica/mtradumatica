const STATUS_INTERVAL = 20*1000; // 20 s
var running_intervals=[];

function pad(num) {
	return (num < 10) ? `0${num}` : num
}

function parseDate(dateTimeStr) {
	return new Date(dateTimeStr)
}

function formatDateDiff(start, now) {
	try {
		let diff = new Date(now.getTime() - start.getTime());
		let date = new Date(diff.getTime() + (diff.getTimezoneOffset() * 60000));
		
		return `${pad(date.getDate() - 1)}:${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
	} catch (e) {
		return ""
	}
}

function init_clock(dateTimeStr, spanid, dataid) {
	let startDate = new Date(dateTimeStr);
	let timerid = setInterval(() => {
		let today = new Date(new Date().getTime() + (new Date().getTimezoneOffset() * 60000));
		let timeElapsed = formatDateDiff(startDate, today);
		if (timeElapsed != "") {
			$("#" + spanid).html(timeElapsed);
		}
	}, 500);

	running_intervals.push(timerid);
}

function init_status_checker(url, id, table) {
	timerid = setInterval(() => {
		//ask web service whether training has finished.
		//It should return finish time if training has finished and empty string otherwise
		//If it has finished, reload datatable
		$.ajax({
			url: `${url}/${id}`,
			dataType: "json"
		}).done(function(data) {
			if(data.status == "done") {
				//remove intervals and reload datatable
				resetIntervals();
				table.ajax.reload(resetPaging=false);
			}
		});
	}, STATUS_INTERVAL);
	running_intervals.push(timerid);
}

function resetIntervals(){
	$.each(running_intervals, function( index, value ) {
    	clearInterval(value);
	});
	running_intervals.length = 0;
}


/*** Other functions not related to intervals ***/
function addFormatedDateToDatatables(row, index) {
	let startDateTimeStr = $('td', row).eq(index).text();
	let date = new Date(startDateTimeStr);
    $('td', row).eq(index).text(date.toLocaleDateString()+" "+date.toLocaleTimeString());
}

function validateInputLanguage(id_array){
	$.each(id_array, function( index, elementid ) {
		$('#'+elementid).closest('.form-group').removeClass('has-error');
		$(`#${elementid}-error`).remove();

		if($('#' + elementid).text() === "None"){
			$('#' + elementid).closest('.form-group').addClass('has-error');
			let span = $('<span />').attr('class', 'help-block').attr("id",elementid+"-error").html('Please select a language.');
			span.insertAfter($('#' + elementid));
		}
	});

	let noneIds = jQuery.grep(id_array, function(input){
		return $('#' + input).text() === "None";
	});
	
	return noneIds.length == 0;
}
