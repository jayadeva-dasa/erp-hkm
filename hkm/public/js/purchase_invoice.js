frappe.ui.form.on("Purchase Invoice", {
  refresh: function (frm) 
  {

    // Setting TDS Fields 
    set_tds_values(frm);

    if (frm.fields_dict["volunteer"]) {
      frm.set_query("volunteer", function () {
        return {
          filters: { enabled: 1 }
        };
      });
    } else {
      console.log("Volunteer field does not exist in this Doctype");
    }




    if (frm.doc.docstatus === 1) {
      frappe.call({
        method:
          "hkm.erpnext___custom.overrides.HKMPurchaseInvoice.get_documents_map_data",
        args: {
          document: frm.doc.name,
        },
        callback: function (r) {
          if (!r.exc) {
            frm.set_df_property("documents_map_html", "options", r.message);
          }sales
        },
      });
    }
  },
  onload: function (frm) 
  {
    if (frm.fields_dict["volunteer"]) {
      frm.set_query("volunteer", function () {
        return {
          filters: { enabled: 1 }
        };
      });
    } else {
      console.log("Volunteer field does not exist in this Doctype");
    }
    frm.set_query("default_difference_account", function () {
      return {
        filters: {
          root_type: ["in", ["Expense", "Liability", "Asset"]],
           company: frm.doc.company,
            is_group: 0 },
      };
    });
    frm.set_query("default_difference_cost_center", function () {
      return {
        filters: {
          disabled: 0,
          company: frm.doc.company,
          is_group: 0,
        },
      };
    });
    if (frm.doc.docstatus == 0) {
      frm.add_custom_button(
        __("Direct Trash"),
        function () {
          frappe.call({
            method: "hkm.erpnext___custom.common.directly_mark_cancelled",
            args: {
              doctype: frm.doc.doctype,
              docname: frm.doc.name,
            },
            callback: (r) => {
              frm.reload_doc();
            },
          });
        },
        "Actions"
      );
    }
  },
  default_difference_account: function (frm) {
    var entries = frm.doc.items;
    for (var i = 0; i < entries.length; i++) {
      frappe.model.set_value(
        "Purchase Invoice Item",
        entries[i].name,
        "expense_account",
        frm.doc.default_difference_account
      );
    }
  },
  default_difference_cost_center: function (frm) {
    var entries = frm.doc.items;
    for (var i = 0; i < entries.length; i++) {
      frappe.model.set_value(
        "Purchase Invoice Item",
        entries[i].name,
        "cost_center",
        frm.doc.default_difference_cost_center
      );
    }
    frm.set_value("cost_center", frm.doc.default_difference_cost_center);
  },
  validate: function(frm)
  {
    //Setting TDS Fields
    set_tds_values(frm);
  }
});

frappe.ui.form.on("Purchase Invoice Item", {
  item_code: function (frm, cdt, cdn) {
    frappe.model.set_value(
      cdt,
      cdn,
      "expense_account",
      frm.doc.default_difference_account
    );
  },
});


//Calculating and Populating The TDS Fields
function set_tds_values(frm) {

    let taxable_amount = 0;
    let tds_amount = 0;
    let tds_rate = 0;

    if (frm.doc.taxes) {

        frm.doc.taxes.forEach(row => {

            if (row.is_tax_withholding_account) {

                taxable_amount =
                    row.tax_amount_for_current_item ||
                    frm.doc.base_net_total;

                tds_amount = Math.abs(row.tax_amount || 0);

                tds_rate = Math.abs((row.tax_amount / frm.doc.base_net_total) * 100) || 0;
            }
        });
    }

    frm.set_value("tds_taxable_amount", taxable_amount);

    frm.set_value("tds_deduction_amount", tds_amount);

    frm.set_value("tds_percentage", tds_rate);
}