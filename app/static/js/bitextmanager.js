$(document).ready(function() {
  $('body .dropdown-toggle').dropdown(); 

  let table = $('#bitextlist').DataTable({
    serverSide: true,
    ajax: {
      url: "actions/bitext-list",
      type: "POST"
    },
    columnDefs: [{
      orderable:false,
      targets:[0,5]
    }],
    order: [[4, "desc"]],
    createdRow : function(row, data, index) {
      addFormatedDateToDatatables(row, 4);
    },
    language: datatables_lang
  });

  var idOfBitextToAppend = -1;
  $('#bitextlist').on('draw.dt', function() {
    $('span.glyphicon-eye-open').off('click').on('click', function() {
      $.ajax({
        url: "actions/bitext-peek/" + $(this).attr("id").substring("peek-".length),
        dataType: "json"
      }).done(function(data) {
        $('#peek-title').text(data.filename);

        let r1 = "";
        let r2 = "";
        for (let i = 0; i < data.lines1.length; i++){
          r1 += data.lines1[i] + "\n";
          r2 += data.lines2[i] + "\n";
        }

        $('#peek-body-1').text(r1);
        $('#peek-body-2').text(r2);
        $('#myModal').modal("show");
      });
    });

    $('tbody span.glyphicon-plus-sign').off('click').on('click', function() {
      //Load files available for each language pair, populate options
      //and display modal
      let domidparts = $(this).attr("id").split("-");
      let bitextid = domidparts[1];
      let bitextl1 = domidparts[2];
      let bitextl2 = domidparts[3];

      //asign id to global variable
      idOfBitextToAppend = bitextid;

      $.ajax("actions/file-plainlist/" + bitextl1).done(function(data) {
        $('#labsourcesel').text(`${bitextl1} side`);
        $('#sourcesel').empty();
        $.each(data.data, function(i, item) {
          let option = document.createElement('option');
          $(option).val(item.id).html(`${item.name} / ${item.nlines}`);
          $("#sourcesel").append(option);
        });

        $.ajax("actions/file-plainlist/" + bitextl2).done(function(data) {
          $('#labtargetsel').text(`${bitextl2} side`);
          $('#targetsel').empty();
          $.each(data.data, function(i, item) {
            let option = document.createElement('option');
            $(option).val(item.id).html(`${item.name} / ${item.nlines}`);
            $("#targetsel").append(option);
          });
        })
      });

      //TODO: load also TMX available

      $('#modal-append').modal("show");
    });

    $('input.file_checkbox').off('change').on('change', function() {
      if ($('#checkbox_all').is(":checked")) {
        $('#checkbox_all').addClass("checkbox-inconsistent");
      }

      let any = false;
      $('.file_checkbox').each(function() {
        if($(this).is(":checked")) {
          any = true;
          return false;
        }
      });

      if (any) {
        $('#delete_all').addClass("trashbin-enabled");
      } else {
        $('#delete_all').removeClass("trashbin-enabled");
        $('#checkbox_all').prop("checked", false);
        $('#checkbox_all').removeClass("checkbox-inconsistent");
      }
    });

    $('#checkbox_all').off('change').on('change', function() {
      $(this).removeClass("checkbox-inconsistent");
      if ($(this).is(":checked")) {
        $('.file_checkbox').prop("checked", true);
        $('#delete_all').addClass("trashbin-enabled");
      } else {
        $('.file_checkbox').prop("checked", false);
        $('#delete_all').removeClass("trashbin-enabled");
      }
    });


    $('#delete_all').off('click').on('click', function() {
      $('.file_checkbox').each(function () {
        if($(this).is(":checked")) {
          $.ajax({
            url: "actions/bitext-delete/" + $(this).attr("id").substring("checkbox-".length)
          }).done(function(){
            table.ajax.reload();
            $('#delete_all').removeClass("trashbin-enabled");
          });
        }
      }).done(function(){
        table.ajax.reload();
      });

      $('#checkbox_all').prop("checked", false);
      $('#checkbox_all').removeClass("checkbox-inconsistent")
      $('#delete_all').removeClass("trashbin-enabled");
    });

    //Put selected language in form
    $('.seleclang').off('click').on('click', function() {
      let seleclang_lang = $(this).attr("lang");
      $('#inputLanguage' + languagenumber).text(seleclang_lang);
      $('#lang-dialog').modal("hide");
      validateInputLanguage(['inputLanguage1','inputLanguage2']);
    });
  });

  //Show modal for creating a new bitext
  $('#addbutton').off('click').on('click', function() {
    $('#modal-add').modal("show");
  });

  let languagenumber="0";
  //Show language selection modal on top ot if
  $('#inputLanguage1').off('click').on('click', function(){
    $('#lang-dialog').modal("show");
    languagenumber="1";
  });

  $('#inputLanguage2').off('click').on('click', function(){
    $('#lang-dialog').modal("show");
    languagenumber="2";
  });

  //submit create form. validate elements that cannot be validated with the plugin
  $('#buttonCreate').off('click').on('click', function(){
    let resultValForm = $('#form-new-bitext').valid();
    let resultValLanguage = validateInputLanguage(['inputLanguage1','inputLanguage2']);
    if (resultValForm && resultValLanguage) {
      $.ajax(`actions/bitext-create/${$('#inputName').val()}/${$('#inputLanguage1').text()}/${$('#inputLanguage2').text()}`)
      .done(function() {
        table.ajax.reload();
        $('#modal-add').modal("hide");
      }).fail(function() {
        //TODO: better error handling
        console.log("error");
      }).always(function() {
        //Always close modal?
      });
    }
  })

  //submit content add form
  $('#buttonAddcontent').off('click').on('click', function(){
    if ($('.nav-tabs .active a').attr("href") === "#tab1") {
      if ($('#form-add-files-to-bitext').valid()) {
        $.ajax(`actions/bitext-add-files/${idOfBitextToAppend}/${$("#sourcesel").val()}/${$("#targetsel").val()}`)
        .done(function() {
          table.ajax.reload();
          //close modal
          $('#modal-append').modal("hide");
        }).fail(function() {
          //TODO: better error handling
          console.log("error");
        }).always(function() {
          //Always close modal?
        });
      }
    } else {
      //Inser here coder for validating and submitting a TMX
    }
  })

  //Validation of new bitext form
  $('#form-new-bitext').validate({
    rules: {
      inputName: {
        required: true
      }
    },
    highlight: function(element) {
      $(element).closest('.form-group').addClass('has-error');
    },
    unhighlight: function(element) {
      $(element).closest('.form-group').removeClass('has-error');
    },
    errorElement: 'span',
    errorClass: 'help-block',
    errorPlacement: function(error, element) {
      if (element.parent('.input-group').length) {
        error.insertAfter(element.parent());
      } else {
        error.insertAfter(element);
      }
    }
  });

  //Validation of form for appending context to bitext
  $('#form-add-files-to-bitext').validate({
    rules: {
      sourcesel: {
        required: true
      },
      targetsel: {
        required: true
      }
    },
    highlight: function(element) {
      $(element).closest('.form-group').addClass('has-error');
    },
    unhighlight: function(element) {
      $(element).closest('.form-group').removeClass('has-error');
    },
    errorElement: 'span',
    errorClass: 'help-block',
    errorPlacement: function(error, element) {
      if (element.parent('.input-group').length) {
        error.insertAfter(element.parent());
      } else {
        error.insertAfter(element);
      }
    }
  });
});
