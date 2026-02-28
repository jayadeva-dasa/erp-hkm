import frappe

# from nexus.utils.roles import ALL_SADHAK_ROLES, get_allowed_preachers

ADMIN_ROLES = ["System Manager"]


def list_filter(user=None):
    user = user or frappe.session.user
    user_roles = frappe.get_roles(user)

    has_full_access = any(role in ADMIN_ROLES for role in user_roles)

    if has_full_access:
        return "( 1 )"

    return f" (`next_approver` = ({user}) )"


def has_single_access(doc, user=None):
    """Check if the user has single access to the given doc."""
    user = user or frappe.session.user
    user_roles = frappe.get_roles(user)

    return any(role in ADMIN_ROLES for role in user_roles) or (
        doc.next_approver == user
    )
