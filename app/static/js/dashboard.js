

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


$("#system_tab").click(function(){
  $("#system_tab_contents").removeClass("hidden");
  $("#users_tab_contents").addClass("hidden");
  $("#queue_tab_contents").addClass("hidden");
  $("#space_tab_contents").addClass("hidden");
  $("#system_tab").addClass("active");
  $("#users_tab").removeClass("active");
  $("#queue_tab").removeClass("active");
  $("#space_tab").removeClass("active");
});

$("#users_tab").click(function(){
  $("#system_tab_contents").addClass("hidden");
  $("#users_tab_contents").removeClass("hidden");
  $("#queue_tab_contents").addClass("hidden");
  $("#space_tab_contents").addClass("hidden");
  $("#system_tab").removeClass("active");
  $("#users_tab").addClass("active");
  $("#queue_tab").removeClass("active");
  $("#space_tab").removeClass("active");
});

$("#queue_tab").click(function(){
  $("#system_tab_contents").addClass("hidden");
  $("#users_tab_contents").addClass("hidden");
  $("#queue_tab_contents").removeClass("hidden");
  $("#space_tab_contents").addClass("hidden");
  $("#system_tab").removeClass("active");
  $("#users_tab").removeClass("active");
  $("#queue_tab").addClass("active");
  $("#space_tab").removeClass("active");
});

$("#space_tab").click(function(){
  $("#system_tab_contents").addClass("hidden");
  $("#users_tab_contents").addClass("hidden");
  $("#queue_tab_contents").addClass("hidden");
  $("#space_tab_contents").removeClass("hidden");
  $("#system_tab").removeClass("active");
  $("#users_tab").removeClass("active");
  $("#queue_tab").removeClass("active");
  $("#space_tab").addClass("active");
});

$("#refresh_dashboard").click(function(){
  document.location.reload();
});
