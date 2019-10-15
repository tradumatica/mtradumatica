$(document).ready(function() {
  $("#submit").click(function(){
    if ($("#inputtext").val().trim() == "") {
      $("#outputtext").val("");
      return;
    }

    let stext = $("#inputtext").val();
    let selection = $("#lmsel").val();
    let type = "translator";
    let id = -1;
    
    if (selection.startsWith("lm-")) {
      type = "lm";
      id = parseInt(selection.substring(3));
    } else {
      id = parseInt(selection);
    }

    $.ajax({
      url: "actions/query-lm",
      dataType: "json",
      data: JSON.stringify({"text": stext, "id": id, "type": type}),
      contentType: "application/json",
      type: "POST"
    }).done(function(data) {
      $("#outputtext").val(data.output);
    }).fail(function() {
      alert("Error");
    });
  });

  $("#submit2").click(function() {
    if ($("#inputtext2").val().trim() == "") {
      $("#outputtext2").val("");
      return;
    }

    let stext = $("#inputtext2").val();
    let id = parseInt($("#tmsel").val());

    $.ajax({
      url: "actions/query-tm",
      dataType: "json",
      data: JSON.stringify({"text": stext, "id": id}),
      contentType: "application/json",
      type: "POST"
    }).done(function(data) {
      $("#outputtext2").val(data.output);
    }).fail(function() {
      alert("Error");
    });
  });

  $("#submit3").click(function() {
    if($("#inputtext3").val().trim() == "") {
      $("#outputtext3").val("");
      return;
    }

    let stext = $("#inputtext3").val();
    let id = parseInt($("#pbdsel").val());
    let st = $("#source_target").val()

    $.ajax({
      url: "actions/search-dictionary",
      dataType: "json",
      data: JSON.stringify({"word": stext, "tid": id, "side": st}),
      contentType: "application/json",
      type: "POST"
    }).done(function(data) {
      let v = "";
      for(i = 0; i< data.translations.length; i++) {
        v += data.translations[i][1].toFixed(7);
        v += "\t";
        v += data.translations[i][0];
        v += "\n";
      }
      
      if(data.translations.length == 0) {
        v = "Empty";
      }
      
      $("#outputtext3").val(v);
    }).fail(function() {
      alert("Error");
    });
  });

  $("#submit4").click(function() {
    if($("#inputtext4").val().trim() == "") {
      $("#inputtok4").val("");
      $("#inputtrue4").val("");
      $("#details4").val("");
      $("#align4").val("");
      $("#unk4").val("");
      $("#nbest4").val("");
      $("#outputtok4").val("");
      $("#outputtrue4").val("");
      $("#outputtext4").val("");
      return;
    }

    let stext = $("#inputtext4").val();
    let id = parseInt($("#mtsel").val());

    $.ajax({
      url: "actions/translate-inspect",
      dataType: "json",
      data: JSON.stringify({"text": stext, "tid": id}),
      contentType: "application/json",
      type: "POST"
    }).done(function(data) {
      $("#inputtok4").val(data.input_tok);
      $("#inputtrue4").val(data.input_tru);
      $("#details4").val(data.details);
      $("#align4").val(data.align);
      $("#unk4").val(data.unknown);
      $("#nbest4").val(data.nbest);    
      $("#outputtok4").val(data.output_tok);
      $("#outputtrue4").val(data.output_tru);
      $("#outputtext4").val(data.output);    
    }).fail(function() {
      alert("Error");
    });
  });

  $("#clear4").click(function() {
    $("#inputtext4").val("");
    $("#outputtext4").val("");
  });

  $("#submit5").click(function() {
    let id = parseInt($("#mrsel").val());
    
    $.ajax({
      url: "actions/moses-activate/"+id.toString(),
      dataType: "json",
      contentType: "application/json",
      type: "GET"
    }).done(function(data) {
      if(data.status == "OK") {
        $("#clear5").removeClass("disabled");
        $("#submit5").addClass("disabled");
        $('#mrsel').attr('disabled', true);
      }
    }).fail(function() {
      alert("Error");
    });
  });

  $("#clear5").click(function() {
    $.ajax({
      url: "actions/moses-deactivate",
      dataType: "json",
      contentType: "application/json",
      type: "GET"
    }).done(function(data) {
      if(data.status == "OK") {
        $("#clear5").addClass("disabled");      
        $("#submit5").removeClass("disabled");
        $('#mrsel').attr("disabled", false);
      }
    }).fail(function() {
      alert("Error");
    });
  });

  $('.nav-tabs a').click(function (e) {
    e.preventDefault()
    $(this).tab('show');
  });

  $(".tab-content form").on('submit', function(e) {
    e.preventDefault();
    e.stopPropagation();
    return false;
  })
});