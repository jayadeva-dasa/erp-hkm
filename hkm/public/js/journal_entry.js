// Copyright (c) 2020, Tara Technologies
// For license information, please see license.txt



frappe.ui.form.on("Journal Entry", {
	refresh: function (frm) {
		frm.add_custom_button(__('Unlink Bank Transaction'), function () {
	
			frappe.warn('Are you sure you want to proceed?',
				'This will unallocate this entry from its connected Bank Trasaction Entry.',
				() => {
					frappe.call({
						method: 'hkm.erpnext___custom.overrides.journal_entry.unallocate_bank_transaction',
						args: { "je": frm.doc.name }
					});
				},
				'Continue',
				true // Sets dialog as minimizable
			)
		}, __("Actions"));
	
		// Add button to update uncleared amount
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__('Update Uncleared Amount'), function () {
				frappe.call({
					method: 'hkm.erpnext___custom.overrides.HKMJournalEntry.update_suspense_jv_cleared_amount',
					args: { "suspense_jv": frm.doc.name },
					callback: function (r) {
						frappe.show_alert({
							message: __('Uncleared Amount Updated Successfully'),
							indicator: 'green'
						});
						frm.reload_doc();
					}
				});
			}, __("Actions"));
		}
	},
	onload: function (frm) {
		frm.set_query("suspense_jv", "accounts", function (doc, cdt, cdn) {
			return {
				query: "hkm.erpnext___custom.extend.queries.uncleared_suspense_voucher_query",
				filters: {
					'company': frm.doc.company
				}
			}
		});

	},
	setup_queries: function (frm) {
		frm.set_query("suspense_jv", "accounts", function (doc, cdt, cdn) {
			return {
				query: "hkm.erpnext___custom.extend.queries.uncleared_suspense_voucher_query",
				filters: {
					'company': frm.doc.company
				}
			}
		});
	},


});
$.extend(erpnext.journal_entry, {
	account_query: function (frm) {
		var filters = {
			company: frm.doc.company,
			is_group: 0
		};
		return { filters: filters };
	},
});
