// Copyright (c) 2021, NRHD and contributors
// For license information, please see license.txt

frappe.ui.form.on('Ashraya Ceremony Participant', {
	// refresh: function(frm) {

	// }
	validate:function(frm){
		console.log("running");
		frappe.call({
	        method: "frappe.client.get_value",
	        args: {
	                doctype: "Ashraya Ceremony Participant",
	                fieldname: "name",
	                filters: {
							participant: frm.doc.participant,
							level: frm.doc.level
	                }
	        },
	        callback: function(response) {
	             var value = response.message;
	             console.log(value);
	             if (!jQuery.isEmptyObject(value)) {
	                 	frappe.msgprint("Similar Record is already available.");
						frappe.validated=false;
	    				return false;
	             }
	        }
		});
	}
});
