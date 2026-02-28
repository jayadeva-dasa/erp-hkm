# Frappe imports
import frappe
from frappe import _
from frappe.utils.verified_command import verify_request

# Local imports
from urllib.parse import parse_qsl

# Third-party imports
from cryptography.fernet import Fernet


from frappe.workflow.doctype.workflow_action.workflow_action import (
    return_action_confirmation_page,
)

from hkm.hkm_approval_matrix.utils.notification_services import (
    get_secret_key,
    get_url,
)
from hkm.hkm_approval_matrix.utils.constants import APPROVE, REJECTED


def respond_error(message):
    """Respond with error message."""
    frappe.respond_as_web_page(
        _("Error"),
        _(message),
        indicator_color="red",
    )


def respond_success(message):
    """Respond with success message."""
    frappe.respond_as_web_page(
        _("Success"),
        _(message),
        indicator_color="green",
    )


def validate_request():
    if not verify_request():
        return False
    return True


def decrypt_and_parse_data(data):
    secret_key = get_secret_key()
    decrypted = Fernet(secret_key).decrypt(data.encode()).decode()
    params = dict(parse_qsl(decrypted))

    doctype = params.get("doctype", "").strip()
    docname = params.get("docname", "").strip()
    action = params.get("action", "").strip()
    user = params.get("user", "").strip()

    return doctype, docname, action, user


def _validate_approval_request(data):

    if data is None:
        data = frappe.form_dict.get("data") or frappe.request.args.get("data")

        if not data:
            return None, {"success": False, "error": "Missing required data parameter"}

    """Validate approval request and return parsed data."""
    if not validate_request():

        return None, {"success": False, "error": "Request validation failed"}

    if not data:
        return None, {"success": False, "error": "Missing required data parameter"}

    try:

        doctype, docname, action, user = decrypt_and_parse_data(data)

        if not frappe.db.exists("User", user):
            return None, {"success": False, "error": "User not found"}
        
        # Check if user is enabled
        if not frappe.get_cached_value("User", user, "enabled"):
            return None, {
                "success": False, 
                "error": f"User {user} is disabled. Please contact your System Manager."
            }

        return (doctype, docname, action, user), None
    except Exception as e:
        return None, {"success": False, "error": f"Failed to parse data: {str(e)}"}


@frappe.whitelist(allow_guest=True)
def approval_matrix_apply_action(data=None):
    """Handle approval matrix action application."""

    result, error = _validate_approval_request(data)

    if error:
        respond_error(error.get("error", "Validation failed"))
        return

    # print(result)
    # frappe.throw("data")

    doctype, docname, action, user = result

    action_link = get_url(doctype, docname, action, user, confirm=True)

    doc = frappe.get_doc(doctype, docname)
    doc.flags.ignore_permissions = True
    doc.flags.ignore_frozen_transaction = True

    try:
        for row in doc.approving_authorities:
            if row.authority == frappe.session.user:
                if row.status == "Approved":
                    frappe.throw(_("You have already approved this document"))
                elif row.status == "Rejected":
                    frappe.throw(_("You have already rejected this document"))

    except Exception as e:
        respond_error(f"Failed to apply action: {str(e)}")
        return

    return return_action_confirmation_page(doc, action, action_link)


@frappe.whitelist(allow_guest=True)
def approval_matrix_confirm_action(data=None):
    """Handle approval matrix action confirmation."""
    result, error = _validate_approval_request(data)

    if error:
        respond_error(error.get("error", "Validation failed"))
        return

    doctype, docname, action, user = result
    if not user:
        respond_error("User not found")
        return

    logged_in_user = frappe.session.user
    user_context_changed = False

    try:
        # Set user if guest and user is valid
        if (
            logged_in_user == "Guest"
            and user
            and frappe.db.exists("User", user)
            and frappe.get_cached_value("User", user, "enabled")
            and frappe.session.user != user
        ):
            frappe.set_user(user)
            user_context_changed = True

        # Get document
        doc = frappe.get_doc(doctype, docname)
        doc.flags.ignore_permissions = True

        try:
            for row in doc.approving_authorities:
                if row.authority == frappe.session.user:
                    if row.status == "Approved":
                        frappe.throw(_("You have already approved this document"))
                    elif row.status == "Rejected":
                        frappe.throw(_("You have already rejected this document"))

        except Exception as e:
            respond_error(f"Failed to apply action: {str(e)}")
            return

        if doc.docstatus == 2:
            respond_error("Document is Cancelled")
            return

        for authority in doc.approving_authorities:
            if authority.authority == user:

                if authority.status == "":
                    authority.status = (
                        "Approved" if action.lower() == APPROVE.lower() else "Rejected"
                    )
                    break
        doc.flags.ignore_frozen_transaction = True
        doc.save()
        frappe.db.commit()  # v16: REVIEW - check if needed

        respond_success("Action applied successfully")
        return

    except Exception as e:
        frappe.log_error(f"Failed to apply action: {str(e)}", "Approval Matrix Error")
        respond_error(f"Failed to apply action: {str(e)}")
        return
    finally:
        # Reset session user only if it was changed
        if user_context_changed:
            frappe.set_user(logged_in_user)
