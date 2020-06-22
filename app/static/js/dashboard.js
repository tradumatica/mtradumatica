
$(document).ready(function() {
  $('body .dropdown-toggle').dropdown(); // avoid dropdown problems (bootstrap/datatables conflict)

  let table_ul = $('#userlist').DataTable({
    serverSide: true,
    ajax: { 
      url: "actions/user-list",
      type: "POST"
    },
    columnDefs: [{
      orderable: false,
      targets:[0, 7]
    }],
    order: [
      [6, "desc"]
    ],
    language: datatables_lang
  });

  let table_mt = $('#mtlist').DataTable({
    serverSide: true,
    ajax: {
      url: "actions/mt-list",
      type: "POST"
    },
    columnDefs: [{
      orderable: false,
      targets:[0, 6]
    }],
    order: [
      [5, "desc"]
    ],
    language: datatables_lang
  });

  let table_queue = $('#tasklist').DataTable({
    serverSide: true,
    bFilter: false,
    ordering: false,
    paging: false,
    ajax: {
      url: 'actions/queue-list',
      type: 'post'
    },
    columnDefs: [
      {
        targets: 0,
        render: function(data, type, row) {
          return `<span class="checkbox"><input type="checkbox" id="ul-checkbox-${row[0]}" data-task-id="${row[0]}" class="task_checkbox" /></div>`
        }
      },
      {
        targets: 3,
        render: function(data, type, row) {
          let date_string = row[3];
          let date_utc = parseDate(date_string);
          let date_local = new Date(date_utc.getTime() - (date_utc.getTimezoneOffset() * 60000))
          return `${date_utc.toLocaleDateString()} ${date_utc.toLocaleTimeString()}`
        }
      },
      {
        targets: 6,
        sortable: false,
        searchable: false,
        render: function(data, type, row) {
          return "";
        }
      }
    ],
    language: datatables_lang
  });

  $('#disable_newusers').on('change', function() {
    let state = $(this).is(":checked");
    $.ajax({
      url: "/actions/user-login/" + (state ? 0 : 1)
    });
  })

  $('#tasklist').on('draw.dt', function() {
    $('input.task_checkbox').off('change').on('change', function() {
      if ($('#task_checkbox_all').is(":checked")) {
        $('#task_checkbox_all').addClass("checkbox-inconsistent");
      }

      let any = false;
      $('.task_checkbox').each(function() {
        if ($(this).is(":checked")) {
          any = true;
          return false;
        }
      });

      if (any) {
        $('#tasks_delete').addClass("trashbin-enabled");
      } else {
        $('#tasks_delete').removeClass("trashbin-enabled");
        $('#task_checkbox_all').prop("checked", false);
        $('#task_checkbox_all').removeClass("checkbox-inconsistent");
      }
    });

    $('#task_checkbox_all').off('change').on('change', function() {
      $(this).removeClass("checkbox-inconsistent");
      if ($(this).is(":checked")) {
        $('.task_checkbox').prop("checked", true);
        $('#tasks_delete').addClass("trashbin-enabled");
      } else {
        $('.task_checkbox').prop("checked", false);
        $('#tasks_delete').removeClass("trashbin-enabled");
      }
    });

    $('#tasks_delete').off('click').on('click', function() {
      $('.task_checkbox').each(function () {
        if($(this).is(":checked")) {
          $.ajax({
            url: "/actions/revoke-task",
            type: "post",
            data: {
              task_id: $(this).attr("data-task-id")
            }
          }).done(function(){
            table_queue.ajax.reload();
            $('#tasks_delete').removeClass("trashbin-enabled");
          });
        }
      });

      $('#task_checkbox_all').prop("checked", false);
      $('#task_checkbox_all').removeClass("checkbox-inconsistent")
      $('#tasks_delete').removeClass("trashbin-enabled");
    });
  });

  $('#mtlist').on('draw.dt', function() {
    $('input.mt_checkbox').off('change').on('change', function() {
      if ($('#mt_checkbox_all').is(":checked")) {
        $('#mt_checkbox_all').addClass("checkbox-inconsistent");
      }

      let any = false;
      $('.mt_checkbox').each(function() {
        if ($(this).is(":checked")) {
          any = true;
          return false;
        }
      });

      if (any) {
        $('#ml_delete_all').addClass("trashbin-enabled");
      } else {
        $('#ml_delete_all').removeClass("trashbin-enabled");
        $('#mt_checkbox_all').prop("checked", false);
        $('#mt_checkbox_all').removeClass("checkbox-inconsistent");
      }
    });

    $('#mt_checkbox_all').change(function() {
      $(this).removeClass("checkbox-inconsistent");
      if ($(this).is(":checked")) {
        $('.mt_checkbox').prop("checked", true);
        $('#ml_delete_all').addClass("trashbin-enabled");
      } else {
        $('.mt_checkbox').prop("checked", false);
        $('#ml_delete_all').removeClass("trashbin-enabled");
      }
    });

    $('#ml_delete_all').off('click').on('click', function() {
      $('.mt_checkbox').each(function() {
        if ($(this).is(":checked")) {
          $.ajax({
						url: "actions/translator-delete/" + $(this).attr("id").substring("mt_checkbox-".length)
					}).done(function(){
						table_mt.ajax.reload();
						$('#delete_all').removeClass("trashbin-enabled");
					});
        }
      })
    });
  });

  $('#userlist').on('draw.dt', function() {
    $('.btn-ban, .btn-unban').off('click').on('click', function() {
      let id = $(this).attr("data-user-id");
      let state = $(this).hasClass('btn-ban') ? 1 : 0;
      $.ajax({
        url: "/actions/ban/" + id + "/" + state
      }).done(function() {
        table_ul.ajax.reload();
      })
    });

    $('input.user_checkbox').off('change').on('change', function() {
      if ($('#ul_checkbox_all').is(":checked")) {
        $('#ul_checkbox_all').addClass("checkbox-inconsistent");
      }

      let any = false;
      $('.user_checkbox').each(function() {
        if ($(this).is(":checked")) {
          any = true;
          return false;
        }
      });

      if (any) {
        $('#ul_delete_all').addClass("trashbin-enabled");
      } else {
        $('#ul_delete_all').removeClass("trashbin-enabled");
        $('#ul_checkbox_all').prop("checked", false);
        $('#ul_checkbox_all').removeClass("checkbox-inconsistent");
      }
    });

    $('#ul_checkbox_all').off('change').on('change', function() {
      $(this).removeClass("checkbox-inconsistent");
      if ($(this).is(":checked")) {
        $('.user_checkbox').prop("checked", true);
        $('#ul_delete_all').addClass("trashbin-enabled");
      } else {
        $('.user_checkbox').prop("checked", false);
        $('#ul_delete_all').removeClass("trashbin-enabled");
      }
    });

    $('#ul_delete_all').off('click').on('click', function() {
      $('.user_checkbox').each(function () {
        if($(this).is(":checked")) {
          $.ajax({
            url: "/actions/delete-user/" + $(this).attr("data-user-id"),
            type: "get",
            data: {
              task_id: $(this).attr("data-task-id")
            }
          }).done(function(){
            table_ul.ajax.reload();
            $('#ul_delete_all').removeClass("trashbin-enabled");
          });
        }
      });

      $('#ul_checkbox_all').prop("checked", false);
      $('#ul_checkbox_all').removeClass("checkbox-inconsistent")
      $('#ul_delete_all').removeClass("trashbin-enabled");
    });
  });

  $('.nav-tabs a').on('shown.bs.tab', function(e) {
    $(".table").DataTable().columns.adjust().draw();
  });

  $("#refresh_dashboard").click(function(){
    document.location.reload();
  });
});

