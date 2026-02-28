// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

frappe.ready(function() {

	$('.btn-send').off("click").on("click", function() {
		var code = $('[name="code"]').val();

		if(!(code)) {
			frappe.throw('कृपया आश्रय कोड दर्ज करें| धन्यवाद!');
			return false;
		}
		frappe.call({
	        method: 'folk.www.ashraya.check_if_code_available',
	        args: {
	            'code': code
	        },
	        callback: function(r) {
	            if (!r.exc) {
	                console.log(r.message);
	                if(r.message == "Not Exists"){
	                	frappe.throw('{{ _("आश्रय कोड गलत है") }}');
	                }else if(r.message == "Exists"){
	                	frappe.msgprint({
	                		title: ('कृपया विवरण की पुष्टि करें'),
	                		message:`आपका विवरण: <br>नाम: <b>${r.doc['name1']}</b><br>मोबाइल: <b>${r.doc['mobile_number']}</b><br>अगर ये आप नहीं हैं तो पीछे जायें और सही आश्रय कोड प्रविष्ट करें |`,
	                		primary_action:{
	                				'label': 'समारोह में प्रवेश करें',
							        action(values) {
							        	frappe.call({
									        method: 'folk.www.ashraya.check_attendance',
									        args: {
									            'code': code
									        },
									        callback: function(r) {
									            if (!r.exc) {
									            	window.location = r.redirect_link;
									            }
									        }
										});
							        }
							    }
	                		});
	                }else if(r.message == "Not allowed"){
	                	frappe.throw('{{ _("आप ऑनलाइन आश्रय के लिए अनुमत नहीं हैं | ") }}');
	                }
	                console.log(r.doc);
	            }
	        }
	    });

		// frappe.check_if_code_available({
		// 	code: $('[name="code"]').val(),
		// 	callback: function(r) {
		// 		if(r.message==="okay") {
		// 			frappe.msgprint('{{ _("Thank you for your message") }}');
		// 		} else {
		// 			frappe.msgprint('{{ _("There were errors") }}');
		// 			console.log(r.exc);
		// 		}
		// 		$(':input').val('');
		// 	}
		// }, this);
		return false;
	});

});

var msgprint = function(txt) {
	if(txt) $("#contact-alert").html(txt).toggle(true);
}