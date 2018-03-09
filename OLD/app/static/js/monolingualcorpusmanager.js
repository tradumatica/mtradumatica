
table=$('#monolingualcorpuslist').DataTable({

  serverSide: true,
  ajax: {
          url: "actions/monolingualcorpus-list",
          type: "POST"},
  columnDefs: [{ orderable:false,
                 targets:[0,5]}],
  order : [[4, "desc"]],
  createdRow : function ( row, data, index ) {
	 addFormatedDateToDatatables(row,4);
  }
});


$('body').on('click', 'span.glyphicon-eye-open', function() {

  $.ajax({
    url: "actions/monolingualcorpus-peek/" + $(this).attr("id").substring("peek-".length),
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



var idOfMonocorpusToAppend = -1;
$('tbody').on('click', 'span.glyphicon-plus-sign', function() {
   //Load files available for each language pair, populate options
   //and display modal
   domidparts=$(this).attr("id").split("-")
   monocorpusid=domidparts[1]
   monocorpusl1=domidparts[2]

   //asign id to global variable
   idOfMonocorpusToAppend=monocorpusid

   $.ajax( "actions/file-plainlist/"+monocorpusl1 )
  .done(function(data) {
	$('#sourcesel').empty();
	$.each(data.data, function(i, item) {
      $("#sourcesel").append($("<option></option>").val(item.id).html(item.name+" / "+item.nlines));
	});
	$('#modal-append').modal("show");
  })
   //TODO: load also TMX available


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
  $('.file_checkbox').each(function () {
    if($(this).is(":checked"))
    {
      my_str = $(this).attr("id");
      $.ajax({
        url: "actions/monolingualcorpus-delete/" + $(this).attr("id").substring("checkbox-".length)
      });
    }
  });

  $('#checkbox_all').prop("checked", false);
  $('#checkbox_all').removeClass("checkbox-inconsistent")
  $('#delete_all').removeClass("icon-enabled");

  table.ajax.reload();
});

//Put selected language in form
$('.seleclang').click(function() {
  seleclang_lang = $(this).attr("lang");
  $('#inputLanguage'+languagenumber).text(seleclang_lang);
  $('#lang-dialog').modal("hide");
  validateInputLanguage(['inputLanguage1']);
});

//Show modal for creating a new bitext
$('#addbutton').click(function() {
  $('#modal-add').modal("show");
  });

var languagenumber="1";
//Show language selection modal on top ot if
$('#inputLanguage1').click(function(){
$('#lang-dialog').modal("show");
})


//submit create form
$('#buttonCreate').click(function(){

	resultValForm=$('#form-new-monolingualcorpus').valid();
	resultValLanguage=validateInputLanguage(['inputLanguage1']);

	if(resultValForm && resultValLanguage){
		$.ajax( "actions/monolingualcorpus-create/"+$('#inputName').val()+"/"+$('#inputLanguage1').text() )
	  .done(function() {
	    table.ajax.reload();
		//close modal
		$('#modal-add').modal("hide");
	  })
	  .fail(function() {
		 //TODO: better error handling
	    console.log( "error" );
	  }).always(function() {
	    //Always close modal?
	  });
  }
})

//submit content add form
$('#buttonAddcontent').click(function(){

	if($('.nav-tabs .active a').attr("href") === "#tab1"){
		if($('#form-add-files-to-monolingualcorpus').valid()){

			$.ajax( "actions/monolingualcorpus-add-files/"+idOfMonocorpusToAppend+"/"+$("#sourcesel").val() )
		  .done(function() {
		    table.ajax.reload();
			//close modal
			$('#modal-append').modal("hide");
		  })
		  .fail(function() {
			 //TODO: better error handling
		    console.log( "error" );
		  }).always(function() {
		    //Always close modal?
		  });
  		}
  }else{
	  //INsert here code for TMX
  }
})


//Validation of new monolingual corpus form
$('#form-new-monolingualcorpus').validate({
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
		   if(element.parent('.input-group').length) {
			   error.insertAfter(element.parent());
		   } else {
			   error.insertAfter(element);
		   }
	   }
   });

   //Validation of form for appending context to monolingual corpus
   $('#form-add-files-to-monolingualcorpus').validate({
		  rules: {
			  sourcesel: {
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
			  if(element.parent('.input-group').length) {
				  error.insertAfter(element.parent());
			  } else {
				  error.insertAfter(element);
			  }
		  }
	  });
