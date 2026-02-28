// Copyright (c) 2022, Narahari Dasa and contributors
// For license information, please see license.txt

frappe.ui.form.on('ALM', {
	onload: function (frm) {
		frm.set_query("department", "alm_levels", function (doc, cdt, cdn) {
			return {
				filters: {
					company: doc.company
				}
			};
		});
	}
});
