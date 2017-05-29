var STATUS_INTERVAL = 20*1000; // 20 s
var status_idint    = -1;

var year;   
var month;  
var day;    
var hours;  
var minutes;
var seconds;

function init_clock()
{
  year    = -1;
  month   = -1
  day     = -1;
  hours   = -1;
  minutes = -1;
  seconds = -1;
}

function pad(num, size) {
  var s = num+"";
  while (s.length < size) s = "0" + s;
    return s;
}

function clock() {
  var today = new Date();
  var start = Date.UTC(year, month - 1, day, hours, minutes, seconds);

  diff = today - start;
    
  d = Math.floor(diff / (1000 * 60 * 60 * 24));
  h = Math.floor(diff / (1000 * 60 * 60)) % 24;
  m = Math.floor(diff / (1000 * 60)) % 60;
  s = Math.floor(diff / 1000) % 60;

  if(year != -1)
    $("#elapsed_time").html(pad(d,2)+":"+pad(h,2)+":"+pad(m,2)+":"+pad(s,2));

  var t = setTimeout(clock, 500);
}

function responsiveState()
{  
  if($('#sourcesel').val() != "null" && $("#targetsel").val() != "null" && $("#targetsel").val() != $("#sourcesel").val()) 
  {
    $("#train").removeClass("disabled");
  }
  else
  { 
    $("#train").addClass("disabled");
  }
}

$("#sourcesel, #targetsel").change(function(){
  responsiveState();
});

$("#train").click(function() {
  $.ajax({url: "actions/build-simple/" + $("#sourcesel").val() + "/" + $("#targetsel").val()});
  updateStatus();
  trainingState();
});

$("#cancel").click(function() {
  $.ajax({url: "actions/cancel-simple"});
  emptyState();
});

$("#remove").click(function() {
  $.ajax({url: "actions/remove-simple"});
  emptyState();
});

function emptyState()
{
  $("#create_form").show();
  $("#cancel_form").hide();
  $("#remove_form").hide();
  responsiveState();
  if(status_idint != -1)
  {
    removeInterval(status_idint);
  }
  
  init_clock();
}

function doneState()
{
  $("#create_form").hide();
  $("#cancel_form").hide();
  $("#remove_form").show();
  if(status_idint != -1)
  {
    removeInterval(status_idint);
  }
  init_clock();
}

function trainingState()
{
  $("#create_form").hide();
  $("#cancel_form").show();
  $("#remove_form").hide();
}


function updateStatus()
{
  $.ajax({
    url: "actions/status-simple",
    dataType: "json"
  }).done(function(data) {
    if(data.status == "empty")
    {
      emptyState();
      return "empty";
    }
    else if(data.status == "done")
    {
      doneState();
      return "done";
    }
    else
    { 
      if(!$("#cancel_form").is(":visible"))
      {
        year    = data.year;
        month   = data.month;
        day     = data.day;
        hours   = data.hours;
        minutes = data.minutes;
        seconds = data.seconds;
        status_idint = setInterval(updateStatus, STATUS_INTERVAL);
      }

      trainingState();
      return "training";
    }
  });  
}

$(document).ready(function(){
  init_clock();
  clock();
  updateStatus();
});
