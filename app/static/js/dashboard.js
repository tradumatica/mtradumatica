
$(document).ready(function() {
  $('body .dropdown-toggle').dropdown(); // avoid dropdown problems (bootstrap/datatables conflict)

  var table_ul = $('#userlist').DataTable({
    serverSide: true,
    ajax: { url: "actions/user-list",
            type: "POST" },
    columnDefs: [{ orderable: false,
                  targets:[0, 7] }],
    order: [[6, "desc"]],
    language: datatables_lang
  });

  var table_mt = $('#mtlist').DataTable({
    serverSide: true,
    ajax: { url: "actions/mt-list",
            type: "POST" },
    columnDefs: [{ orderable: false,
                  targets:[0, 6] }],
    order: [[5, "desc"]],
    language: datatables_lang
  });

  let table_queue = $('#tasklist').DataTable({
    serverSide: true,
    ajax: {
      url: 'actions/queue-list',
      type: 'post'
    },
    columnDefs: [
      {
        targets: 2,
        render: function(data, type, row) {
          let date_string = row[2];
          let date_utc = new Date(date_string)
          let date_local = new Date(date_utc.getTime() - (date_utc.getTimezoneOffset() * 60000))
          return `${date_local.toLocaleDateString()} ${date_local.toLocaleTimeString()}`
        }
      }
    ],
    language: datatables_lang
  })

  $('.nav-tabs a').click(function (e) {
    e.preventDefault()
    $(this).tab('show')

  });

  $('.nav-tabs a').on('shown.bs.tab', function(e) {
    $(".table").DataTable().columns.adjust().draw()
  })

  $("#refresh_dashboard").click(function(){
    document.location.reload();
  });
});

