// Copyright (c) 2025, Narahari Dasa and contributors
// For license information, please see license.txt

frappe.query_reports["HKM Report A02"] = {
  filters: [
    {
      fieldname: "cost_head",
      label: __("Cost Head"),
      fieldtype: "MultiSelectList",
      options: "Cost Head",
      reqd: 1,
      get_data: function (txt) {
        return frappe.db.get_link_options("Cost Head", txt, {
          disabled: 0,
        });
      },
    },
  ],
};
