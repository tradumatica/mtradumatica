$(document).ready(function() {
  $("#clear").click(function(){
    $("#inputtext").val("");
    $("#outputtext").val("");
  });

  $("#form-texttrans").submit(function(e){
    return false;
  });

  $("#submit").click(function(){
    if ($("#inputtext").val().trim() == "") {
      $("#outputtext").val("");
      return;
    }

    let stext = $("#inputtext").val();

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

  $("#my-file-selector").change(function(){
    let parts_filename   = $(this).val().split("\\");
    let display_filename = parts_filename[parts_filename.length-1];
    
    const extensions = ["txt", "html", "htm", "docx", "odt", "odp", "ods", "pptx", "xlsx"];
    let found = false;
    for (let i = 0; !found && i < extensions.length; i++) {
      if (display_filename.toLowerCase().endsWith("." + extensions[i])) {
        found = true
      }
    }
    
    if (!found) {
      $('#upload-file-info').html("");
      $('#upload-error').removeClass("hidden");
    } else {
      $('#upload-file-info').html(display_filename);
      $('#upload-error').addClass("hidden");
    }
  });

  $("#my-file-selector-tmx").change(function(){
    let parts_filename   = $(this).val().split("\\");
    let display_filename = parts_filename[parts_filename.length-1];
    
    const extensions = ["tmx"];
    let found = false;
    for (let i = 0; !found && i < extensions.length; i++) {
      if(display_filename.toLowerCase().endsWith("." + extensions[i])) {
        found = true;
      }
    }
    
    if(!found) {
      $('#upload-file-info-tmx').html("");
      $('#upload-error-tmx').removeClass("hidden");
    } else {
      $('#upload-file-info-tmx').html(display_filename);
      $('#upload-error-tmx').addClass("hidden");
    }
  });

  $("#cancel-modal").click(function(){
    // cancel task
    $("#my-please-wait").modal("hide");
  });
});
