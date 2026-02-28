/**
 * Purchase Order Form Events
 * Handles custom buttons and form behavior for Purchase Order doctype
 */
frappe.ui.form.on("Purchase Order", {
  onload: function (frm) {
    // addApprovalActionItems(frm);
    if (frm.doc.__islocal) {
      frm.set_value("locked", 0);
      frm.set_value("approval_status", null);
      frm.set_value("current_approving_authority", null);
      frm.set_value("approving_authorities", []);
      frm.set_value("approval_initiator", null);
      frm.set_value("status_indicator", "Check Pending");
    }
    if (frm.fields_dict["volunteer"]) {
      frm.set_query("volunteer", function () {
        return {
          filters: { enabled: 1 }
        };
      });
    } else {
      console.log("Volunteer field does not exist in this Doctype");
    }
  },

  refresh: function (frm) {
    // Hide submit button when document is locked and docstatus is 0
    if (frm.doc.locked && frm.doc.docstatus == 0) {
      frm.disable_save();
    }
    if (frm.fields_dict["volunteer"]) {
      frm.set_query("volunteer", function () {
        return {
          // filters: { enabled: 1 }
        };
      });
    } else {
      console.log("Volunteer field does not exist in this Doctype");
    }

    // Add approval action items (with duplicate prevention)
    addApprovalActionItems(frm);

    // Add custom buttons for draft documents that are not new
    if (frm.doc.docstatus == 0 && !frm.doc.__islocal) {
      // Show buttons for locked documents
      if (
        frm.doc.locked &&
        (frappe.user.has_role("Purchase Manager") ||
          frappe.user.has_role("System Manager"))
      ) {
        frm
          .add_custom_button("Resend Approval Request", function () {
            showResendApprovalModal(frm);
          })
          .css({
            color: "white",
            "background-color": "#52527a",
            "font-weight": "800",
          });

        frm
          .add_custom_button("Unlock", function () {
            frappe.confirm(
              "Are you sure you want to make this purchase order editable?",
              function () {
                frappe.call({
                  method: "hkm.hkm_approval_matrix.main.make_doc_editable",
                  args: {
                    docname: frm.doc.name,
                    doctype: "Purchase Order",
                  },
                  async: false,
                  freeze: true,
                  freeze_message: "Unlocking Purchase Order",

                  callback: (r) => {
                    if (!r.exc) {
                      frappe.show_alert({
                        message: "Purchase Order is editable now",
                        indicator: "green",
                      });

                      frm.reload_doc();

                      document
                        .querySelectorAll(".dropdown-menu li a")
                        .forEach((el) => {
                          let txt = el.innerText.trim();
                          if (
                            txt.includes("Approve") ||
                            txt.includes("Reject")
                          ) {
                            el.parentElement.remove();
                          }
                        });

                      // If Actions has no items left, remove the Actions button itself
                      document
                        .querySelectorAll(".actions-btn-group")
                        .forEach((group) => {
                          let items = group.querySelectorAll(
                            ".dropdown-menu li a"
                          );
                          if (items.length === 0) {
                            group.remove();
                          }
                        });
                      frm.reload_doc();
                    }
                  },
                });
              },
              function () {
                frappe.msgprint("Action cancelled.");
              }
            );
          })
          .css({
            color: "white",
            "background-color": "#e63900",
            "font-weight": "800",
          });
      }

      // Show buttons for unlocked documents
      if (
        !frm.doc.locked &&
        (frappe.user.has_role("Purchase Manager") ||
          frappe.user.has_role("System Manager"))
      ) {
        frm
          .add_custom_button(
            "Cancel <i class='fa fa-times' style='color:white'></i>",
            function () {
              frappe.confirm(
                `Are you sure you want to cancel this purchase order?`,
                function () {
                  frappe.call({
                    method: `hkm.hkm_approval_matrix.main.cancel_purchase_order`,
                    args: {
                      docname: frm.doc.name,
                      doctype: "Purchase Order",
                    },
                    freeze: true,
                    freeze_message:
                      "Document Checked ... Setting Up Authorization",
                    callback: (r) => {
                      if (!r.exc) {
                        // Show success message
                        frappe.show_alert({
                          message: "Purchase Order cancelled successfully",
                          indicator: "green",
                        });

                        // Reload document
                        if (!r.exc) {
                          frm.reload_doc();
                          frm.refresh();
                        }
                      }
                    },
                  });
                }
              );
            }
          )
          .css({
            color: "white",
            "background-color": "#e63900",
            "font-weight": "800",
          });

        frm
          .add_custom_button(
            "Check <i class='fa fa-check' style='color:white'></i>",
            function () {
              handleApprovalRequest(
                frm,
                "send_approval",
                "send this purchase order for approval"
              );
            }
          )
          .css({
            color: "white",
            "background-color": "#3399ff",
            "font-weight": "800",
          });
      }
    }
  },

  company: function (frm) {
    frm.set_query("department", () => {
      return {
        filters: {
          company: frm.doc.company,
        },
      };
    });
  },
});

/**
 * Add approval action items (Approve/Reject) with proper duplicate prevention
 * @param {Object} frm - The form object
 */
function addApprovalActionItems(frm) {
  if (
    frm.doc.docstatus == 0 &&
    frm.doc.approving_authorities &&
    frm.doc.approving_authorities.length > 0 &&
    frm.doc.locked &&
    frm.doc.current_approving_authority === frappe.session.user &&
    frm.doc.approval_status != "Rejected"
  ) {
    // Check if actions already exist by looking at the actual DOM content
    const actionsMenu = frm.page.actions;
    const existingApprove =
      actionsMenu.find('a .menu-item-label:contains("Approve")').length > 0;
    const existingReject =
      actionsMenu.find('a .menu-item-label:contains("Reject")').length > 0;

    // Add Approve action item only if it doesn't exist
    if (!existingApprove) {
      frm.page.add_action_item(
        __('Approve <i class="fa fa-check text-success"></i>'),
        function () {
          approvePurchaseOrder(frm);
        }
      );
    }

    // Add Reject action item only if it doesn't exist
    if (!existingReject) {
      frm.page.add_action_item(
        __('Reject <i class="fa fa-times text-danger"></i>'),
        function () {
          rejectPurchaseOrder(frm);
        }
      );
    }
  }
}

function approvePurchaseOrder(frm) {
  frappe.confirm(
    `Are you sure you want to approve this purchase order?`,
    function () {
      frappe.call({
        method: "hkm.hkm_approval_matrix.main.approve_purchase_order",
        args: {
          docname: frm.doc.name,
          doctype: "Purchase Order",
        },
        freeze: true,
        freeze_message: "Approving Purchase Order",
        callback: (r) => {
          if (!r.exc) {
            // Show success message
            frappe.show_alert({
              message: "Purchase Order sent for approval",
              indicator: "green",
            });

            frm.reload_doc();
            frm.refresh();
          }
        },
      });
    }
  );
}

function rejectPurchaseOrder(frm) {
  frappe.confirm(
    `Are you sure you want to reject this purchase order?`,
    function () {
      frappe.call({
        method: "hkm.hkm_approval_matrix.main.reject_purchase_order",
        args: {
          docname: frm.doc.name,
          doctype: "Purchase Order",
        },
        freeze: true,
        freeze_message: "Rejecting Purchase Order",
        callback: (r) => {
          if (!r.exc) {
            // Show success message
            frappe.show_alert({
              message: "Purchase Order rejected successfully",
              indicator: "green",
            });

            // Reload document
            frm.reload_doc();
            frm.refresh();
          }
        },
      });
    }
  );
}

/**
 * Helper function to handle approval requests
 * @param {Object} frm - The form object
 * @param {string} method - The method to call (send_approval or resend_approval)
 * @param {string} action - The action description for confirmation dialog
 */
function handleApprovalRequest(frm, method, action) {
  frappe.confirm(`Are you sure you want to ${action}?`, function () {
    frappe.call({
      method: `hkm.hkm_approval_matrix.main.${method}`,
      args: {
        docname: frm.doc.name,
        doctype: "Purchase Order",
      },
      freeze: true,
      freeze_message: "Document Checked ... Setting Up Authorization",
      callback: (r) => {
        if (!r.exc) {
          // Show success message
          frappe.show_alert({
            message: "Purchase Order sent for approval",
            indicator: "green",
          });

          // Reload document
          if (!r.exc) {
            frm.reload_doc();
            frm.refresh();
          }
        }
      },
    });
  });
}

/**
 * Show modal to select resend method (Email or WhatsApp)
 * @param {Object} frm - The form object
 */
function showResendApprovalModal(frm) {
  let d = new frappe.ui.Dialog({
    title: __("Resend Approval Request"),
    fields: [
      {
        fieldtype: "HTML",
        options: `
          <div style="padding: 20px; text-align: center;">
            <p style="font-size: 14px; margin-bottom: 25px; color: #333;">
              How would you like to resend the approval request?
            </p>
            <div style="display: flex; gap: 15px; justify-content: center;">
              <button class="btn btn-primary resend-email-btn" style="
                background-color: #3399ff;
                color: white;
                border: none;
                padding: 12px 30px;
                font-weight: 600;
                border-radius: 4px;
                cursor: pointer;
                min-width: 150px;
              ">
                <i class="fa fa-envelope"></i> Resend via Email
              </button>
              <button class="btn btn-secondary resend-whatsapp-btn" style="
                background-color: #25D366;
                color: white;
                border: none;
                padding: 12px 30px;
                font-weight: 600;
                border-radius: 4px;
                cursor: pointer;
                min-width: 150px;
              ">
                <i class="fa fa-whatsapp"></i> Resend via WhatsApp
              </button>
            </div>
          </div>
        `,
      },
    ],
    primary_action_label: __("Cancel"),
    primary_action: function () {
      d.hide();
    },
  });

  // Add click handlers for custom buttons
  d.$wrapper.find(".resend-email-btn").on("click", function () {
    resendApprovalWithMethod(frm, "email");
    d.hide();
  });

  d.$wrapper.find(".resend-whatsapp-btn").on("click", function () {
    resendApprovalWithMethod(frm, "whatsapp");
    d.hide();
  });

  d.show();
}

/**
 * Resend approval with specified method
 * @param {Object} frm - The form object
 * @param {string} method - "email" or "whatsapp"
 */
function resendApprovalWithMethod(frm, method) {
  frappe.call({
    method: "hkm.hkm_approval_matrix.main.resend_approval",
    args: {
      docname: frm.doc.name,
      doctype: "Purchase Order",
      preferred_method: method,
    },
    freeze: true,
    freeze_message: `Resending approval via ${method === "whatsapp" ? "WhatsApp" : "Email"}...`,
    callback: (r) => {
      if (!r.exc) {
        // Show success message
        frappe.show_alert({
          message: r.message || `Approval resent successfully via ${method === "whatsapp" ? "WhatsApp" : "Email"}`,
          indicator: "green",
        });

        // Reload document
        frm.reload_doc();
        frm.refresh();
      }
    },
  });
}

/*
 * Purchase Order Item Events
 * Handles item-specific logic in the child table
 */
frappe.ui.form.on("Purchase Order Item", {
  /**
   * Set item type based on item properties when item code is selected
   */
  item_code(frm, cdt, cdn) {
    let row = frappe.get_doc(cdt, cdn);
    if (row.item_code) {
      frappe.db.get_doc("Item", row.item_code).then((doc) => {
        if (doc.is_fixed_asset == 1) {
          row.item_type = "Asset";
        } else if (doc.is_stock_item == 1) {
          row.item_type = "Stock";
        } else {
          row.item_type = "Non-Stock";
        }
        frm.refresh_field("items");
      });
    }
  },
});

frappe.listview_settings["Purchase Order"] = {
  has_indicator_for_draft: true,
  has_indicator_for_cancelled: true,

  add_fields: ["status_indicator"],

  get_indicator: function (doc) {

    if (doc.status_indicator == "Approved") {
      return [__("Approved"), "green", "docstatus,=,1"];
    }
    if (doc.status_indicator == "Cancelled") {
      return [__("Cancelled"), "red", "docstatus,=,2"];
    }
    if (doc.status_indicator == "Check Pending") {
      return [__("Check Pending"), "orange", "docstatus,=,0"];
    }
    if (doc.status_indicator == "Checked") {
      return [__("Checked"), "blue", "docstatus,=,0"];
    }
    if (doc.status_indicator == "Final Approval Pending") {
      return [__("Final Approval Pending"), "purple", "docstatus,=,0"];
    }
    if (doc.status_indicator == "Approval Started") {
      return [__("Approval Started"), "orange", "docstatus,=,0"];
    }
    if (doc.status_indicator == "Rejected") {
      return [__("Rejected"), "red", "docstatus,=,0"];
    }

    // fallback
    return [__("Draft"), "gray", "docstatus,=,0"];
  },
};
