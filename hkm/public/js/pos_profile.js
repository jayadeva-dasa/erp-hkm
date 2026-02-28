// Client script for POS Profile - Filter Sales Invoice Print Format field

frappe.ui.form.on("POS Profile", {
	setup: function(frm) {
		// Filter sales_invoice_print_format to show only Sales Invoice print formats
		frm.set_query("sales_invoice_print_format", function() {
			return {
				filters: [["Print Format", "doc_type", "=", "Sales Invoice"]]
			};
		});
	}
});
