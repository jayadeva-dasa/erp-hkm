// Copyright (c) 2022, Narahari Dasa and contributors
// For license information, please see license.txt

frappe.ui.form.on("Item Creation Request", {
  refresh: function (frm) {
    if (frm.doc.status == "Pending") {
      frm.add_custom_button(__("Create Item"), function () {
        frappe.call({
          method:
            "hkm.erpnext___custom.doctype.item_creation_request.item_creation_request.quickly_create_item",
          args: { request: frm.doc.name },
          callback: function (r) {
            if (r.message) {
              frappe.msgprint(r.message);
            }
            frm.reload_doc();
          },
        });
      });
      frm.add_custom_button(__("Reject"), function () {
        frm.set_value("status", "Rejected");
        frm.save();
      });
    }
  },
  // tax_category: function (frm) {
  //   console.log("tax");
  //   frappe.db.get_doc("Item Tax Template", frm.doc.tax_category).then((doc) => {
  //     // frm.doc.default_company = doc.company
  //     frm.set_value("default_company", doc.company);
  //   });
  // },
  onload: function (frm) {
    frm.set_query("default_sales_income_account", function () {
      return {
        filters: {
          root_type: "Income",
          is_group: 0,
          // company: frm.doc.default_company,
        },
      };
    });
    frm.set_query("item_group", function () {
      return {
        filters: {
           is_group: 0,
          
          },
      };
    });
  },
});

frappe.listview_settings["Item Creation Request"] = {
  add_fields: ["status"],
  get_indicator: function (doc) {
    if (doc.status == "Pending") {
      return [__("Pending"), "yellow", "status,=,Pending"];
    } else if (doc.status == "Created") {
      return [__("Created"), "green", "status,=,Created"];
    } else if (doc.status == "Rejected") {
      return [__("Rejected"), "red", "status,=,Rejected"];
    }
  },
};
