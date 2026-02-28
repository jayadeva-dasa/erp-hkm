import frappe

ADMIN_USER = "DD Manager"


def query(user):
    if ADMIN_USER in frappe.get_roles(frappe.session.user):
        return
    return f"(   user = '{user}' )"
