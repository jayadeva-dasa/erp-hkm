"""
Approval Matrix Viewer - Backend API (Read-Only)
Allows users to view approval matrices by department/dimension
"""

import frappe
from frappe import _


@frappe.whitelist()
def get_all_matrices():
    """Get all approval matrices with their basic information"""
    matrices = frappe.get_all(
        "Approval Matrix",
        fields=["name", "target_doctype", "dimension", "fields_applicable"],
        order_by="target_doctype, dimension"
    )
    
    # Add transition count for each matrix
    for matrix in matrices:
        matrix["transition_count"] = frappe.db.count(
            "Approval Matrix Detail",
            {"parent": matrix.name, "disabled": 0}
        )
    
    return matrices


@frappe.whitelist()
def get_matrix_by_doctype_and_dimension(target_doctype, dimension):
    """Get matrix details for a specific doctype and dimension"""
    matrix_name = target_doctype  # Matrix name is usually the target_doctype
    
    if not frappe.db.exists("Approval Matrix", matrix_name):
        return None
    
    doc = frappe.get_doc("Approval Matrix", matrix_name)
    
    if doc.dimension != dimension:
        return None
    
    transitions = []
    for t in doc.transitions:
        if not t.disabled:
            # Get user full names for display
            approvers = []
            if t.approving_authority:
                for user_email in t.approving_authority.split('\n'):
                    user_email = user_email.strip()
                    if user_email:
                        user_full_name = frappe.db.get_value("User", user_email, "full_name") or user_email
                        approvers.append({
                            "email": user_email,
                            "full_name": user_full_name
                        })
            
            transitions.append({
                "idx": t.idx,
                "dimension_value": t.dimension_value or "Any Dimension",
                "condition": t.condition or "",
                "approving_authority": approvers
            })
    
    return {
        "name": doc.name,
        "target_doctype": doc.target_doctype,
        "dimension": doc.dimension,
        "fields_applicable": doc.fields_applicable or "",
        "transitions": transitions
    }


@frappe.whitelist()
def get_dimensions():
    """Get list of dimensions that have approval matrices configured"""
    # Get unique dimensions from all approval matrices
    matrices = frappe.get_all(
        "Approval Matrix",
        fields=["dimension"],
        order_by="dimension"
    )
    
    # Get unique dimensions
    unique_dimensions = list(set([m.dimension for m in matrices if m.dimension]))
    
    # Get dimension details
    dimensions = []
    for dim_name in unique_dimensions:
        dim_doc = frappe.db.get_value(
            "Accounting Dimension",
            dim_name,
            ["name", "label", "document_type"],
            as_dict=True
        )
        if dim_doc:
            dimensions.append(dim_doc)
    
    # Sort by name
    dimensions.sort(key=lambda x: x.get("name", ""))
    
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
def get_matrices_by_dimension_value(dimension, dimension_value):
    """Get all matrices that have rules for a specific dimension value"""
    # Find all matrices with this dimension
    matrices = frappe.get_all(
        "Approval Matrix",
        filters={"dimension": dimension},
        fields=["name", "target_doctype", "dimension", "fields_applicable"]
    )
    
    result = []
    for matrix in matrices:
        # Check if this matrix has rules for the given dimension value
        transitions = frappe.get_all(
            "Approval Matrix Detail",
            filters={
                "parent": matrix.name,
                "dimension_value": dimension_value,
                "disabled": 0
            },
            fields=["idx", "dimension_value", "condition", "approving_authority"],
            order_by="idx"
        )
        
        # Also check for "Any Dimension" rules
        any_dimension_transitions = frappe.get_all(
            "Approval Matrix Detail",
            filters={
                "parent": matrix.name,
                "dimension_value": ["in", ["", None]],
                "disabled": 0
            },
            fields=["idx", "dimension_value", "condition", "approving_authority"],
            order_by="idx"
        )
        
        all_transitions = transitions + any_dimension_transitions
        
        if all_transitions:
            # Get user full names for display
            for t in all_transitions:
                approvers = []
                if t.approving_authority:
                    for user_email in t.approving_authority.split('\n'):
                        user_email = user_email.strip()
                        if user_email:
                            user_full_name = frappe.db.get_value("User", user_email, "full_name") or user_email
                            approvers.append({
                                "email": user_email,
                                "full_name": user_full_name
                            })
                t["approvers"] = approvers
                t["dimension_value"] = t.dimension_value or "Any Dimension"
            
            result.append({
                "name": matrix.name,
                "target_doctype": matrix.target_doctype,
                "dimension": matrix.dimension,
                "fields_applicable": matrix.fields_applicable or "",
                "transitions": all_transitions
            })
    
    return result


@frappe.whitelist()
def get_doctypes_with_matrices():
    """Get list of doctypes that have approval matrices configured"""
    matrices = frappe.get_all(
        "Approval Matrix",
        fields=["target_doctype", "dimension"],
        order_by="target_doctype"
    )
    
    # Group by doctype
    doctype_map = {}
    for matrix in matrices:
        if matrix.target_doctype not in doctype_map:
            doctype_map[matrix.target_doctype] = []
        doctype_map[matrix.target_doctype].append(matrix.dimension)
    
    return doctype_map
