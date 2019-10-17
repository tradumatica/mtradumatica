function refreshSubmitButtons() {
  if ($("#htrans").val().trim() == "" || $("#mt").val().trim() == "") {
    $("#evaluate").addClass("disabled");
  } else {
    $("#evaluate").removeClass("disabled");
  }
}

function populate_table(result) {
  if(typeof(result.error) === "undefined") {
    // empty possible pre-existing rows
    $("#tscores > tbody").empty();

    let data = []
    $(result.records).each(function(r){
      data.push({
        name: this.name,
        metrics: [
          this.bleu.toFixed(2), this.chrf3.toFixed(2),
          this.beer.toFixed(2), this.ter.toFixed(2),
          this.wer.toFixed(2)
        ]
      });
    });

    for (let record of data) {
      let tr = document.createElement('tr');
      let td = document.createElement('td');
      $(td).html(record.name);
      $(tr).append(td);

      for (let metric of record.metrics) {
        let td = document.createElement('td')
        $(td).html(metric);
        $(td).attr('style', 'text-align: right');
        $(tr).append(td)
      }

      $("#tscores tbody").append(tr)
      $("#scores").removeClass("hidden");
    }
  } else {
    /* set error message */
  }
}

$(document).ready(function() {
  $("#evalform").submit(function(e){
    return false;
  });

  $("#evaluate").click(function(){
    let form = $("#evalform")[0];
    let data = new FormData(form);
    
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
});