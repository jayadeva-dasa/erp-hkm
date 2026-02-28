// Copyright (c) 2022, Narahari Dasa and contributors
// For license information, please see license.txt

frappe.ui.form.on('Block GST Entry Settings', {
	setup: function(frm) {
		frm.set_query("department", "entries", function(doc, cdt, cdn) {
				let row = frappe.get_doc(cdt, cdn);
				return {
					filters: {
						"company": row.company
					}
				};
		});
	},
});

frappe.ui.form.on('Block GST Entry', {
	company: function(frm, cdt, cdn) {
		frappe.model.set_value(cdt, cdn, "department", "");
		frappe.model.set_value(cdt, cdn, "block_input_gst", 0);
		frappe.model.set_value(cdt, cdn, "block_output_gst", 0);
	},
});
