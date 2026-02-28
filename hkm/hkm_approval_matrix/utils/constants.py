"""Constants used throughout the approval matrix module."""

import frappe

# Action constants
APPROVE = "Approve"
REJECTED = "Rejected"

# Field and DocType constants
CHILD_TABLE_FIELD = "approving_authorities"
APPROVAL_MATRIX = "Approval Matrix"

# Role constants
FULL_ACCESS_ROLES = ["Administrator", "System Manager"]
CUSTOM_FIELDS = [
    "approving_authorities",
    "docstatus",
    "locked",
    "approval_initiator",
    "approval_status",
    "current_approving_authority",
]


SAFE_GLOBALS = dict(
    frappe=frappe._dict(
        db=frappe._dict(get_value=frappe.db.get_value, get_list=frappe.db.get_list),
        session=frappe.session,
        utils=frappe._dict(
            now_datetime=frappe.utils.now_datetime,
            add_to_date=frappe.utils.add_to_date,
            get_datetime=frappe.utils.get_datetime,
            now=frappe.utils.now,
        ),
    )
)


IGNORED_FIELDS = [
    "workflow_state",
    "modified",
    "modified_by",
    "creation",
    "owner",
    "idx",
    "name",
    "doctype",
    "__unsaved",
    "__onload",
    "approved",
    "parent",
    "parentfield",
    "parenttype",
    "Section Break",
    "Column Break",
    "Tab Break",
]
