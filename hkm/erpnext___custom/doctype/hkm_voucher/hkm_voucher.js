// Copyright (c) 2024, Narahari Dasa and contributors
// For license information, please see license.txt

frappe.ui.form.on("HKM Voucher", {
  onload(frm) {
    frappe.db
      .get_single_value("HKM General Settings", "pp_group")
      .then((value) => {
        frm.doc.pp_group = value;
      });
  },
  refresh(frm) {
    if (frm.doc.status != "Final Approved") {
      frm.add_custom_button("Approve", function () {
        // approve
        frm
          .call({
            freeze: true,
            freeze_message: "Approving.",
            method:
              "hkm.erpnext___custom.doctype.hkm_voucher.hkm_voucher.approve",
            args: { doc: frm.doc.name },
            btn: frm.page.btn_primary,
          })
          .then((r) => {
            frm.reload_doc();
          });
      });
    }

    frm.set_query("expense_head", () => {
      return {
        filters: {
          company: frm.doc.company,
          account_type: "Expense Account",
          is_group: 0,
        },
      };
    });
    frm.set_query("expense_head", "items", (doc, cdt, cdn) => {
      var d = locals[cdt][cdn];
      return {
        filters: {
          company: frm.doc.company,
          account_type: "Expense Account",
          is_group: 0,
        },
      };
    });
    frm.set_query("user_supplier_link", () => {
      return {
        filters: {
          supplier_group: frm.doc.pp_group,
          disabled: 0,
        },
      };
    });
  },
  expense_head: function (frm) {
    if (frm.doc.expense_head) {
      for (let i = 0; i < frm.doc.items.length; i++) {
        frm.doc.items[i].expense_head = frm.doc.expense_head;
      }
      frm.refresh_field("items");
    }
  },
});

frappe.ui.form.on("HKM Voucher Detail", {
  voucher_type: function (frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    frappe.db.get_doc("HKM Voucher Type", row.voucher_type).then((r) => {
      for (let i = 0; i < r.defaults.length; i++) {
        if (r.defaults[i].company === frm.doc.company) {
          row.expense_head = r.defaults[i].default_account;
          break;
        }
      }
      frm.refresh_field("items");
    });
  },
  amount: function (frm, cdt, cdn) {
    let grand_total = 0;
    for (let i = 0; i < frm.doc.items.length; i++) {
      grand_total += frm.doc.items[i].amount;
    }
    frm.set_value("grand_total", grand_total);
  },
});
