// Copyright (c) 2024, Narahari Dasa and contributors
// For license information, please see license.txt

frappe.ui.form.on("HKM General Settings", {
	refresh(frm) {
        frm.set_query("cash_account", "active_company", (doc, cdt, cdn) => {
            var d = locals[cdt][cdn];
            return {
              filters: {
                company: d.company,
                account_type: "Cash",
                is_group: 0,
                disabled: 0,
              },
            };
          });
	},
});
