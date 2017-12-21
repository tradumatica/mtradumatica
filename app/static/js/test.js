$("#clear").click(function(){
 $("#inputtext").val("")
 $("#outputtext").val("")
});

$("#submit").click(function(){
  if($("#inputtext").val().trim() == "")
  {
    $("#outputtext").val("");
    return;
  }
  stext = $("#inputtext").val();
  
  $.ajax({
    url: "actions/translate",
    dataType: "json",
    data: JSON.stringify({"text": stext}),
    contentType: "application/json",
    type: "POST"
  }).done(function(data) {
    $("#outputtext").val(data.text);
  });
});

