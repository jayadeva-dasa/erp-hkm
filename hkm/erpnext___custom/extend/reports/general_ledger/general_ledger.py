import frappe
from erpnext.accounts.report.general_ledger.general_ledger import execute as general_ledger_execute

def execute(filters=None):
    user_roles = frappe.get_roles(frappe.session.user)

    # Normal users: no changes
    if "Auditor" not in user_roles:
        return general_ledger_execute(filters)

    filters = sanitize_filters(filters)

    columns, data, *args = general_ledger_execute(filters)

    columns = get_columns(columns)

    return columns, data, *args


def sanitize_filters(filters):
    """Remove accounting dimension filters for Auditor users"""
    filters = frappe._dict(filters or {})

    dimension_fields = frappe.get_all("Accounting Dimension", pluck="fieldname")

    # Remove all dimensions from filters
    for f in dimension_fields:
        filters.pop(f, None)

    # Optionally remove project/cost_center also if you want them hidden fully
    filters.pop("project", None)
    filters.pop("cost_center", None)

    return filters


def get_columns(columns):
    dimension_fields = frappe.get_all("Accounting Dimension", pluck="fieldname")

    return [
        c for c in columns
        if c.get("fieldname") not in ("project", "cost_center", *dimension_fields)
    ]
