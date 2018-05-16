var doctype = "";
var ufilename = "";

function refreshSubmitButtons()
{
  if($("select#lmsel option").filter(":selected").text() == "" || $("#inputtext").val().trim() == "")
  {
    $("#submit").addClass("disabled");
  }
  else
  {
    $("#submit").removeClass("disabled");
  }
  
  if($("select#tmsel option").filter(":selected").text() == "" || $("#inputtext2").val().trim() == "")
  {
    $("#submit2").addClass("disabled");
  }
  else
  {
    $("#submit2").removeClass("disabled");
  }
  
  if($("select#pbdsel option").filter(":selected").text() == "" || $("#inputtext3").val().trim() == "")
  {
    $("#submit3").addClass("disabled");
  }
  else
  {
    $("#submit3").removeClass("disabled");
  }

  if($("select#mtsel option").filter(":selected").text() == "" || $("#inputtext4").val().trim() == "")
  {
    $("#submit4").addClass("disabled");
  }
  else
  {
    $("#submit4").removeClass("disabled");
  }
  
  if($("#inputtext4").val().trim() == "")
  {
    $("#clear4").addClass("disabled");
  }
  else
  {
    $("#clear4").removeClass("disabled");
  }
  
  if($("select#mrsel option").filter(":selected").text() == "")
  {
    $("#submit5").addClass("disabled");
    $("#clear5").addClass("disabled");
  }
  else if($('#mrsel').is(':disabled'))
  {
    $("#submit5").addClass("disabled");
    $("#clear5").removeClass("disabled");
  }   
  else
  {
    $("#submit5").removeClass("disabled");
    $("#clear5").addClass("disabled");
  }  
}


$("#submit").click(function(){
  if($("#inputtext").val().trim() == "")
  {
    $("#outputtext").val("");
    return;
  }
  stext = $("#inputtext").val();
  selection = $("#lmsel").val();
  type = "translator";
  id = -1;
  
  if(selection.startsWith("lm-"))
  {
    type = "lm";
    id = parseInt(selection.substring(3));
  }
  else
  {
    id = parseInt(selection);
  }

  $.ajax({
    url: "actions/query-lm",
    dataType: "json",
    data: JSON.stringify({"text": stext, "id": id, "type": type}),
    contentType: "application/json",
    type: "POST"
  })
  .done(function(data) {
    $("#outputtext").val(data.output);
  })
  .fail(function() {
    alert("Error");
  });
});

$("#submit2").click(function(){
  if($("#inputtext2").val().trim() == "")
  {
    $("#outputtext2").val("");
    return;
  }
  stext = $("#inputtext2").val();
  id = parseInt($("#tmsel").val());

  $.ajax({
    url: "actions/query-tm",
    dataType: "json",
    data: JSON.stringify({"text": stext, "id": id}),
    contentType: "application/json",
    type: "POST"
  })
  .done(function(data) {
    $("#outputtext2").val(data.output);
  })
  .fail(function() {
    alert("Error");
  });
});

$("#submit3").click(function(){
  if($("#inputtext3").val().trim() == "")
  {
    $("#outputtext3").val("");
    return;
  }
  stext = $("#inputtext3").val();
  id = parseInt($("#pbdsel").val());
  st = $("#source_target").val()

  $.ajax({
    url: "actions/search-dictionary",
    dataType: "json",
    data: JSON.stringify({"word": stext, "tid": id, "side": st}),
    contentType: "application/json",
    type: "POST"
  })
  .done(function(data) {
  
    v = "";
    for(i = 0; i< data.translations.length; i++)
    {
      v += data.translations[i][1].toFixed(7);
      v += "\t";
      v += data.translations[i][0];
      v += "\n";
    }
    
    if(data.translations.length == 0)
    {
      v = "Empty";
    }
    
    $("#outputtext3").val(v);
  })
  .fail(function() {
    alert("Error");
  });
});

$("#submit4").click(function(){
  if($("#inputtext4").val().trim() == "")
  {
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
  stext = $("#inputtext4").val();
  id = parseInt($("#mtsel").val());

  $.ajax({
    url: "actions/translate-inspect",
    dataType: "json",
    data: JSON.stringify({"text": stext, "tid": id}),
    contentType: "application/json",
    type: "POST"
  })
  .done(function(data) {
    $("#inputtok4").val(data.input_tok);
    $("#inputtrue4").val(data.input_tru);
    $("#details4").val(data.details);
    $("#align4").val(data.align);
    $("#unk4").val(data.unknown);
    $("#nbest4").val(data.nbest);    
    $("#outputtok4").val(data.output_tok);
    $("#outputtrue4").val(data.output_tru);
    $("#outputtext4").val(data.output);    
  })
  .fail(function() {
    alert("Error");
  });
});

$("#clear4").click(function(){
  $("#inputtext4").val("");
  $("#outputtext4").val("");
});


$("#submit5").click(function(){
  id = parseInt($("#mrsel").val());
  
  $.ajax({
    url: "actions/moses-activate/"+id.toString(),
    dataType: "json",
    contentType: "application/json",
    type: "GET"
  })
  .done(function(data) {
    if(data.status == "OK")
    {
      $("#clear5").removeClass("disabled");
      $("#submit5").addClass("disabled");
      $('#mrsel').attr('disabled', true);
    }
  })
  .fail(function() {
    alert("Error");
  });
  
});

$("#clear5").click(function(){
  $.ajax({
    url: "actions/moses-deactivate",
    dataType: "json",
    contentType: "application/json",
    type: "GET"
  })
  .done(function(data){
    if(data.status == "OK")
    {
      $("#clear5").addClass("disabled");      
      $("#submit5").removeClass("disabled");
      $('#mrsel').attr("disabled", false);
    }
  })
  .fail(function(){
    alert("Error");
  });
});

$("#lmtab").click(function(){
  $("#lmtab_contents").removeClass("hidden");
  $("#tmtab_contents").addClass("hidden");
  $("#pbdtab_contents").addClass("hidden");
  $("#mttab_contents").addClass("hidden");
  $("#mrtab_contents").addClass("hidden");
  $("#lmtab_tab").addClass("active");
  $("#tmtab_tab").removeClass("active");
  $("#pbdtab_tab").removeClass("active");
  $("#mttab_tab").removeClass("active");
  $("#mrtab_tab").removeClass("active");
});

$("#tmtab").click(function(){
  $("#lmtab_contents").addClass("hidden");
  $("#tmtab_contents").removeClass("hidden");
  $("#pbdtab_contents").addClass("hidden");
  $("#mttab_contents").addClass("hidden");
  $("#mrtab_contents").addClass("hidden");  
  $("#lmtab_tab").removeClass("active");
  $("#tmtab_tab").addClass("active");
  $("#pbdtab_tab").removeClass("active");
  $("#mttab_tab").removeClass("active");
  $("#mrtab_tab").removeClass("active");
});

$("#pbdtab").click(function(){
  $("#lmtab_contents").addClass("hidden");
  $("#tmtab_contents").addClass("hidden");
  $("#pbdtab_contents").removeClass("hidden");
  $("#mttab_contents").addClass("hidden");
  $("#mrtab_contents").addClass("hidden");
  $("#lmtab_tab").removeClass("active");
  $("#tmtab_tab").removeClass("active");
  $("#pbdtab_tab").addClass("active");
  $("#mttab_tab").removeClass("active");
  $("#mrtab_tab").removeClass("active");
});

$("#mttab").click(function(){
  $("#lmtab_contents").addClass("hidden");
  $("#tmtab_contents").addClass("hidden");
  $("#pbdtab_contents").addClass("hidden");
  $("#mttab_contents").removeClass("hidden");
  $("#mrtab_contents").addClass("hidden");
  $("#lmtab_tab").removeClass("active");
  $("#tmtab_tab").removeClass("active");
  $("#pbdtab_tab").removeClass("active");
  $("#mttab_tab").addClass("active");
  $("#mrtab_tab").removeClass("active");
});

$("#mrtab").click(function(){
  $("#lmtab_contents").addClass("hidden");
  $("#tmtab_contents").addClass("hidden");
  $("#pbdtab_contents").addClass("hidden");
  $("#mttab_contents").addClass("hidden");
  $("#mrtab_contents").removeClass("hidden");
  $("#lmtab_tab").removeClass("active");
  $("#tmtab_tab").removeClass("active");
  $("#pbdtab_tab").removeClass("active");
  $("#mttab_tab").removeClass("active");
  $("#mrtab_tab").addClass("active");
});

$("#lmsel").change(function(){
  refreshSubmitButtons();
});

$("#tmsel").change(function(){
  refreshSubmitButtons();
});

$("#pbdsel").change(function(){
  refreshSubmitButtons();
});

$("#mtsel").change(function(){
  refreshSubmitButtons();
});

$("#mrsel").change(function(){
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

$("#inputtext2").change(function(){
  refreshSubmitButtons();
});

$("#inputtext2").keypress(function(event){
  refreshSubmitButtons();
});

$("#inputtext2").keyup(function(event){
  refreshSubmitButtons();
});
$("#inputtext2").keydown(function(event){
  refreshSubmitButtons();
});

$("#inputtext3").change(function(){
  refreshSubmitButtons();
});

$("#inputtext3").keypress(function(event){
  refreshSubmitButtons();
});

$("#inputtext3").keyup(function(event){
  refreshSubmitButtons();
});
$("#inputtext3").keydown(function(event){
  refreshSubmitButtons();
});

$("#inputtext4").keypress(function(event){
  refreshSubmitButtons();
});

$("#inputtext4").keyup(function(event){
  refreshSubmitButtons();
});
$("#inputtext4").keydown(function(event){
  refreshSubmitButtons();
});



$(document).ready(function(){
  $("form#form-lmtab").submit(false);
  $("form#form-tmtab").submit(false);
  $("form#form-pbdtab").submit(false);
  $("form#form-mttab").submit(false);
  $("form#from-mrtab").submit(false);
  refreshSubmitButtons();  
});

