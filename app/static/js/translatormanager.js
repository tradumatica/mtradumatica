
table=$('#translatorlist').DataTable({

  serverSide: true,
  ajax: {
          url: "actions/translator-list",
          type: "POST"},
  columnDefs: [{ orderable:false,
                 targets:[0,6,7,8]}],
  order : [[5, "desc"]],
  createdRow : function ( row, data, index ) {

	//Id of translator represented by the row
    id= $('td', row).eq(0).find('input').attr('id').split("-")[1];

	/***** Enable training counter  *********/
	spanid="training-time-"+id;
	startDateTimeStr = $('td', row).eq(5).text();
	curContent=$('td', row).eq(6).text();
	if(curContent === "")
	{
		//Show if training has not finished yet
		$('td', row).eq(6).html('<span class="label label-primary" id="'+spanid+'"></span>');

		updater = init_clock(startDateTimeStr,spanid,id);
		timerid = setInterval(updater,500);
		running_intervals.push(timerid);

		init_status_checker("actions/status-translator",id);
	}
	else {
		//Training has finished: show green label
		startDate=parseDate(startDateTimeStr);
		endDate=parseDate(curContent);
		diffStr=formatDateDiff(startDate,endDate);
		$('td', row).eq(6).html('<span class="label label-success" id="'+spanid+'">'+diffStr+'</span>');
	}
	//Once counters are initialized, display the date according to client's locale
	timestamp=parseDate(startDateTimeStr);
	date = new Date(timestamp);
	$('td', row).eq(5).text(date.toLocaleDateString()+" "+date.toLocaleTimeString());


	/***** Enable optimization counter  *********/
	spanid="optimization-time-"+id;
	cancelid="cancel-id-"+id;
	optimizingContent=$('td', row).eq(7).text();
	parts=optimizingContent.split("#");
	if( parts.length <= 1 ){
		//If there is only one part, server returned a button, keep it as is
	}else{
		if (parts[1] !==  ""){
			//optimization has finished: display elapsed time
			startDate=parseDate(parts[0]);
			endDate=parseDate(parts[1]);
			diffStr=formatDateDiff(startDate,endDate);
			$('td', row).eq(7).html('<span class="label label-success" id="'+spanid+'">'+diffStr+'</span>');
		}else{
			//optimization is running, display counter
			$('td', row).eq(7).html('<span class="label label-primary" id="'+spanid+'"></span> <span class="glyphicon glyphicon-remove trashbin-enabled" id="'+cancelid+'"></span>');

			updater = init_clock(parts[0],spanid,id);
			timerid = setInterval(updater,500);
			running_intervals.push(timerid);

			init_status_checker("actions/status-translator-optimization",id);
		}
    }
}
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
        url: "actions/translator-delete/" + $(this).attr("id").substring("checkbox-".length)
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


$('body').on('click', 'span.glyphicon-remove', function(){
  $.ajax({
    url: "actions/optimization-kill/" + $(this).attr("id").substring("cancel-id-".length)
  }).done(function(){
    table.ajax.reload();
  });
});

//Manage optimization modal
var idOfTranslatorToOptimize = -1;
$('tbody').on('click', 'button', function() {
	domidparts=$(this).attr("id").split("-");
	//asign id to global variable
	idOfTranslatorToOptimize=domidparts[2];

	//get list of compatible bitexts, populate modal and show it
	//fill select with bitexts
	$.ajax( "actions/bitext-plainlist/"+idOfTranslatorToOptimize)
	  .done(function(data) {
	    $('#selBitextOptimize').empty();
	    if(data.data.length  > 0)
	    {
	      $.each(data.data, function(i, item){
	        $("#selBitextOptimize").append($("<option></option>").val(item.id).html(item.name+" / "+item.nlines));
	      });
	    }
	    else{
	      $("#selBitextOptimize").append($("<option></option>").val(null).html(""));
	    }
	    //SHow modal
	    $('#modal-optimize').modal("show");
	});

});

//submit optimize form
$('#buttonOptimize').click(function(){
	$.ajax( "actions/translator-optimize/"+idOfTranslatorToOptimize+"/"+$('#selBitextOptimize').val() )
  .done(function() {
	table.ajax.reload();
	//close modal
	$('#modal-optimize').modal("hide");
  })
  .fail(function() {
	 //TODO: better error handling
	console.log( "error" );
  })
});


//Put selected language in form, list monolingual corpora
$('.seleclang').click(function() {
  seleclang_lang = $(this).attr("lang");
  $('#inputLanguage'+languagenumber).text(seleclang_lang);
  validateInputLanguage(['inputLanguage1','inputLanguage2']);
  //if SL and TL are not empty, reload bitexts and language models
  if($('#inputLanguage1').text() != "" && $('#inputLanguage2').text() != ""){
	  $.ajax( "actions/languagemodel-plainlist/"+$('#inputLanguage2').text())
	     .done(function(data) {
	   		 //fill select with language models
			 $('#selLanguageModel').empty();
			if(data.data.length  > 0){
			 	$.each(data.data, function(i, item) {
			       $("#selLanguageModel").append($("<option></option>").val(item.id).html(item.name));
			 	});
			}
			else{
				$("#selLanguageModel").append($("<option></option>").val(null).html(""));
			}

			//fill select with bitexts
			$.ajax( "actions/bitext-plainlist/"+$('#inputLanguage1').text()+"/"+$('#inputLanguage2').text())
			   .done(function(data) {
				   $('#selBitext').empty();
		  			if(data.data.length  > 0){
		  			 	$.each(data.data, function(i, item) {
		  			       $("#selBitext").append($("<option></option>").val(item.id).html(item.name+" / "+item.nlines));
		  			 	});
		  			}
		  			else{
		  				$("#selBitext").append($("<option></option>").val(null).html(""));
		  			}
					//hide language selection modal
					$('#lang-dialog').modal("hide");
				   })
	     })
  }
});

//Show modal for creating a new bitext
$('#addbutton').click(function() {
  $('#modal-add').modal("show");
  });

var languagenumber="0";
//Show language selection modal on top ot if
$('#inputLanguage1').click(function(){
languagenumber="1";
$('#lang-dialog').modal("show");
})

$('#inputLanguage2').click(function(){
languagenumber="2";
$('#lang-dialog').modal("show");
})


//submit create form
$('#buttonCreate').click(function() {
  resultValFormName=$('#form-new-translator-name').valid();

  if($('.nav-tabs .active a').attr("href") === "#tab1")
  {
    resultValFormBLM = $('#form-new-translator-BLM').valid();
    resultValLanguage=validateInputLanguage(['inputLanguage1','inputLanguage2'])
    if(resultValFormName && resultValFormBLM && resultValLanguage)
    {
      $.ajax("actions/translator-create/"+$('#inputName').val()+"/"+$('#inputLanguage1').text()+"/"+$('#inputLanguage2').text()+"/"+$('#selBitext').val()+"/"+$('#selLanguageModel').val())
        .done(function() {
	  table.ajax.reload();
	  //close modal
	  $('#modal-add').modal("hide");
	})
	.fail(function() {
	  //TODO: better error handling
	  console.log( "error" );
	})
	.always(function() {
	  //Always close modal?
	});
    }
  }
  else if($('.nav-tabs .active a').attr("href") === "#tab2")
  {
    resultValFormFiles = $('#form-new-translator-files').valid();
    if(resultValFormName && resultValFormFiles)
    {
      $.ajax( "actions/translator-createfromfiles/"+$('#inputName').val()+"/"+$('#selFile1').val()+"/"+$('#selFile2').val() )
        .done(function() {
	  table.ajax.reload();
	  //close modal
	  $('#modal-add').modal("hide");
        })
	.fail(function() {
	  //TODO: better error handling
	  console.log( "error" );
	})
	.always(function() {
	  //Always close modal?
	});
    }
  }
  else if($('.nav-tabs .active a').attr("href") === "#tab3")
  {
    resultValFormFiles = $('#form-new-translator-existing').valid();
    if(resultValFormName && resultValFormFiles)
    {
      $.ajax( "actions/translator-createfromexisting/"+$('#inputName').val()+"/"+$('#selTrans1').val()+"/"+$('#selTrans2').val() )
        .done(function() {
          table.ajax.reload();
	  //close modal
	  $('#modal-add').modal("hide");
	})
	.fail(function() {
	  //TODO: better error handling
	  console.log( "error" );
	})
	.always(function() {
	  //Always close modal?
	});
     }
   }	
});


$('#form-new-translator-name').validate({
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

   $('#form-new-translator-files').validate({
   	   rules: {
   		   selFile1: {
   			   required: true
   		   },
		   selFile2: {
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

	  $('#form-new-translator-BLM').validate({
	  	rules: {
	  		selBitext: {
	  			required: true
	  		},
	  		selLanguageModel: {
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
