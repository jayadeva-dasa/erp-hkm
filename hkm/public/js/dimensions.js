$(document).on("app_ready", function () {
  $.each(
    [
      "Purchase Invoice",
      "Sales Invoice",
      "Stock Entry",
      "Purchase Order",
      "Material Request",
      "Purchase Receipt",
    ],
    function (i, doctype) {
      frappe.ui.form.on(doctype, {


        cost_head: function (frm) {
          for (var i = 0; i < frm.doc.items.length; i++) {
            // Only update if child item doesn't have a value already
            if (!frm.doc.items[i].cost_head) {
              frappe.model.set_value(
                frm.doc.items[i].doctype,
                frm.doc.items[i].name,
                "cost_head",
                frm.doc.cost_head
              );
            }
          }
        },
        cost_center: function (frm) {
          for (var i = 0; i < frm.doc.items.length; i++) {
            // Only update if child item doesn't have a value already
            if (!frm.doc.items[i].cost_center) {
              frappe.model.set_value(
                frm.doc.items[i].doctype,
                frm.doc.items[i].name,
                "cost_center",
                frm.doc.cost_center
              );
            }
          }
        },
        project: function (frm) {
          for (var i = 0; i < frm.doc.items.length; i++) {
            // Only update if child item doesn't have a value already
            if (!frm.doc.items[i].project) {
              frappe.model.set_value(
                frm.doc.items[i].doctype,
                frm.doc.items[i].name,
                "project",
                frm.doc.project
              );
            }
          }
        },
        festival: function (frm) {
          for (var i = 0; i < frm.doc.items.length; i++) {
            // Only update if child item doesn't have a value already
            if (!frm.doc.items[i].festival) {
              frappe.model.set_value(
                frm.doc.items[i].doctype,
                frm.doc.items[i].name,
                "festival",
                frm.doc.festival
              );
            }
          }
        },
        devotee: function (frm) {
          for (var i = 0; i < frm.doc.items.length; i++) {
            // Only update if child item doesn't have a value already
            if (!frm.doc.items[i].devotee) {
              frappe.model.set_value(
                frm.doc.items[i].doctype,
                frm.doc.items[i].name,
                "devotee",
                frm.doc.devotee
              );
            }
          }
        },
        folk_residency: function (frm) {
          for (var i = 0; i < frm.doc.items.length; i++) {
            // Only update if child item doesn't have a value already
            if (!frm.doc.items[i].folk_residency) {
              frappe.model.set_value(
                frm.doc.items[i].doctype,
                frm.doc.items[i].name,
                "folk_residency",
                frm.doc.folk_residency
              );
            }
          }
        },
      });
    }
  );
});
