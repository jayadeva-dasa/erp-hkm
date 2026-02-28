from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
    get_accounting_dimensions,
)


relevant_documents = [
    "Material Request",
    "Purchase Order",
    "Purchase Invoice",
    "Sales Invoice",
    "Stock Entry",
    "Purchase Receipt",
]

import frappe


def set_dimensions(doc, method=None):
    # Early return if doctype is not relevant
    if doc.doctype not in relevant_documents:
        return
    
    # Check if document has required fields
    if not hasattr(doc, 'company') or not doc.company:
        return
        
    # Check if document has items field
    if not hasattr(doc, 'items') or not doc.items:
        return
    
    try:
        company_abbr = frappe.get_cached_value("Company", doc.company, "abbr")
        default_cost_center = "Main - " + company_abbr
        dimensions = get_accounting_dimensions()
        dimensions.extend(["cost_center", "project"])
        for dim in dimensions:
            if doc.get(dim):
                for item in doc.items:
                    if (not item.get(dim)) or (
                        dim == "cost_center" and item.get(dim) == default_cost_center
                    ):
                        item.update({dim: doc.get(dim)})
                if doc.get("taxes"):
                    for tc in doc.taxes:
                        if (not tc.get(dim)) or (
                            dim == "cost_center" and tc.get(dim) == default_cost_center
                        ):
                            tc.update({dim: doc.get(dim)})
    except Exception as e:
        frappe.log_error(f"Error in set_dimensions for {doc.doctype}: {str(e)}")
        # Don't raise the error, just log it to prevent blocking document saves
        pass
