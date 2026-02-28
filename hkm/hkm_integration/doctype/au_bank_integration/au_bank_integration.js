// Copyright (c) 2024, Narahari Dasa and contributors
// For license information, please see license.txt

frappe.ui.form.on("AU Bank Integration", {
  refresh(frm) {
    frm.add_custom_button(__("Refresh Token"), () => {
      frappe.call({
        method:
          "hkm.hkm_integration.doctype.au_bank_integration.au_bank_integration.refresh_token",
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
