// Copyright (c) 2025, Narahari Dasa and contributors
// For license information, please see license.txt

frappe.ui.form.on("HKM Expense Voucher Type", {
	refresh(frm) {
        frm.set_query("default_account", "defaults", (doc, cdt, cdn) => {
            var d = locals[cdt][cdn];
            return {
              filters: {
                company: d.company,
                root_type: "Expense",
                disabled: 0,
                is_group: 0,
              },
            };
          });
	},
});
