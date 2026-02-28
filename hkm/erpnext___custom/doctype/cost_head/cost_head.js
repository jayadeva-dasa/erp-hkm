// Copyright (c) 2024, Narahari Dasa and contributors
// For license information, please see license.txt

frappe.ui.form.on("Cost Head", {
  refresh(frm) {
    frm.set_query("parent_cost_head", function () {
      return {
        filters: {
          is_group: 1,
        },
      };
    });
  },
});
