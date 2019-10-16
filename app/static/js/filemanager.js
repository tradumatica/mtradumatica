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
        $('#filelist').DataTable().ajax.reload();
      }, 5000);
      $('#filelist').DataTable().ajax.reload();
    });

    this.on("canceled", function(file) {
      this.removeFile(file);
    });
  },
  autoProcessQueue: true
};

$(document).ready(function() {
  $('body .dropdown-toggle').dropdown(); 

  let table = $('#filelist').DataTable({
    serverSide: true,
    ajax: {
      url: "actions/file-list",
      type: "POST"
    },
    columnDefs: [{
      orderable:false,
      targets:[0,7]
    }],
    order: [
      [6, "desc"]
    ],
    createdRow: function (row, data, index) {
      addFormatedDateToDatatables(row,6);
    },
    language: datatables_lang
  });

  $('#filelist').on('draw.dt', function() {
    let seleclang_id = "";

    $('td').on('click', function(){
      let col = $(this).parent().children().index($(this));

      if (col == 2) {
        let lang_prev = $(this).html().replace(/^\s+|\s+$/g, '');
        $("div.seleclang").removeClass("bg-primary");
        $(`div.seleclang[lang = '${lang_prev}']`).addClass("bg-primary");
        $('#lang-dialog').modal("show");
        let mystr = $(this).parent().html();
        seleclang_id = parseInt(mystr.split('id="checkbox-')[1].split('"')[0]);
      }
    });

    $('span.glyphicon-eye-open').on('click', function() {
      $.ajax({
        url: "actions/file-peek/" + $(this).attr("id").substring("peek-".length),
        dataType: "json"
      }).done(function(data) {
        $('#peek-title').text(data.filename);

        let r = "";
        for (let i = 0; i < data.lines.length; i++) {
          r += data.lines[i] + "\n";
        }

        $('#peek-body').text(r);
        $('#myModal').modal("show");
      });
    });

    $('span.glyphicon-download-alt').on('click', function() {
      window.location.href = "actions/file-download/" + $(this).attr("id").substring("download-".length);
    });

    $('input.file_checkbox').on('change', function() {
      if($('#checkbox_all').is(":checked")) {
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

    $('#checkbox_all').change(function() {
      $(this).removeClass("checkbox-inconsistent");
      if($(this).is(":checked"))
      {
        $('.file_checkbox').prop("checked", true);
        $('#delete_all').addClass("trashbin-enabled");
      }
      else
      {
        $('.file_checkbox').prop("checked", false);
        $('#delete_all').removeClass("trashbin-enabled");
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
          }).done(function(){
            table.ajax.reload();
            $('#delete_all').removeClass("trashbin-enabled");
          });
        }
      });

      $('#checkbox_all').prop("checked", false);
      $('#checkbox_all').removeClass("checkbox-inconsistent")
      $('#delete_all').removeClass("trashbin-enabled");
    });

    $('.seleclang').click(function() {
      seleclang_lang = $(this).attr("lang");
      $.ajax({
        url: "actions/file-setlang/" + seleclang_id + "/" + seleclang_lang
      }).done(function(){
        table.ajax.reload();  
      });

      $('#lang-dialog').modal("hide");
    });
  });
});