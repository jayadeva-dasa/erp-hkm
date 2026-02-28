// Copyright (c) 2023, Narahari Dasa and contributors
// For license information, please see license.txt

frappe.ui.form.on('DD Order', {
	refresh: function (frm) {
		if (frm.doc.status == 'Paid') {
			frm.add_custom_button(__('Mark Delivered'), function () {
				frappe.warn('Are you sure you want to proceed?',
					'This action will mark this order to be Delivered.',
					() => {
						frappe.call({
							freeze: true,
							method: "hkm.divine_dishes.doctype.dd_order.dd_order.mark_delivered",
							args: {
								docname: frm.doc.name
							},
							callback: function (r) {
								if (!r.exc) {
									frappe.msgprint("Successfully Delivered.");
								}
								frm.refresh();
							}
						});
					}, () => {

					});

			});
		}

	}
});
