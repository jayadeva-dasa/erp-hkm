# Copyright (c) 2025, HKM and contributors
# For license information, please see license.txt

import frappe
from frappe import _

@frappe.whitelist()
def get_accounting_dimension_fields():
    """
    Get list of all accounting dimension fields (both standard and custom).
    Returns field names that should be hidden for auditors.
    """
    try:
        # Standard accounting dimensions
        dimension_fields = ["cost_center", "project"]
        
        # Get custom accounting dimensions from ERPNext
        try:
            # Import from ERPNext if available
            from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_accounting_dimensions
            custom_dimensions = get_accounting_dimensions() or []
            dimension_fields.extend(custom_dimensions)
        except ImportError:
            # If ERPNext module not available, fetch from Accounting Dimension doctype
            custom_dims = frappe.get_all(
                "Accounting Dimension",
                fields=["fieldname"],
                filters={"disabled": 0}
            )
            dimension_fields.extend([d.fieldname for d in custom_dims if d.fieldname])
        
        return {"success": True, "data": dimension_fields}
    except Exception as e:
        frappe.log_error(f"Error fetching accounting dimension fields: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def get_doctypes_with_accounting_dimensions():
    """
    Get list of doctypes that have accounting dimensions.
    This function returns all doctypes that are configured to use accounting dimensions.
    """
    try:
        # Get doctypes with accounting dimensions from hooks
        doctypes = frappe.get_hooks("accounting_dimension_doctypes")
        
        # Classify doctypes as parent or child
        result = []
        for doctype in doctypes:
            # Check if this is a child table
            meta = frappe.get_meta(doctype, cached=True)
            is_child = getattr(meta, 'istable', False) if meta else False
            
            result.append({
                'doctype': doctype,
                'is_child': is_child
            })
        
        return {"success": True, "data": result}
    except Exception as e:
        frappe.log_error(f"Error fetching doctypes with accounting dimensions: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def hide_accounting_dimensions_for_auditor(doctype=None):
    """
    Check if the current user is an auditor and should have accounting dimensions hidden.
    This function can be called from the frontend to determine if accounting dimensions
    should be hidden for the current user on a specific doctype.
    
    Args:
        doctype (str): The doctype to check
        
    Returns:
        dict: Result with should_hide flag
    """
    try:
        # Define accounting roles
        accounting_roles = [
            "Accounts Admin",
            "Accounts Manager", 
            "Accounts User"
        ]
        
        # Check if user has any accounting role
        user_roles = frappe.get_roles()
        has_accounting_role = any(role in accounting_roles for role in user_roles)
        
        # If user has accounting role, don't hide
        if has_accounting_role:
            return {"success": True, "should_hide": False}
            
        # Check if user has auditor role
        is_auditor = "Auditor" in user_roles
        
        # Hide only for auditors
        should_hide = is_auditor
        
        return {"success": True, "should_hide": should_hide}
        
    except Exception as e:
        frappe.log_error(f"Error checking if accounting dimensions should be hidden: {str(e)}")
        return {"success": False, "error": str(e)}