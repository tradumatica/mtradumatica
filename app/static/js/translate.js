var doctype = "";
var ufilename = "";

function refreshSubmitButtons()
{
  if($("select#translatorsel option").filter(":selected").text() == "" || $("#inputtext").val().trim() == "")
  {
    $("#submit").addClass("disabled");
  }
  else
  {
    $("#submit").removeClass("disabled");
  }
  
  if($("select#translatorsel2 option").filter(":selected").text() == "" || $("#my-file-selector").val().trim() == "" || !$("#upload-error").hasClass("hidden"))
  {
    $("#submit2").addClass("disabled");
  }
  else
  {
    $("#submit2").removeClass("disabled");
  }
}


$("#clear").click(function(){
 $("#inputtext").val("");
 $("#outputtext").val("");
 refreshSubmitButtons();
});

$("#form-texttrans").submit(function(e){
  return false;
});


$("#submit").click(function(){
  if($("#inputtext").val().trim() == "")
  {
    $("#outputtext").val("");
    return;
  }
  stext = $("#inputtext").val();

  $("#my-please-wait").modal("show");
  
  $.ajax({
    url: "actions/translatechoose/"+$("#translatorsel").val(),
    dataType: "json",
    data: JSON.stringify({"text": stext}),
    contentType: "application/json",
    type: "POST"
  }).done(function(data) {
    $("#outputtext").val(data.text);
    $("#my-please-wait").modal("hide");
  });
});


$("#form-doctrans").submit(function(e){
  e.preventDefault();
  var data = new FormData(this);
  data.append('doctype', doctype);

//  $("#my-please-wait").modal("show");
  
  $.ajax({
    url: "actions/translate-doc/"+$("#translatorsel2").val(),
    data: data,
    cache: false,
    contentType: false,
    processData: false,
    type: 'POST'
  })
  .done(function(){
    alert("OK");
  })
  .fail(function(xhr, err){
    var responseTitle= $(xhr.responseText).filter('title').get(0);
    alert($(responseTitle).text() + "\n" + err);
  })
  .always(function(){
    //$("#my-please-wait".modal("hide");
  });
});

$("#texttab").click(function(){
  $("#texttab_contents").removeClass("hidden");
  $("#docstab_contents").addClass("hidden");
  $("#texttab_tab").addClass("active");
  $("#docstab_tab").removeClass("active");

});

$("#docstab").click(function(){
  $("#docstab_contents").removeClass("hidden");
  $("#texttab_contents").addClass("hidden");
  $("#docstab_tab").addClass("active");
  $("#texttab_tab").removeClass("active");
});

$("#my-file-selector").change(function(){
  parts_filename   = $(this).val().split("\\");
  display_filename = parts_filename[parts_filename.length-1];
  
  extensions = ["txt", "html", "htm", "docx", "odt", "odp", "ods", "pptx", "xlsx"];
  var i = 0;
  while(i < extensions.length)
  {
    if(display_filename.toLowerCase().endsWith("."+extensions[i]))
    {
      doctype = extensions[i];
      ufilename = display_filename;
      break;
    }
    i++;
  }
  
  if(i == extensions.length)
  {
    $('#upload-file-info').html("");
    $('#upload-error').removeClass("hidden");
  }
  else
  {
    $('#upload-file-info').html(display_filename);
    $('#upload-error').addClass("hidden");
  }
  
  refreshSubmitButtons();
});

$("#cancel-modal").click(function(){
  // cancel task
  $("#my-please-wait").modal("hide");
});

$("#translatorsel").change(function(){
  refreshSubmitButtons();
});

$("#translatorsel2").change(function(){
  refreshSubmitButtons();
});

$("#inputtext").change(function(){
  refreshSubmitButtons();
});

$("#inputtext").keypress(function(event){
  refreshSubmitButtons();
});

$("#inputtext").keyup(function(event){
  refreshSubmitButtons();
});
$("#inputtext").keydown(function(event){
  refreshSubmitButtons();
});

$(document).ready(function(){
  refreshSubmitButtons();
});

