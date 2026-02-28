// Copyright (c) 2025, Narahari Dasa and contributors
// For license information, please see license.txt

frappe.ui.form.on("HKMP User", {
	refresh(frm) {
		// Add button to generate/reset secret PIN
		if (!frm.is_new()) {
			frm.add_custom_button(__('Generate/Reset PIN'), function() {
				frappe.prompt({
					label: __('Enter desired PIN (leave blank for auto-generated)'),
					fieldname: 'desired_pin',
					fieldtype: 'Data',
					description: __('Enter a 4-digit PIN or leave blank to auto-generate a random PIN'),
					reqd: 0
				}, function(values) {
					frappe.call({
						method: 'hkm.hkm_pay.doctype.hkmp_user.hkmp_user.generate_secret_pin',
						args: {
							docname: frm.doc.name,
							desired_pin: values.desired_pin || null
						},
						callback: function(r) {
							if (r.message) {
								frappe.msgprint({
									title: __('Secret PIN Generated'),
									indicator: 'green',
									message: __('New Secret PIN: <b>{0}</b>', [r.message])
								});
								frm.reload_doc();
							}
						},
						error: function(r) {
							frappe.msgprint({
								title: __('Error'),
								indicator: 'red',
								message: r.message || __('Failed to generate PIN')
							});
						}
					});
				});
			});

			// Add button to show current secret PIN
			frm.add_custom_button(__('Show PIN'), function() {
				frappe.call({
					method: 'hkm.hkm_pay.doctype.hkmp_user.hkmp_user.show_secret_pin',
					args: {
						docname: frm.doc.name
					},
					callback: function(r) {
						if (r.message) {
							frappe.msgprint({
								title: __('Current Secret PIN'),
								indicator: 'blue',
								message: __('Secret PIN: <b>{0}</b>', [r.message])
							});
						}
					}
				});
			});
		}
	},
});
