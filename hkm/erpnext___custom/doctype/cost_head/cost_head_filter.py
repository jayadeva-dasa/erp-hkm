from hkm.api.v1.accounting import hide_accounting_dimensions_for_auditor
import frappe
from frappe.utils.nestedset import get_descendants_of

EXCLUDE_ROLES = ["System Manager", "Accounts Admin",
                 "Accounts User", "Accounts Manager"]


def list(user):

    user = frappe.session.user
    user_roles = frappe.get_roles(user)
    if "Auditor" in user_roles:
        return "( 0 )"
    
    

    return "( 1 )"


def single(doc, user=None, permission_type=None):
    user = frappe.session.user
    user_roles = frappe.get_roles(user)
    if "Auditor" in user_roles:
        return False

    return True




from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_dimensions

@frappe.whitelist()
def get_accounting_dimension(with_cost_center_and_project=False):
    user = frappe.session.user
    user_roles = frappe.get_roles(user)
    if "Auditor" in user_roles:
        dimension_filters = [
            frappe._dict({"fieldname": "cost_center", "document_type": "Cost Center"}),
            frappe._dict({"fieldname": "project", "document_type": "Project"}),
        ]

        # No default dimensions from Accounting Dimension Detail
        default_dimensions_map = {}

        return dimension_filters, default_dimensions_map
    
    return get_dimensions(with_cost_center_and_project=with_cost_center_and_project)
        
