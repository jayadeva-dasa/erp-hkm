import frappe
from frappe.contacts.doctype.address.address import get_address_display
from frappe.utils import time_diff_in_hours, time_diff_in_seconds, date_diff, flt
from frappe.model.workflow import apply_workflow
from frappe.utils.background_jobs import enqueue
from frappe import _


item_supplier_admin = "Item Manager"


def creation_from_gstin(self, method):
    if (
        self.is_new()
        and not self.get("gstin")
        and not item_supplier_admin in frappe.get_roles(frappe.session.user)
    ):
        frappe.throw(
            "You are not allowed to create a Supplier without GSTIN. Raise through Supplier Creation Request."
        )
    return


def set_concerned_person(self, method):
    """
    Automatically set the concerned person field when a supplier is created.
    
    Logic:
    1. If supplier is created from Supplier Creation Request, use the owner of that request
    2. Otherwise, use the owner/creator of the Supplier document
    """
    # Only set on new documents
    if not self.is_new():
        return
    
    # Skip if concerned person is already set
    if self.get("custom_concerned_person"):
        return
    
    try:
        # Check if supplier was created from Supplier Creation Request
        if self.get("supplier_creation_request"):
            # Get the owner of the Supplier Creation Request
            scr_owner = frappe.db.get_value(
                "Supplier Creation Request",
                self.supplier_creation_request,
                "owner"
            )
            if scr_owner:
                self.custom_concerned_person = scr_owner
                frappe.logger().info(
                    f"Set concerned person for {self.name} to {scr_owner} from SCR"
                )
        else:
            # Use the owner of the Supplier document
            self.custom_concerned_person = self.owner
            frappe.logger().info(
                f"Set concerned person for {self.name} to {self.owner} from owner"
            )
    except Exception as e:
        frappe.log_error(
            message=f"Error setting concerned person for Supplier {self.name}: {str(e)}",
            title="Supplier Concerned Person Error"
        )