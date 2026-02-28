// Copyright (c) 2024, Narahari Dasa and contributors
// For license information, please see license.txt

frappe.ui.form.on("AU Bank Account", {
  refresh(frm) {
    frm.add_custom_button("Fetch Bank Transactions", function () {
      frappe.call({
        method:
          "hkm.hkm_integration.doctype.au_bank_account.au_bank_account.fetch_statement",
        freeze: 1,
        freeze_message: "Fetching Status",
        args: {
          bank_id: frm.doc.name,
        },
        callback: function (r) {
          if (r.message) {
            frappe.msgprint(r.message);
          }
          frm.reload_doc();
        },
      });
    });
  },
});
