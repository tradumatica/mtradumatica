var table = $('#filelist').DataTable({
  serverSide: true,
  ajax: {
          url: "actions/file-list",
          type: "POST"},
  columnDefs: [{ orderable:false,
                 targets:[0,7]}],
  order : [[6, "desc"]],
  createdRow : function ( row, data, index ) {
	addFormatedDateToDatatables(row,6);
  }
});



Dropzone.options.myDropZone = { // camelized id
  paramName: "file",
  maxFilesize: 1024, // 1 GB
  filesizeBase: 1000,
  //maxFiles: 40, // needed?
  init: function() {
    this.on("complete", function(file) {
      obj = this;
      setTimeout(function() {
        obj.removeFile(file);
        table.ajax.reload();
      }, 5000);
      table.ajax.reload();
    });


    this.on("canceled", function(file) {
      this.removeFile(file);
    });
  },
  autoProcessQueue: true
};


var seleclang_id = "";

$('body').on('click','td', function(){
  var col = $(this).parent().children().index($(this));
  var row = $(this).parent().parent().children().index($(this).parent());

  if(col == 2)
  {
    lang_prev = $(this).html().replace(/^\s+|\s+$/g, '');
    $("div.seleclang").removeClass("bg-primary");
    $("div.seleclang[lang = '" + lang_prev + "']").addClass("bg-primary");
    $('#lang-dialog').modal("show");
    mystr = $(this).parent().html();
    seleclang_id = parseInt(mystr.split('id="checkbox-')[1].split('"')[0]);
  }
});


$('body').on('click', 'span.glyphicon-eye-open', function() {

  $.ajax({
    url: "actions/file-peek/" + $(this).attr("id").substring("peek-".length),
    dataType: "json"
  }).done(function(data) {
    $('#peek-title').text(data.filename);

    r = "";
    for(i = 0; i < data.lines.length; i++)
      r += data.lines[i] + "\n";

    $('#peek-body').text(r);
    $('#myModal').modal("show");
  });
});

$('body').on('click', 'span.glyphicon-download-alt', function() {
  $.ajax({
    url: "actions/file-download/" + $(this).attr("id").substring("download-".length)
  });
});

$('body').on('change', 'input.file_checkbox', function() {
  if($('#checkbox_all').is(":checked"))
  {
    $('#checkbox_all').addClass("checkbox-inconsistent");
  }

  var any = false;
  $('.file_checkbox').each(function() {
    if($(this).is(":checked"))
    {
      any = true;
      return false;
    }
  });

  if(any)
  {
    $('#delete_all').addClass("icon-enabled");
  }
  else
  {
    $('#delete_all').removeClass("icon-enabled");
    $('#checkbox_all').prop("checked", false);
    $('#checkbox_all').removeClass("checkbox-inconsistent");
  }

});

$('#checkbox_all').change(function() {
  $(this).removeClass("checkbox-inconsistent");
  if($(this).is(":checked"))
  {
    $('.file_checkbox').prop("checked", true);
    $('#delete_all').addClass("icon-enabled");
  }
  else
  {
    $('.file_checkbox').prop("checked", false);
    $('#delete_all').removeClass("icon-enabled");
  }
});


$('#delete_all').click(function() {
  var url = "actions/file-delete/";
  $('.file_checkbox').each(function () {
    if($(this).is(":checked"))
    {
      my_str = $(this).attr("id");
      $.ajax({
        url: "actions/file-delete/" + $(this).attr("id").substring("checkbox-".length)
      });
    }
  });

  $('#checkbox_all').prop("checked", false);
  $('#checkbox_all').removeClass("checkbox-inconsistent")
  $('#delete_all').removeClass("icon-enabled");

  table.ajax.reload();
});

$('.seleclang').click(function() {
  seleclang_lang = $(this).attr("lang");
  $.ajax({
    url: "actions/file-setlang/" + seleclang_id + "/" + seleclang_lang
  });

  $('#lang-dialog').modal("hide");
  table.ajax.reload();
});
