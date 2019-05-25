function refreshSubmitButtons(){
  if ($("#htrans").val().trim() == "" || $("#mt").val().trim() == "")
  {
    $("#evaluate").addClass("disabled");
  }
  else
  {
    $("#evaluate").removeClass("disabled");
  }
}



function populate_table(result){
  if(typeof(result.error) === "undefined")
  {
    // empty possible pre-existing rows
    $("#tscores > tbody").empty();
    $(result.records).each(function(r){
      var mytr = [];
      mytr.push("<tr>");
      mytr.push("<td>"+this.name+"</td>");
      mytr.push("<td align='right'>"+this.bleu.toFixed(2)+"</td>");
      mytr.push("<td align='right'>"+this.chrf3.toFixed(2)+"</td>");
      mytr.push("<td align='right'>"+this.beer.toFixed(2)+"</td>");
      mytr.push("<td align='right'>"+this.ter.toFixed(2)+"</td>");
      mytr.push("<td align='right'>"+this.wer.toFixed(2)+"</td>");
      mytr.push("</tr>");
      $("#tscores tbody").append(mytr.join(""));
      $("#scores").removeClass("hidden");
    });
  }
  else
  {
    /* set error message */
  }
}


$("#evalform").submit(function(e){
  return false;
});

$("#evaluate").click(function(){
  var form = $("#evalform")[0];
  var data = new FormData(form);
  
  $("#my-please-wait").modal("show");

  $.ajax({
    type: "POST",
    enctype: "multipart/form-data",
    url: "actions/perform-evaluation",
    cache: false,
    contentType: false,
    processData: false,
    data: data,
    success: function(result){
      /* Create table */
      populate_table(result);
      $("#my-please-wait").modal("hide");
    }
  });
});

$("#htrans").change(function(){
  refreshSubmitButtons();
});

$("#mt").change(function(){
  refreshSubmitButtons();
});
