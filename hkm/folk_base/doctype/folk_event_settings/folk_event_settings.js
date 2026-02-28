// Copyright (c) 2023, Narahari Dasa and contributors
// For license information, please see license.txt

frappe.ui.form.on('FOLK Event Settings', {
	refresh: function(frm) {
		frm.add_custom_button(__('Fetch Entries'), function(){
			frappe.call({
				freeze:true,
				freeze_message:"Updating from Razorpay",
				method: "hkm.folk_base.doctype.folk_event_settings.folk_event_settings.update_razorpay_entries", //dotted path to server method
				callback: function(r) {
					if(!r.exc){
						frappe.msgprint("Successfully Updated");
					}
					
				}
			});
		}, __("Utilities"));
		frm.add_custom_button(__('Send QR Emails'), function(){
			frappe.call({
				freeze:true,
				freeze_message:"Sending the Emails",
				method: "hkm.folk_base.doctype.folk_event_settings.folk_event_settings.send_QR_email", //dotted path to server method
				callback: function(r) {
					if(!r.exc){
						frappe.msgprint("Successfully Sent");
					}
					
				}
			});
		}, __("Utilities"));
	}
});
