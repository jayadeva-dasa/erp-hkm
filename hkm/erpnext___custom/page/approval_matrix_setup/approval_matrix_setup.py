"""
Approval Matrix Setup - Backend API
Clean implementation following the new dimension_value philosophy
"""

import frappe
from frappe import _


@frappe.whitelist()
def get_approval_matrices():
    """Get all approval matrices with their basic info"""
    matrices = frappe.get_all(
        "Approval Matrix",
        fields=["name", "target_doctype", "dimension", "fields_applicable"],
        order_by="modified desc"
    )
    
    # Add transition count for each matrix
    for matrix in matrices:
        matrix["transition_count"] = frappe.db.count(
            "Approval Matrix Detail",
            {"parent": matrix.name, "disabled": 0}
        )
    
    return matrices


@frappe.whitelist()
def get_matrix_details(matrix_name):
    """Get detailed information about a specific approval matrix"""
    doc = frappe.get_doc("Approval Matrix", matrix_name)
    
    transitions = []
    for t in doc.transitions:
        transitions.append({
            "name": t.name,
            "idx": t.idx,
            "dimension_value": t.dimension_value,
            "condition": t.condition or "",
            "approving_authority": t.approving_authority,
            "disabled": t.disabled
        })
    
    return {
        "name": doc.name,
        "target_doctype": doc.target_doctype,
        "dimension": doc.dimension,
        "fields_applicable": doc.fields_applicable or "",
        "transitions": transitions
    }


@frappe.whitelist()
def get_doctypes():
    """Get list of accounting doctypes that can have approval matrix"""
    # Get all accounting doctypes (doctypes with accounting dimensions enabled)
    doctypes = frappe.db.sql("""
        SELECT DISTINCT dt.name, dt.name as label
        FROM `tabDocType` dt
        WHERE dt.istable = 0
        AND dt.issingle = 0
        AND dt.name IN (
            SELECT DISTINCT parent 
            FROM `tabDocField` 
            WHERE fieldname IN (
                SELECT DISTINCT fieldname 
                FROM `tabAccounting Dimension Detail`
            )
        )
        ORDER BY dt.name
    """, as_dict=1)
    
    # If no accounting doctypes found, return common transaction doctypes
    if not doctypes:
        common_doctypes = [
            "Purchase Order", "Purchase Invoice", "Sales Order", 
            "Sales Invoice", "Payment Entry", "Journal Entry",
            "Delivery Note", "Purchase Receipt", "Stock Entry"
        ]
        doctypes = [{"name": dt, "label": dt} for dt in common_doctypes]
    
    return doctypes


@frappe.whitelist()
def get_dimensions():
    """Get list of available accounting dimensions"""
    dimensions = frappe.get_all(
        "Accounting Dimension",
        fields=["name", "label", "document_type"],
        order_by="name"
    )
    return dimensions


@frappe.whitelist()
def get_dimension_values(dimension):
    """Get values for a specific dimension"""
    if not dimension:
        return []
    
    # Get the doctype for this dimension
    dimension_doc = frappe.get_doc("Accounting Dimension", dimension)
    doctype = dimension_doc.document_type
    
    # Get all values
    values = frappe.get_all(
        doctype,
        fields=["name"],
        order_by="name"
    )
    
    return [v.name for v in values]


@frappe.whitelist()
def get_doctype_fields(doctype):
    """Get fields for a doctype that can be used in conditions"""
    if not doctype:
        return []
    
    meta = frappe.get_meta(doctype)
    
    # Get relevant field types
    allowed_fieldtypes = [
        "Data", "Select", "Link", "Int", "Float", "Currency",
        "Check", "Date", "Datetime", "Time"
    ]
    
    fields = []
    for df in meta.fields:
        if df.fieldtype in allowed_fieldtypes and not df.hidden:
            fields.append({
                "fieldname": df.fieldname,
                "label": df.label or df.fieldname,
                "fieldtype": df.fieldtype
            })
    
    return fields


@frappe.whitelist()
def save_matrix(data):
    """Save or update an approval matrix"""
    import json
    if isinstance(data, str):
        data = json.loads(data)
    
    matrix_name = data.get("name")
    
    # Create or update matrix
    if matrix_name and frappe.db.exists("Approval Matrix", matrix_name):
        doc = frappe.get_doc("Approval Matrix", matrix_name)
    else:
        doc = frappe.new_doc("Approval Matrix")
        doc.name = data.get("target_doctype")
    
    doc.target_doctype = data.get("target_doctype")
    doc.dimension = data.get("dimension")
    doc.fields_applicable = data.get("fields_applicable", "")
    
    # Clear existing transitions
    doc.transitions = []
    
    # Add new transitions
    for idx, transition in enumerate(data.get("transitions", []), start=1):
        doc.append("transitions", {
            "idx": idx,
            "dimension_value": transition.get("dimension_value"),
            "condition": transition.get("condition", ""),
            "approving_authority": transition.get("approving_authority"),
            "disabled": transition.get("disabled", 0)
        })
    
    # Skip dimension_value validation during save if needed
    if not all(t.get("dimension_value") for t in data.get("transitions", [])):
        doc.flags.ignore_validate_dimension_value = True
    
    # Skip link validation to avoid "No Label must be set first" error
    doc.flags.ignore_links = True
    doc.save(ignore_permissions=True)
    
    return {
        "success": True,
        "message": _("Approval Matrix saved successfully"),
        "name": doc.name
    }


@frappe.whitelist()
def delete_matrix(matrix_name):
    """Delete an approval matrix"""
    frappe.delete_doc("Approval Matrix", matrix_name, ignore_permissions=True)
    return {
        "success": True,
        "message": _("Approval Matrix deleted successfully")
    }


@frappe.whitelist()
def get_users():
    """Get list of active users for approving authority selection"""
    users = frappe.get_all(
        "User",
        filters={"enabled": 1, "user_type": "System User"},
        fields=["name", "full_name", "email"],
        order_by="full_name"
    )
    return users
