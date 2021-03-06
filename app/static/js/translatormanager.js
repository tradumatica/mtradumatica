$(document).ready(function() {
	$('body .dropdown-toggle').dropdown(); 
	let translator_id = "";

	let table = $('#translatorlist').DataTable({
		serverSide: true,
		ajax: {
			url: "actions/translator-list",
			type: "POST"
		},
		columnDefs: [{
			orderable: false,
			targets: [0,6,7,8,9]
		},
		{
			targets: [9],
			render: function(data, type, row) {
				let template = document.importNode(document.querySelector("#change-lm-template").content, true);
				$(template).find(".change-lm-btn").attr("data-id", row[10])
				$(template).find(".change-lm-btn").attr("data-lang", row[11])

				if (row[6] != "") {
					// Training has finished. We can share the MT
					$(template).find(".share-mt-btn").attr("data-id", row[10]);
					$(template).find(".share-mt-btn").removeClass("hidden");
				}

				let ghost = document.createElement('div');

				$(ghost).append(template);
				return ghost.innerHTML + data;
			}
		}],
		order : [
			[5, "desc"]
		],
  		createdRow : function ( row, data, index ) {
			//Id of translator represented by the row
			let id = $('td', row).eq(0).find('input').attr('id').split("-")[1];

			/***** Enable training counter  *********/
			let spanid = "training-time-" + id;
			let startDateTimeStr = $('td', row).eq(5).text();
			let curContent = $('td', row).eq(6).text();
			if(curContent === "") {
				//Show if training has not finished yet
				$('td', row).eq(6).html(`<span class="label label-primary" id="${spanid}"></span>`);

				init_clock(startDateTimeStr, spanid, id);
				init_status_checker("actions/status-translator", id, '#translatorlist');
			} else {
				//Training has finished: show green label
				let startDate = parseDate(startDateTimeStr);
				let endDate = parseDate(curContent);
				let diffStr = formatDateDiff(startDate,endDate);
				$('td', row).eq(6).html(`<span class="label label-success" id="${spanid}">${diffStr}</span>`);
			}

			//Once counters are initialized, display the date according to client's locale
			let date = parseDate(startDateTimeStr)
			if (!isNaN(date.getTime())) {
				$('td', row).eq(5).text(`${date.toLocaleDateString()} ${date.toLocaleTimeString()}`);
			}

			/***** Enable optimization counter  *********/
			spanid = "optimization-time-"+id;
			let cancelid = "cancel-id-" + id;
			let optimizingContent = $('td', row).eq(7).text();
			let parts = optimizingContent.split("#");

			if (parts.length <= 1) {
				//If there is only one part, server returned a button, keep it as is
			} else {
				if (parts[1] !== "") {
					//optimization has finished: display elapsed time
					let startDate = parseDate(parts[0]);
					let endDate = parseDate(parts[1]);
					let diffStr = formatDateDiff(startDate,endDate);
					$('td', row).eq(7).html(`<span class="label label-success" id="${spanid}">${diffStr}</span>`);
				} else {
					//optimization is running, display counter
					$('td', row).eq(7).html(`<span class="label label-primary" id="${spanid}"></span> <span class="glyphicon glyphicon-remove trashbin-enabled" id="${cancelid}"></span>`);

					init_clock(parts[0],spanid,id);
					init_status_checker("actions/status-translator-optimization", id, '#translatorlist');
				}
			}
		},
		language: datatables_lang
	});

	$('#translatorlist').on('draw.dt', function() {
		//Manage optimization modal
		let idOfTranslatorToOptimize = -1;
		$('#translatorlist .btn').off('click').on('click', function() {
			if ($(this).attr("id").startsWith("button-optimize-")) {
				let domidparts = $(this).attr("id").split("-");
				//asign id to global variable
				idOfTranslatorToOptimize = domidparts[2];

				//get list of compatible bitexts, populate modal and show it
				//fill select with bitexts
				$.ajax("/actions/bitext-plainlist/" + idOfTranslatorToOptimize).done(function(data) {
					$('#selBitextOptimize').empty();
					if (data.data.length  > 0) {
						$.each(data.data, function(i, item){
							let option = document.createElement('option');
							$(option).val(item.id).html(`${item.name} / ${item.nlines}`);
							$("#selBitextOptimize").append(option);
						});
					} else {
						let option = document.createElement('option');
						$(option).val(null).html("")
						$("#selBitextOptimize").append(option);
					}
					//SHow modal
					$('#modal-optimize').modal("show");
				});
			} else if($(this).attr("id").startsWith("button-evaluate-")) {
				$('#src').val('');
				$('#htrans').val('');
				$('#translator_name').html($(this).closest("tr").find("td:nth-child(2)").text());
				let langpair = $(this).closest("tr").find("td:nth-child(3)").text().split("-");
				
				$('#src_lang_indication').html(`[${langpair[0]}]`);
				$('#trg_lang_indication').html(`[${langpair[1]}]`);
				$('#modal-evaluate').modal("show");
				let domidparts = $(this).attr("id").split("-");
				//asign id to global variable
				translator_id = domidparts[2];
			}
		});

		//submit optimize form
		$('#buttonOptimize').off('click').on('click', function(){
			$.ajax(`actions/translator-optimize/${idOfTranslatorToOptimize}/${$('#selBitextOptimize').val()}`)
			.done(function() {
				table.ajax.reload();
				//close modal
				$('#modal-optimize').modal("hide");
			}).fail(function() {
				//TODO: better error handling
				console.log( "error" );
			})
		});

		$('input.file_checkbox').off('change').on('change', function() {
			if ($('#checkbox_all').is(":checked")) {
				$('#checkbox_all').addClass("checkbox-inconsistent");
			}

			let any = false;
			$('.file_checkbox').each(function() {
				if ($(this).is(":checked")) {
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

		$('#delete_all').off('change').on('click', function() {
			$('.file_checkbox').each(function () {
				if ($(this).is(":checked")) {
					$.ajax({
						url: "actions/translator-delete/" + $(this).attr("id").substring("checkbox-".length)
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

		$('span.glyphicon-remove').off('click').on('click', function(){
			$.ajax({
				url: "actions/optimization-kill/" + $(this).attr("id").substring("cancel-id-".length)
			}).done(function(){
				table.ajax.reload();
			});
		});

		$("#evalform").off('submit').on('submit', function(e){
			return false;
		});

		$('#button_evaluate').off('click').on('click', function(){
			let form = $("#evalform")[0];
			let data = new FormData(form);
			
			$('#modal-evaluate').modal("hide");
			$("#my-please-wait").modal("show");

			$.ajax({
				type: "POST",
				enctype: "multipart/form-data",
				url: "actions/perform-evaluation-translator/" + translator_id,
				cache: false,
				contentType: false,
				processData: false,
				data: data,
				success: function(result){
					/* Update table */
					table.ajax.reload();
					$("#my-please-wait").modal("hide");
				}
			});
		});

		//Put selected language in form, list monolingual corpora
		$('.seleclang').off('click').on('click', function() {
			let seleclang_lang = $(this).attr("lang");
			$('#inputLanguage' + languagenumber).text(seleclang_lang);
			validateInputLanguage(['inputLanguage1','inputLanguage2']);
			
			//if SL and TL are not empty, reload bitexts and language models
			if($('#inputLanguage1').text() != "" && $('#inputLanguage2').text() != ""){
				$.ajax("actions/languagemodel-plainlist/" + $('#inputLanguage2').text()).done(function(data) {
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
					$.ajax(`/actions/bitext-plainlist/${$('#inputLanguage1').text()}/${$('#inputLanguage2').text()}`)
					.done(function(data) {
						$('#selBitext').empty();
						if (data.data.length > 0) {
							$.each(data.data, function(i, item) {
								let option = document.createElement('option');
								$(option).val(item.id).html(`${item.name} / ${item.nlines}`);
								$("#selBitext").append(option);
							});
						} else {
							let option = document.createElement('option');
							$(option).val(null).html("");
							$("#selBitext").append(option);
						}

						//hide language selection modal
						$('#lang-dialog').modal("hide");
					})
				})
			}
		});

		//Show modal for creating a new bitext
		$('#addbutton').off('click').on('click', function() {
			$('#modal-add').modal("show");
		});

		let languagenumber = "0";
		//Show language selection modal on top ot if
		$('#inputLanguage1').off('click').on('click', function(){
			languagenumber = "1";
			$('#lang-dialog').modal("show");
		})

		$('#inputLanguage2').off('click').on('click', function(){
			languagenumber = "2";
			$('#lang-dialog').modal("show");
		})

		$(".change-lm-btn").off('click').on('click', function() {
			let translator_id = $(this).attr("data-id");
			
			$('#changeLMalert').addClass("hidden");
			$.ajax("actions/languagemodel-plainlist/" + $(this).attr("data-lang")).done(function(data) {
				$('#changeLMselect option:not(.select_original)').remove();
				if (data.data.length > 0){
					$.each(data.data, function(i, item) {
						$("#changeLMselect").append($("<option></option>").val(item.id).html(item.name));
					});
				} else{
					$("#changeLMselect").append($("<option></option>").val(null).html(""));
				}

				$("#modal-change-lm #changeLMBtn").off("click").on("click", function() {
					let lm_id = $("#changeLMselect option:selected").val()
					$.ajax({
						url: "actions/change-lm",
						method: "POST",
						data: { translator_id: translator_id, lm_id: lm_id }
					}).done(function(data) {
						if (data.result == 200) {
							table.ajax.reload();
							$('#modal-change-lm').modal("hide");
						} else {
							$('#changeLMalert').removeClass("hidden");
						}
					});
				});

				$('#changeLMalert').addClass("hidden");
				$("#modal-change-lm").modal();
			})
		});

		$(".share-mt-btn").off('click').on('click', function() {
			$("#modal-share-mt .copy-btn").removeClass("btn-success").addClass("btn-default");
			$("#modal-share-mt").modal('show');

			$.ajax({
				url: "actions/generate-share-link",
				method: "POST",
				data: { id: $(this).attr("data-id") }
			}).done(function(data) {
				console.log(data);
				if (data.result == 200) {
					$(".share-mt-link").val(data.share_url);

					$(".copy-btn").off('click').on('click', function() {
						$(".share-mt-link")[0].select();
						document.execCommand('copy');
						$(this).removeClass("btn-default").addClass("btn-success");
					});
				}
			});
		});
	});

	//submit create form
	$('#buttonCreate').off('click').on('click', function() {
		let resultValFormName = $('#form-new-translator-name').valid();

		if ($('.nav-tabs .active a').attr("href") === "#tab1") {
			let resultValFormBLM = $('#form-new-translator-BLM').valid();
			let resultValLanguage = validateInputLanguage(['inputLanguage1','inputLanguage2'])
			if (resultValFormName && resultValFormBLM && resultValLanguage) {
				$.ajax(`actions/translator-create/${$('#inputName').val()}/${$('#inputLanguage1').text()}/${$('#inputLanguage2').text()}/${$('#selBitext').val()}/${$('#selLanguageModel').val()}`)
				.done(function() {
					table.ajax.reload();
					//close modal
					$('#modal-add').modal("hide");
				}).fail(function() {
					//TODO: better error handling
					console.log( "error" );
				}).always(function() {
					//Always close modal?
				});
			}
		} else if($('.nav-tabs .active a').attr("href") === "#tab2") {
			let resultValFormFiles = $('#form-new-translator-files').valid();
			if (resultValFormName && resultValFormFiles) {
				$.ajax(`actions/translator-createfromfiles/${$('#inputName').val()}/${$('#selFile1').val()}/${$('#selFile2').val()}`)
				.done(function() {
					table.ajax.reload();
					//close modal
					$('#modal-add').modal("hide");
				}).fail(function() {
					//TODO: better error handling
					console.log( "error" );
				}).always(function() {
					//Always close modal?
				});
			}
		} else if($('.nav-tabs .active a').attr("href") === "#tab3") {
			resultValFormFiles = $('#form-new-translator-existing').valid();
			if (resultValFormName && resultValFormFiles) {
				$.ajax(`actions/translator-createfromexisting/${$('#inputName').val()}/${$('#selTrans1').val()}/${$('#selTrans2').val()}`)
				.done(function() {
					table.ajax.reload();
					//close modal
					$('#modal-add').modal("hide");
				}).fail(function() {
					//TODO: better error handling
					console.log( "error" );
				}).always(function() {
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
});
