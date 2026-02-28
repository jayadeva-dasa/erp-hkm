// Copyright (c) 2022, Narahari Dasa and contributors
// For license information, please see license.txt
frappe.ui.form.on('Freeze Transaction Settings', {
	setup: function(frm) {
		frm.page.sidebar.toggle(false);
	},		
	freeze_from: function(frm) {
		$.each(frm.doc.forzen_documents || [], function(i, d) {
			d.frozen_from = frm.doc.freeze_from;
		});
		refresh_field("forzen_documents");
	},		
	freeze_upto: function(frm) {
		$.each(frm.doc.forzen_documents || [], function(i, d) {
			d.frozen_upto = frm.doc.freeze_upto;
		});
		refresh_field("forzen_documents");
	},	
});

frappe.ui.form.on('Freeze Transaction Settings Document', {
	frozen_upto: function(frm, cdt, cdn) {
		if(!frm.doc.freeze_upto) {
			erpnext.utils.copy_value_in_all_rows(frm.doc, cdt, cdn, "forzen_documents", "frozen_upto");
		}
	},
	frozen_from: function(frm, cdt, cdn) {
		if(!frm.doc.freeze_from) {
			erpnext.utils.copy_value_in_all_rows(frm.doc, cdt, cdn, "forzen_documents", "frozen_from");
		}
	}			
});




