// Copyright (c) 2021, NRHD and contributors
// For license information, please see license.txt

frappe.ui.form.on('FOLK Redirect', {
	validate: function(frm) {
		if (frm.doc.short_link.length <5){
			frappe.msgprint("Short Link should have length more than 4");
			frappe.validated = false;
			}
		}
});
