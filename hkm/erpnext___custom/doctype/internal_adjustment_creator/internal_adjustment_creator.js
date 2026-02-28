// Copyright (c) 2025, Narahari Dasa and contributors
// For license information, please see license.txt

frappe.ui.form.on("Internal Adjustment Creator", {
  refresh(frm) {
    frm.set_query("cost_head", "service_department", (doc, cdt, cdn) => {
      return {
        filters: {
          is_group: 0,
          disabled: 0,
        },
      };
    });
    frm.set_query("cost_head", "execution_department", (doc, cdt, cdn) => {
      return {
        filters: {
          is_group: 0,
          disabled: 0,
        },
      };
    });

    frm.set_query("account", "accounts", (doc, cdt, cdn) => {
      return {
        filters: {
          root_type: "Expense",
        },
      };
    });
    // Add custom button
    frm.add_custom_button(__("Create Internal Adjustment"), () => {
      validateChildTableField(
        frm,
        "service_department",
        "cost_head",
        "Cost Head"
      );
      validateChildTableField(
        frm,
        "execution_department",
        "cost_head",
        "Cost Head"
      );
      validateChildTableField(frm, "execution_department", "share", "Share");
      
      let args = {
        service_cost_heads: frm.doc.service_department,
        execution_cost_heads: frm.doc.execution_department,
        from_date: frm.doc.from_date,
        to_date: frm.doc.to_date,
        posting_date: frm.doc.posting_date,
        name: frm.doc.name,
      };
   

      if (frm.doc.specific_accounts) {
        if (!frm.doc.accounts || !frm.doc.accounts.length) {
          frappe.throw("Account is required in the case of Specific Accounts.");
        }
        
        args["specific_accounts"] = frm.doc.specific_accounts;
        args["accounts"] = frm.doc.accounts;
      }

      frappe.call({
        method: "hkm.erpnext___custom.doctype.internal_adjustment_creator.internal_adjustment_creator.create_internal_adjustment",
        args: args,
        freeze: true,
        async: true,
        callback: function (r) {
          console.log(r.exc)
          if (!r.exc) {
            frappe.msgprint(__("Internal Adjustment Created Successfully."));
          } else {
            frappe.msgprint(__(r.message));
          }
        },
      });
    });
  },
  specific_accounts(frm) {
    //    frm.toggle_display("accounts", frm.doc.specific_accounts);
    if (frm.doc.specific_accounts) {
      frm.set_df_property("accounts", "hidden", 0);
    } else {
      frm.set_df_property("accounts", "hidden", 1);
    }
  },
  onload(frm) {
    if (frm.doc.specific_accounts) {
      frm.set_df_property("accounts", "hidden", 0);
    } else {
      frm.set_df_property("accounts", "hidden", 1);
    }
  },
});
function validateChildTableField(
  frm,
  childTableFieldname,
  fieldToCheck,
  fieldLabel
) {
  const table = frm.doc[childTableFieldname] || [];

  const hasMissingField = table.some((row) => {
    const value = row[fieldToCheck];

    // Disallow null/undefined
    if (value === null || value === undefined) return true;

    // Disallow empty or whitespace-only strings
    if (typeof value === "string" && value.trim() === "") return true;

    // Disallow numeric 0
    if (typeof value === "number" && value === 0) return true;

    // Otherwise, it's valid
    return false;
  });

  if (hasMissingField) {
    frappe.throw(
      `All rows in ${frappe.meta.get_label(
        frm.doc.doctype,
        childTableFieldname,
        frm.doc.name
      )} must have a valid ${fieldLabel} (non-empty and not 0).`
    );
  }
}
