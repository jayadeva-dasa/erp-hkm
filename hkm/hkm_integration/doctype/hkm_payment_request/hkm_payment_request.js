// Copyright (c) 2024, Narahari Dasa and contributors
// For license information, please see license.txt

frappe.ui.form.on("HKM Payment Request", {
  onload: function (frm) {
    if (frm.doc.__islocal) {
      frm.set_value("status", "");
    }
  },
  refresh: function (frm) {
    // Update totals on form load
    cur_frm.cscript.update_totals(frm.doc);
    
    frm.set_query("bank_account", function () {
      return {
        filters: {
          is_company_account: 1,
          company: frm.doc.company,
        },
      };
    });
    frm.set_query("supplier_bank_account", "items", function (frm, cdt, cdn) {
      const row = locals[cdt][cdn];
      return {
        filters: {
          party_type: "Supplier",
          party: row.supplier,
          disabled: 0,
        },
      };
    });
    if (frm.doc.docstatus == 1) {
      // Only show Upload button if not already uploaded and not cancelled
      if (!frm.doc.batch_number && !frm.doc.request_id && frm.doc.status !== "Cancelled") {
        frm.add_custom_button(
          "Upload to Bank",
          function () {
            frappe.call({
              method:
                "hkm.hkm_integration.doctype.hkm_payment_request.hkm_payment_request.upload_payment",
              freeze: 1,
              freeze_message: "Uploading to Bank",
              args: {
                payment_request: frm.doc.name,
              },
              callback: function (r) {
                if (r.message) {
                  frappe.msgprint(r.message);
                }
                // Update payment request status after upload
                frappe.call({
                  method:
                    "hkm.hkm_integration.doctype.hkm_payment_request.hkm_payment_request.update_payment_request_status",
                  freeze: 1,
                  freeze_message: "Updating Payment Request Status",
                  callback: function (status_r) {
                    frm.reload_doc();
                  },
                });
              },
            });
          },
          "Bank Operations"
        );
      }
      frm.add_custom_button(
        "Get Status",
        function () {
          frappe.call({
            method:
              "hkm.hkm_integration.doctype.hkm_payment_request.hkm_payment_request.get_status",
            freeze: 1,
            freeze_message: "Fetching Status",
            args: {
              payment_request: frm.doc.name,
            },
            callback: function (r) {
              if (r.message) {
                frappe.msgprint(r.message);
              }
              frm.reload_doc();
            },
          });
        },
        "Bank Operations"
      );
    }

    // if (
    //   frm.doc.document_type &&
    //   ["Purchase Invoice", "Purchase Order"].includes(frm.doc.document_type)
    // ) {
    //   frm.set_query("document_name", "items", function (frm, cdt, cdn) {
    //     const row = locals[cdt][cdn];
    //     return {
    //       filters: {
    //         party_type: "Supplier",
    //         party: row.supplier,
    //         docstatus: 1,
    //       },
    //     };
    //   });
    // }

    // if (frm.doc.docstatus == 0) {
    //   frm.add_custom_button(
    //     __("Purchase Invoice"),
    //     function () {
    //       //   frm.trigger("get_from_purchase_invoice");
    //       erpnext.utils.map_current_doc({
    //         method:
    //           "hkm.hkm_integration.doctype.hkm_payment_request.hkm_payment_request.make_payment_request_from_pi",
    //         source_doctype: "Purchase Invoice",
    //         target: frm,
    //         date_field: "posting_date",
    //         setters: {
    //           // supplier: frm.doc.supplier || undefined,
    //           company: frm.doc.company,
    //           supplier: frm.doc.supplier,
    //         },
    //         get_query_filters: {
    //           docstatus: 1,
    //         },
    //       });
    //     },
    //     __("Get Payments from")
    //   );

    //   frm.add_custom_button(
    //     __("Purchase Order"),
    //     function () {
    //       frm.trigger("get_from_purchase_order");
    //     },
    //     __("Get Payments from")
    //   );

    //   frm.trigger("remove_button");
    // }
  },

  get_from_purchase_invoice: function (frm) {
    // frm.trigger("remove_row_if_empty");
    erpnext.utils.map_current_doc({
      method:
        "hkm.hkm_integration.doctype.hkm_payment_request.hkm_payment_request.make_payment_request_from_pi",
      source_doctype: "Purchase Invoice",
      target: frm,
      setters: {
        party_type: "Supplier",
        party: frm.doc.supplier || "",
      },
      get_query_filters: {
        docstatus: 1,
        // status: ["=", "Initiated"],
      },
    });
  },
});

cur_frm.cscript.update_totals = function (doc) {

  if (doc.docstatus == 1) {
    return;
  }

  var ta = 0.0;
  var entries = doc.items || [];
  for (var i in entries) {
    ta += flt(entries[i].amount, precision("amount", entries[i]));
  }
  doc = locals[doc.doctype][doc.name];
  doc.total_amount = ta;
  refresh_field("total_amount");
};

// Track error messages per row
let errorShownPerRow = {};
let previousSupplierPerRow = {};

frappe.ui.form.on("HKM Payment Request Detail", {
  items_add: function (frm, cdt, cdn) {
    cur_frm.cscript.update_totals(frm.doc);
  },
  items_remove: function (frm, cdt, cdn) {
    cur_frm.cscript.update_totals(frm.doc);
  },
  supplier: async function (frm, cdt, cdn) {
    var d = frappe.get_doc(cdt, cdn);

    // Don't process if supplier is empty
    if (!d.supplier) {
      errorShownPerRow[cdn] = false; // Reset flag for this specific row
      previousSupplierPerRow[cdn] = null; // Reset previous supplier
      return;
    }

    // Reset error flag if supplier has changed
    if (previousSupplierPerRow[cdn] !== d.supplier) {
      errorShownPerRow[cdn] = false;
      previousSupplierPerRow[cdn] = d.supplier;
    }

    // Use get_list to check for multiple bank accounts
    const bank_accounts = await frappe.db.get_list("Bank Account", {
      filters: {
        party_type: "Supplier",
        party: d.supplier,
        disabled: 0,
      },
      fields: ["name"],
    });

    if (bank_accounts.length > 1) {
      // Only show error once per row per supplier
      if (!errorShownPerRow[cdn] && !d.supplier_bank_account) {
        errorShownPerRow[cdn] = true;
        frappe.msgprint({
          title: __("Error"),
          message: __(
            "Multiple bank accounts found for supplier {0}. Please select the correct bank account manually.",
            [d.supplier]
          ),
          indicator: "red",
        });
      }
      return;
    }

    // Reset flag for this row when there's only one or no bank account
    errorShownPerRow[cdn] = false;

    if (bank_accounts.length === 1) {
      frappe.model.set_value(
        cdt,
        cdn,
        "supplier_bank_account",
        bank_accounts[0].name
      );
    }
  },
  supplier_bank_account: async function (frm, cdt, cdn) {
    var d = frappe.get_doc(cdt, cdn);
    var bank_doc = await frappe.db.get_doc(
      "Bank Account",
      d.supplier_bank_account
    );
    frappe.model.set_value(
      cdt,
      cdn,
      "bank_account_name",
      bank_doc.account_name
    );
    frappe.model.set_value(
      cdt,
      cdn,
      "bank_account_number",
      bank_doc.bank_account_no
    );
    frappe.model.set_value(cdt, cdn, "ifsc_code", bank_doc.branch_code);
    refresh_field("items");
  },

  amount: function (frm, dt, dn) {
    cur_frm.cscript.update_totals(frm.doc);
  },
});
