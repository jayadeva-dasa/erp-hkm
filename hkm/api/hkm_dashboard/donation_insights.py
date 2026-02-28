"""
Donation Insights API Wrapper
Wraps Dhananjaya APIs with permission checks
Only System Manager can access
"""

import frappe
from frappe import _


# Hardcoded permission - Only System Manager
DONATION_INSIGHTS_ALLOWED_ROLES = ["System Manager"]


def check_donation_insights_permission():
    """Check if user has permission to access Donation Insights"""
    user_roles = frappe.get_roles(frappe.session.user)
    has_access = any(role in DONATION_INSIGHTS_ALLOWED_ROLES for role in user_roles)
    
    if not has_access:
        frappe.throw(
            _("You don't have permission to access Donation Insights. Required roles: {0}").format(
                ", ".join(DONATION_INSIGHTS_ALLOWED_ROLES)
            ),
            frappe.PermissionError
        )


@frappe.whitelist()
def get_donation_insights(**kwargs):
    """
    Wrapper for Dhananjaya donation insights API
    Checks permission before forwarding to actual API
    """
    check_donation_insights_permission()
    
    # Forward to actual Dhananjaya API
    try:
        # Import the actual Dhananjaya function
        from dhananjaya.api.v1.donation_insights import get_donation_insights as dhananjaya_api
        return dhananjaya_api(**kwargs)
    except ImportError as ie:
        frappe.log_error(f"Dhananjaya import error: {str(ie)}")
        frappe.throw(_("Dhananjaya app not installed or API not found"))
    except Exception as e:
        frappe.log_error(f"Donation Insights API error: {str(e)}")
        frappe.throw(_("Error fetching donation insights: {0}").format(str(e)))

