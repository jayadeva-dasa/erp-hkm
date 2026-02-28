"""
Main API endpoints for HKM Approval Matrix.
This module provides the primary API functions while delegating
implementation details to specialized utility modules.
"""

from re import A
import frappe
from frappe import _
import requests
import json
import imgkit

# Import reorganized utility modules
from .utils.general import (
    is_doctype_in_approval_matrix,
    get_current_approving_authority,
    set_approving_authority,
)


from .utils.notification_services import (
    send_whatsapp_approval,
    send_approval_email,
    is_eligible_to_send_on_whatsapp,
    notify_next_authority,
)

from .utils.validation import (
    validate,
)


def _check_permissions(message=None):
    """Check if user has permission to send/manage approvals."""

    roles = frappe.get_roles(frappe.session.user)
    if "Purchase Manager" not in roles and frappe.session.user != "Administrator":
        if "System Manager" not in roles:
            message = (
                message or "Purchase Manager or System Manager can only send approval"
            )

            frappe.throw(message)


def _get_success_response(message, docname, doctype):
    """Get standardized success response."""
    return {
        "status": "success",
        "message": message,
        "reload_doc": True,
        "docname": docname,
        "doctype": doctype,
    }


@frappe.whitelist()
def send_approval(doctype, docname):
    _check_permissions()

    # Set approving authorities
    set_approving_authority(doctype, docname)

    doc = frappe.get_doc(doctype, docname)
    approving_authority = get_current_approving_authority(doctype, docname)

    mobile_no = frappe.db.get_value("User", approving_authority, "mobile_no")

    doc.approval_status = f"0/{len(doc.approving_authorities)} Approved"

    if is_eligible_to_send_on_whatsapp(approving_authority, mobile_no):
        send_whatsapp_approval(doctype, docname, doc, approving_authority, mobile_no)
    else:
        send_approval_email(doctype, docname, doc, approving_authority)

    from .utils.notification_services import assign_to_authority

    assign_to_authority(doctype, docname, approving_authority)

    frappe.db.set_value(
        doctype,
        docname,
        {
            "locked": 1,
            "approval_initiator": frappe.session.user,
            "approval_status": f"0/{len(doc.approving_authorities)} Approved",
            "status_indicator": "Checked",
            "current_approving_authority": get_current_approving_authority(
                doctype, docname
            ),
        },
    )
    frappe.db.commit()  # v16: REVIEW - check if needed

    return _get_success_response("Approval sent successfully", docname, doctype)


@frappe.whitelist()
def before_save(doc, method=None):
    """Validate document freeze state during updates."""

    if (
        not is_doctype_in_approval_matrix(doc.doctype)
        or doc.docstatus in [1, 2]
        or not doc.locked
        or doc.is_new()
    ):
        return

    validate(doc)


def on_cancel(doc, method=None):
    """Cancel approval before document cancellation."""
    if not is_doctype_in_approval_matrix(doc.doctype):
        return

    frappe.db.set_value(
        doc.doctype,
        doc.name,
        {
            "status_indicator": "Cancelled",
        },
    )
    # frappe.db.commit()  # v16: REMOVED - not allowed in document hooks


def before_submit(doc, method=None):
    """Validate approval before document submission."""
    if not is_doctype_in_approval_matrix(doc.doctype):
        return

    if not doc.locked and not doc.approving_authorities:
        frappe.throw(
            "This document has not been checked by the Purchase Manager. Please click Check to proceed."
        )

    if not doc.approving_authorities:
        frappe.throw(
            "Approving authorities not found for this document. They are required to submit the document."
        )

    if not all(
        authority.status == "Approved" for authority in doc.approving_authorities
    ):
        frappe.throw(
            "Document cannot be submitted as all authorities have not approved yet."
        )

    frappe.db.set_value(
        doc.doctype,
        doc.name,
        {
            "status_indicator": "Approved",
        },
    )
    frappe.db.commit()  # v16: REVIEW - check if needed


def clear_assignment(doc):
    from frappe.desk.form.assign_to import clear

    # clear(doc.doctype, doc.name)
    frappe.db.delete(
            "ToDo", {"reference_type": doc.doctype, "reference_name": doc.name}
        )

    # frappe.db.set_value(
    #     "ToDo",
    #     {"reference_type": doc.doctype, "reference_name": doc.name},
    #     "status",
    #     "Closed",
    # )
    # frappe.db.commit()


def on_submit(doc, method=None):
    if is_doctype_in_approval_matrix(doc.doctype):
        clear_assignment(doc)


def on_update(doc, method=None):
    """Handle document updates and auto-submission when all approvals are complete."""
    if (
        not is_doctype_in_approval_matrix(doc.doctype)
        or doc.docstatus in [1, 2]
        or not doc.locked
    ):
        return

    if not doc.approving_authorities and doc.current_approving_authority is not None:
        frappe.db.set_value(
            doc.doctype,
            doc.name,
            {
                "current_approving_authority": None,
            },
        )
        # frappe.db.commit()  # v16: REMOVED - not allowed in document hooks
        return

    approved_count = sum(1 for a in doc.approving_authorities if a.status == "Approved")
    total = len(doc.approving_authorities)

    # If any rejected → Rejected else show progress
    status = (
        "Rejected"
        if any(a.status == "Rejected" for a in doc.approving_authorities)
        else f"{approved_count}/{total} Approved"
    )

    approval_indicator = "Checked"

    if status != "Rejected":
        approval_indicator = "Checked"
        if approved_count == 1:
            approval_indicator = "Approval Started"
        if (approved_count + 1) == total:
            approval_indicator = "Final Approval Pending"
        if approved_count == total:
            approval_indicator = "Approved"

    if status == "Rejected":
        approval_indicator = "Rejected"

    frappe.db.set_value(
        doc.doctype,
        doc.name,
        {
            "approval_status": status,
            "current_approving_authority": get_current_approving_authority(
                doc.doctype, doc.name
            ),
            "status_indicator": approval_indicator,
        },
    )

    frappe.db.commit()  # v16: REVIEW - check if needed

    if all(authority.status == "Approved" for authority in doc.approving_authorities):
        try:
            doc = frappe.get_doc(doc.doctype, doc.name)
            doc.flags.ignore_permissions = True
            doc.flags.ignore_frozen_transaction = True
            doc.submit()
        except Exception as e:
            frappe.log_error(
                f"Error submitting document {doc.doctype} {doc.name}: {str(e)}"
            )
        frappe.db.set_value(
            doc.doctype,
            doc.name,
            {
                "current_approving_authority": None,
            },
        )
    else:
        clear_assignment(doc)
        notify_next_authority(doc)
    frappe.db.commit()  # v16: REVIEW - check if needed


@frappe.whitelist()
def make_doc_editable(doctype, docname):
    """
    API endpoint to make a document editable.
    Resets the document's approval state if conditions are met.
    """

    if frappe.db.get_value(doctype, docname, "locked") == 0:
        frappe.throw("Document is not locked make editable not allowed")

    _check_permissions("You are not authorized to make this document editable")

    frappe.db.set_value(
        doctype,
        docname,
        {
            "locked": 0,
            "approval_initiator": None,
            "approval_status": None,
            "current_approving_authority": None,
            "status_indicator": "Check Pending",
        },
    )
    frappe.db.commit()  # v16: REVIEW - check if needed
    doc = frappe.get_doc(doctype, docname)
    doc.approving_authorities = []
    doc.flags.ignore_frozen_transaction = True
    doc.save()
    frappe.db.commit()  # v16: REVIEW - check if needed


@frappe.whitelist()
def resend_approval(doctype, docname, preferred_method=None):
    """
    Resend approval notification to the current approving authority.
    Does not reset the approval matrix, only resends notification.
    
    Args:
        doctype: Document type
        docname: Document name
        preferred_method: Optional. "email" or "whatsapp" to force a specific method.
                         If not provided, automatically selects based on eligibility.
    """
    if frappe.db.get_value(doctype, docname, "locked") == 0:
        frappe.throw("Document is not locked resend not allowed")

    _check_permissions("You are not authorized to resend this document for approval")
    
    # Get current approving authority
    current_authority = get_current_approving_authority(doctype, docname)
    
    if not current_authority:
        frappe.throw("No current approving authority found. Cannot resend approval.")
    
    # Get document
    doc = frappe.get_doc(doctype, docname)
    
    # Get mobile number for WhatsApp eligibility check
    mobile_no = frappe.db.get_value("User", current_authority, "mobile_no")
    
    # Determine notification method
    use_whatsapp = False
    if preferred_method:
        preferred_method = preferred_method.lower()
        if preferred_method == "whatsapp":
            if not mobile_no:
                frappe.throw("WhatsApp cannot be used: Mobile number not found for the approving authority.")
            use_whatsapp = True
        elif preferred_method == "email":
            use_whatsapp = False
        else:
            frappe.throw(f"Invalid preferred_method: {preferred_method}. Must be 'email' or 'whatsapp'.")
    else:
        # Auto-detect based on eligibility
        use_whatsapp = is_eligible_to_send_on_whatsapp(current_authority, mobile_no)
    
    # Resend notification to current authority
    if use_whatsapp:
        send_whatsapp_approval(doctype, docname, doc, current_authority, mobile_no)
        method_used = "WhatsApp"
    else:
        send_approval_email(doctype, docname, doc, current_authority)
        method_used = "Email"
    
    # Re-assign ToDo to current authority
    from .utils.notification_services import assign_to_authority
    assign_to_authority(doctype, docname, current_authority)
    
    frappe.db.commit()  # v16: REVIEW - check if needed

    # Return success response with reload instruction
    return _get_success_response(
        f"Approval resent successfully via {method_used} to current authority", 
        docname, 
        doctype
    )


def _update_authority_status(doctype, docname, status):
    """Update the current user's authority status for a document."""
    # if frappe.session.user != get_current_approving_authority(doctype, docname):
    #     frappe.throw(f"You are not authorized to {status.lower()} this document")

    doc = frappe.get_doc(doctype, docname)
    doc.flags.ignore_permissions = True
    for authority in doc.approving_authorities:
        if authority.authority == frappe.session.user:
            authority.status = status
            break
    doc.flags.ignore_frozen_transaction = True
    doc.save()
    doc.reload()
    frappe.db.commit()  # v16: REVIEW - check if needed
    return _get_success_response(
        f"Document {status.lower()} successfully", docname, doctype
    )


@frappe.whitelist()
def approve_purchase_order(doctype, docname):
    if frappe.db.get_value(doctype, docname, "locked") == 0:
        frappe.throw("Document is not locked approve not allowed")
    return _update_authority_status(doctype, docname, "Approved")


@frappe.whitelist()
def reject_purchase_order(doctype, docname):
    if frappe.db.get_value(doctype, docname, "locked") == 0:
        frappe.throw("Document is not locked reject not allowed")
    return _update_authority_status(doctype, docname, "Rejected")


@frappe.whitelist(allow_guest=True)
def get_purchase_order_image(docname):
    docs = frappe.get_all("Purchase Order", fields=["*"], filters={"name": docname})
    if not docs:
        frappe.throw("Doesn't exist.")
    doc = frappe._dict(docs[0])
    items = frappe.get_all(
        "Purchase Order Item",
        fields=["*"],
        filters={"parent": doc.name},
        order_by="idx asc",
    )
    currency = frappe.get_cached_value("Company", doc.company, "default_currency")
    template_data = {
        "doc": doc,
        "currency": currency,
        "items": items,
        "document_link": frappe.utils.get_url_to_form("Purchase Order", doc.name),
    }
    message_html = frappe.render_template(
        "hkm/erpnext___custom/overrides/purchase_order/templates/whatsapp_template.html",
        template_data,
    )
    img = imgkit.from_string(
        message_html,
        False,
        options={
            "format": "png",
        },
    )

    frappe.local.response.filename = f"approval_{doc.name}.png"
    frappe.local.response.filecontent = img
    frappe.local.response.type = "download"


@frappe.whitelist()
def cancel_purchase_order(doctype, docname):
    _check_permissions("You are not authorized to cancel this document")
    if frappe.db.get_value(doctype, docname, "locked") == 1:
        frappe.throw("Document is locked cancel not allowed")

    frappe.db.set_value(
        doctype,
        docname,
        {
            "docstatus": 2,
            "status_indicator": "Cancelled",
        },
    )
    frappe.db.commit()  # v16: REVIEW - check if needed


def correct_mrn():
    name = "MAT-MR-2024-09224"
    frappe.db.set_value(
        "Material Request",
        name,
        {
            "docstatus": 1,
            "status": "Ordered",
            "execution_department": "Civil (General)",
            "cost_head": "Civil / Maintainance",
        },
    )

    frappe.db.commit()


def correct_purchase_order():
    name = "WOR-ORD-2024-01641"
    approving_authority = ["rtgd@hkmjaipur.org",  "sysd@hkmjaipur.org" , "amitdas@iskconbangalore.org"]
    correct_mrn()
    frappe.db.set_value(
        "Purchase Order",
        name,
        {
            "docstatus": 0,
            "locked": 0,
            "approval_initiator": "rtgd@hkmjaipur.org",
            "approval_status": "3/3 Approved",
            "current_approving_authority": None,
            "cost_head": "Civil / Maintainance",
        },
    )

    frappe.db.commit()
    doc = frappe.get_doc("Purchase Order", name)
    doc.approving_authorities = []

    for authority in approving_authority:
        doc.append("approving_authorities", {"authority": authority})
    doc.flags.ignore_frozen_transaction = True
    doc.save()

    for i in frappe.get_all(
        "Approval Matrix Authority",
        filters={"parent": name, "parenttype": "Purchase Order"},
    ):
        frappe.db.set_value(
            "Approval Matrix Authority",
            i.name,
            {
                "status": "Approved",
            },
        )

    frappe.db.commit()

    frappe.db.set_value(
        "Purchase Order",
        name,
        {
            "docstatus": 1,
            "locked": 1,
            "status_indicator": "Approved",
        },
    )

    frappe.db.commit()


def assign_to_authority():
    result = frappe.db.sql(
        """
        
        SELECT 
            po.name ,
            po.current_approving_authority ,
            td.allocated_to 
        FROM `tabPurchase Order` po
        LEFT JOIN `tabToDo` td
            ON po.name = td.reference_name
        AND td.reference_type = "Purchase Order"
        AND td.allocated_to = po.current_approving_authority
        WHERE po.docstatus = 0
        AND po.status_indicator != "Check Pending"
        AND po.current_approving_authority IS NOT NULL
        AND td.allocated_to is NULL
        ;
                """,
        as_dict=True,
    )
    for po in result:
        if frappe.db.exists(
            "ToDo",
            {
                "reference_type": "Purchase Order",
                "reference_name": po.name,
                "allocated_to": po.current_approving_authority,
            },
        ):
            # frappe.log_error(
            #     "ToDo already exists for {doctype} {docname} for {user}".format(
            #         doctype="Purchase Order", docname=po, user=user
            #     )
            # )
            continue

        frappe.get_doc(
            {
                "doctype": "ToDo",
                "allocated_to": po.current_approving_authority,
                "reference_type": "Purchase Order",
                "reference_name": po.name,
                "description": f"Purchase Order {po.name} is assigned to you for approval.",
                "priority": "Medium",
                "status": "Open",
                "date": frappe.utils.nowdate(),
                "assigned_by": frappe.session.user,
                "assignment_rule": "",
            }
        ).insert(ignore_permissions=True)
    frappe.db.commit()  # v16: REVIEW - check if needed


def submit_po():

    for i in ["PUR-ORD-2025-05160"]:
        doc = frappe.get_doc("Purchase Order", i)
        if all(
            authority.status == "Approved" for authority in doc.approving_authorities
        ):
            doc.flags.ignore_permissions = True
            doc.flags.ignore_frozen_transaction = True
            doc.submit()
            frappe.db.set_value(
                doc.doctype,
                doc.name,
                {
                    "current_approving_authority": None,
                },
            )
    frappe.db.commit()  # v16: REVIEW - check if needed
