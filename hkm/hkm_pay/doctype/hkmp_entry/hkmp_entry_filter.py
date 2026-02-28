ALL_ACCESS_ROLES = ["System Manager" , "Accounts User"]
import frappe
def list_filter(user=None):
    user = user or frappe.session.user
    user_roles = frappe.get_roles(user)
    has_full_access = any(role in ALL_ACCESS_ROLES for role in user_roles)
    if has_full_access:
        return "( 1 )"
    
    if "HKMP User" in user_roles:
        return f" ( user = '{user}' ) "
    return "( 0 )"

def doc_filter(doc, user=None):
    user = user or frappe.session.user
    user_roles = frappe.get_roles(user)
    has_full_access = any(role in ALL_ACCESS_ROLES for role in user_roles)
    if has_full_access:
        return True
    if "HKMP User" in user_roles:
        return doc.user == user
    return False