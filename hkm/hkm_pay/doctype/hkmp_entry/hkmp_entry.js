// Copyright (c) 2025, Narahari Dasa and contributors
// For license information, please see license.txt

frappe.ui.form.on("HKMP Entry", {
	refresh(frm) {
		// Add button to validate VPA
		frm.add_custom_button(__('Validate VPA'), function() {
				const vpa = frm.doc.upi_id;
				
				if (!vpa) {
					frappe.msgprint({
						title: __('Validation Error'),
						indicator: 'orange',
						message: __('Please enter a VPA (UPI ID) before validating.')
					});
					return;
				}

				frappe.call({
					method: 'hkm.hkm_pay.doctype.hkmp_entry.hkmp_entry.validate_vpa_id',
					args: {
						vpa_id: vpa
					},
					freeze: true,
					freeze_message: __('Validating VPA...'),
					callback: function(r) {
						if (r.message) {
							frappe.msgprint({
								title: __('VPA Validation Response'),
								indicator: 'blue',
								message: __('Response: <pre>{0}</pre>', [JSON.stringify(r.message, null, 5)])
							});
						}
					},
					error: function(r) {
						frappe.msgprint({
							title: __('Validation Error'),
							indicator: 'red',
							message: r.message || __('Failed to validate VPA')
						});
					}
				});
			}, __('Actions'));

		// Add button to check transaction status
		frm.add_custom_button(__('Check Transaction Status'), function() {
				const entry_name = frm.doc.name;
				
				if (!entry_name) {
					frappe.msgprint({
						title: __('Validation Error'),
						indicator: 'orange',
						message: __('Please save the document before checking transaction status.')
					});
					return;
				}

				frappe.call({
					method: 'hkm.hkm_pay.doctype.hkmp_entry.hkmp_entry.check_transaction_status_hkmp_entry',
					args: {
						entry_name: entry_name
					},
					freeze: true,
					freeze_message: __('Checking transaction status...'),
					callback: function(r) {
						if (r.message) {
							const response = r.message;
							
							if (response.success) {
								let message = __('<b>Transaction Status Check</b><br><br>');
								message += __('<b>Old Status:</b> {0}<br>', [response.old_status || 'N/A']);
								message += __('<b>New Status:</b> {0}<br>', [response.new_status || 'N/A']);
								
								if (response.status_changed) {
									message += __('<br><b style="color: green;">Status has been updated!</b><br>');
								} else {
									message += __('<br><b>Status unchanged.</b><br>');
								}
								
								if (response.transaction_tracking_id) {
									message += __('<br><b>Tracking ID:</b> {0}<br>', [response.transaction_tracking_id]);
								}
								
								if (response.utr) {
									message += __('<b>UTR:</b> {0}<br>', [response.utr]);
								}
								
								if (response.customer_ref_no) {
									message += __('<b>Customer Ref No:</b> {0}<br>', [response.customer_ref_no]);
								}
								
								if (response.api_response) {
									message += __('<br><b>API Response:</b><br><pre>{0}</pre>', [JSON.stringify(response.api_response, null, 2)]);
								}
								
								frappe.msgprint({
									title: __('Transaction Status Response'),
									indicator: response.status_changed ? 'green' : 'blue',
									message: message
								});
								
								// Reload the form to show updated status
								frm.reload_doc();
							} else {
								frappe.msgprint({
									title: __('Transaction Status Check Failed'),
									indicator: 'red',
									message: response.message || response.error || __('Failed to check transaction status')
								});
							}
						}
					},
					error: function(r) {
						frappe.msgprint({
							title: __('Transaction Status Check Error'),
							indicator: 'red',
							message: r.message || __('Failed to check transaction status')
						});
					}
				});
			}, __('Actions'));
	},
});
