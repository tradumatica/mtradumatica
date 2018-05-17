

table=$('#languagemodellist').DataTable({

  serverSide: true,
  ajax: {
          url: "actions/languagemodel-list",
          type: "POST"},
  columnDefs: [{ orderable:false,
                 targets:[0,5,6]}],
  order : [[4, "desc"]],
  createdRow : function ( row, data, index ) {
	id= $('td', row).eq(0).find('input').attr('id').split("-")[1];
	spanid="training-time-"+id;
	startDateTimeStr = $('td', row).eq(4).text();
	curContent=$('td', row).eq(5).text();
	if(curContent === "")
	{
		//Show if training has not finished yet
		$('td', row).eq(5).html('<span class="label label-primary" id="'+spanid+'"></span>');

		updater = init_clock(startDateTimeStr,spanid,id);
		timerid = setInterval(updater,500);
		running_intervals.push(timerid);

		init_status_checker("actions/status-languagemodel",id);
	}
	else {
		//Training has finished: show green label
		startDate=parseDate(startDateTimeStr);
		endDate=parseDate(curContent);
		diffStr=formatDateDiff(startDate,endDate);

		//If we have an error icon, label will be "danger"

		if($('td', row).eq(6).find('span').attr('id').split("-")[0] === "exiterror"){
			labeltype="danger"
		}else{
			labeltype="success"
		}
		$('td', row).eq(5).html('<span class="label label-'+labeltype+'" id="'+spanid+'">'+diffStr+'</span>');
	}
	//Once counters are initialized, display the date according to client's locale
	timestamp=parseDate(startDateTimeStr);
	date = new Date(timestamp);
	$('td', row).eq(4).text(date.toLocaleDateString()+" "+date.toLocaleTimeString());

        }
});


$('#languagemodellist').on('preXhr.dt', function ( e, settings, data ) {
	   resetIntervals();
   } )


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

//Add counter to training time

  if(any)
  {
    $('#delete_all').addClass("trashbin-enabled");
  }
  else
  {
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
  $('.file_checkbox').each(function () {
    if($(this).is(":checked"))
    {
      my_str = $(this).attr("id");
      $.ajax({
        url: "actions/languagemodel-delete/" + $(this).attr("id").substring("checkbox-".length)
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
  $('#dele[Ate_all').removeClass("trashbin-enabled");

});

//Put selected language in form, list monolingual corpora
$('.seleclang').click(function() {
  seleclang_lang = $(this).attr("lang");
  $('#inputLanguage'+languagenumber).text(seleclang_lang);
  $.ajax( "actions/monolingualcorpus-plainlist/"+seleclang_lang )
     .done(function(data) {
   		 //fill select with monolingual corpora
		 $('#selMonolingualCorpus').empty();
		if(data.data.length  > 0){
		 	$.each(data.data, function(i, item) {
		       $("#selMonolingualCorpus").append($("<option></option>").val(item.id).html(item.name+" / "+item.nlines));
		 	});
		}
		else{
			//$("#selMonolingualCorpus").append($("<option></option>").val(null).html(""));
		}

     }).always(function() {
        //Always close modal
        $('#lang-dialog').modal("hide");
		validateInputLanguage(["inputLanguage1"]);
     });

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
	resultValForm=$('#form-new-languagemodel').valid();
	resultValLanguage=validateInputLanguage(["inputLanguage1"]);

	if(resultValForm && resultValLanguage){
		$.ajax( "actions/languagemodel-create/"+$('#inputName').val()+"/"+$('#inputLanguage1').text()+"/"+$('#selMonolingualCorpus').val() )
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


//Validate create LM form
$('#form-new-languagemodel').validate({
	   rules: {
		   name: {
			   required: true
		   },
		   selMonolingualCorpus: {
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
