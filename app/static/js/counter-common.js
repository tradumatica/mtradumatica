var STATUS_INTERVAL = 20*1000; // 20 s
var running_intervals=[];

function pad(num, size) {
  var s = num+"";
  while (s.length < size) s = "0" + s;
    return s;
}

function parseDate(dateTimeStr){
	splitBySpace=dateTimeStr.split(" ")
	dateParts=splitBySpace[0].split("-")
	timeParts=splitBySpace[1].split(":")

	year    = dateParts[0];
    month   = dateParts[1];
    day     = dateParts[2];
    hours   = timeParts[0];
    minutes = timeParts[1];
    seconds = timeParts[2];
	return Date.UTC(year, month - 1, day, hours, minutes, seconds);
}



function formatDateDiff(start, now){

	diff = now - start;

	d = Math.floor(diff / (1000 * 60 * 60 * 24));
	h = Math.floor(diff / (1000 * 60 * 60)) % 24;
	m = Math.floor(diff / (1000 * 60)) % 60;
	s = Math.floor(diff / 1000) % 60;

	if(year != -1)
		return pad(d,2)+":"+pad(h,2)+":"+pad(m,2)+":"+pad(s,2);
	else
		return ""
}

function init_clock(dateTimeStr, spanid, dataid )
{
	var startDate= parseDate(dateTimeStr)
    upd =function() {
		var today = new Date();
		timeElapsed = formatDateDiff(startDate,today);
		if (timeElapsed != "")
			$("#"+spanid).html(timeElapsed);
	};
	timerid = setInterval(upd,500);
	running_intervals.push(timerid);

}

function init_status_checker(url, id ){
	updater = function(){
		//ask web service whether training has finished.
		//It should return finish time if training has finished and empty string otherwise
		//If it has finished, reload datatable
		$.ajax({
		  url: url+"/"+id,
		  dataType: "json"
		}).done(function(data) {
			if(data.status == "done"){
				//remove intervals and reload datatable
				resetIntervals();
				table.ajax.reload(resetPaging=false);
			}
		})
	};
	timerid = setInterval(updater,STATUS_INTERVAL);
	running_intervals.push(timerid);
}

function resetIntervals(){
	$.each(running_intervals, function( index, value ) {
    clearInterval(value);
 });
	running_intervals.length=0;
}


/*** Other functions not related to intervals ***/
function addFormatedDateToDatatables(row, index){
	startDateTimeStr = $('td', row).eq(index).text();
    timestamp=parseDate(startDateTimeStr);
    date = new Date(timestamp);
    $('td', row).eq(index).text(date.toLocaleDateString()+" "+date.toLocaleTimeString());

}


function validateInputLanguage(id_array){
	$.each(id_array, function( index, elementid ) {
		$('#'+elementid).closest('.form-group').removeClass('has-error');
		$('#'+elementid+'-error').remove();

		if($('#'+elementid).text() === "None"){
			$('#'+elementid).closest('.form-group').addClass('has-error');
			var span = $('<span />').attr('class', 'help-block').attr("id",elementid+"-error").html('Please select a language.');
			span.insertAfter($('#'+elementid));
		}

	});

	noneIds= jQuery.grep(id_array, function(input){
		return $('#'+input).text() === "None" ;
	});
	return noneIds.length == 0;
}
