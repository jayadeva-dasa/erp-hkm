// Copyright (c) 2025, Narahari Dasa and contributors
// For license information, please see license.txt

frappe.ui.form.on("Internal Adjustment", {
  onload: function (frm) {
    frm.set_query("account", "entries", function (doc, cdt, cdn) {
      return {
        filters: {
          root_type: doc.adjustment_for,
          disabled: 0,
        },
      };
    });
  },
});
