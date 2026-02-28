// Copyright (c) 2021, Narahari Das and contributors
// For license information, please see license.txt

frappe.ui.form.on('Stock Check', {
	refresh: function(frm) {
		frm.add_custom_button(__("Create Stock Reconcillation"), function() {
	        frappe.model.open_mapped_doc({
	    			method: "hkm.erpnext___custom.doctype.stock_check.stock_check.make_stock_reconcillation_entry",
	    			frm: frm
	    		});
	    });
	}
});