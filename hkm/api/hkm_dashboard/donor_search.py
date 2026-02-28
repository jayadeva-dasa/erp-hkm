"""
Donor Search API Wrapper
Wraps Dhananjaya APIs with permission checks
Only DCC Manager can access
"""

import frappe
from frappe import _


# Hardcoded permission - Only DCC Manager
DONOR_SEARCH_ALLOWED_ROLES = ["DCC Manager", "System Manager"]


def check_donor_search_permission():
    """Check if user has permission to access Donor Search"""
    user_roles = frappe.get_roles(frappe.session.user)
    has_access = any(role in DONOR_SEARCH_ALLOWED_ROLES for role in user_roles)
    
    if not has_access:
        frappe.throw(
            _("You don't have permission to access Donor Search. Required roles: {0}").format(
                ", ".join(DONOR_SEARCH_ALLOWED_ROLES)
            ),
            frappe.PermissionError
        )


# Parameters accepted by Dhananjaya donor search API (exclude RPC keys like 'cmd')
DONOR_SEARCH_PARAMS = frozenset({
    "name_query", "phone_query", "address_query", "start", "page_length"
})


@frappe.whitelist()
def search_donors(**kwargs):
    """
    Wrapper for Dhananjaya donor search API
    Checks permission before forwarding to actual API
    """
    check_donor_search_permission()

    # Only pass params that Dhananjaya search() accepts (strip cmd and other RPC keys)
    filtered = {k: v for k, v in kwargs.items() if k in DONOR_SEARCH_PARAMS}

    # Forward to actual Dhananjaya API
    try:
        # Import the actual Dhananjaya search function
        from dhananjaya.api.v1.donor_search import search as dhananjaya_search
        return dhananjaya_search(**filtered)
    except ImportError as ie:
        frappe.log_error(f"Dhananjaya import error: {str(ie)}")
        frappe.throw(_("Dhananjaya app not installed or API not found"))
    except Exception as e:
        frappe.log_error(f"Donor Search API error: {str(e)}")
        frappe.throw(_("Error searching donors: {0}").format(str(e)))

