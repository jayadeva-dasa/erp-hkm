// Copyright (c) 2024, Narahari Dasa and contributors
// For license information, please see license.txt

frappe.ui.form.on("HKM Voucher Type", {
  refresh(frm) {
    frm.set_query("default_account", "defaults", (doc, cdt, cdn) => {
      var d = locals[cdt][cdn];
      return {
        filters: {
          company: d.company,
          account_type: "Expense Account",
          is_group: 0,
        },
      };
    });
  },
});
