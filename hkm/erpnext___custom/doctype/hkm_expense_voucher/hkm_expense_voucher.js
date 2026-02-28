// Copyright (c) 2025, Narahari Dasa and contributors
// For license information, please see license.txt

frappe.ui.form.on("HKM Expense Voucher", {
	refresh(frm) {
        if (frm.doc.docstatus > 0) {
            frm.add_custom_button(__("Ledger"), function () {
              frappe.route_options = {
                voucher_no: frm.doc.name,
                company: frm.doc.company,
                from_date: frm.doc.posting_date,
                to_date: moment(frm.doc.modified).format("YYYY-MM-DD"),
                group_by: "Group by Voucher (Consolidated)",
                show_cancelled_entries: frm.doc.docstatus === 2,
              };
              frappe.set_route("query-report", "General Ledger");
            });
          }
	},
});



