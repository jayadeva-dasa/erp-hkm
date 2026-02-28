frappe.ui.form.on("POS Closing Entry", {
	refresh: function (frm) {
		if (frm.doc.name) {
			frm.add_custom_button(__("Refresh Sales Items"), function () {
				frappe.call({
					method: "hkm.erpnext___custom.overrides.HKMPOSClosingEntry.generate_sales_invoices_item_html",
					args: { doc_name: frm.doc.name },
					freeze: true,
					callback: function (r) {
						frm.reload_doc();
						frappe.show_alert({
							message: __("Sales Invoices Item refreshed successfully"),
							indicator: "green",
						});
					},
				});
			}, __("Actions"));
		}
	},
});
