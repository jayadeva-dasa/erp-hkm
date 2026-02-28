"""
Migration patch to extract dimension values from existing approval matrix conditions
and populate the new dimension_value field.
"""

import frappe
import re


def execute():
    """
    Extract dimension values from conditions in Approval Matrix Detail
    and populate the new dimension_value field.
    """
    print("Starting migration: Extract dimension values from approval matrix conditions")
    
    # Check if the dimension_value column exists in the database
    if not frappe.db.has_column("Approval Matrix Detail", "dimension_value"):
        print("Column 'dimension_value' does not exist yet. Skipping migration.")
        print("This patch will run automatically after schema sync.")
        return
    
    # Get all approval matrices
    approval_matrices = frappe.get_all(
        "Approval Matrix",
        fields=["name", "dimension", "target_doctype"]
    )
    
    if not approval_matrices:
        print("No approval matrices found")
        return
    
    total_updated = 0
    total_failed = 0
    
    for matrix in approval_matrices:
        print(f"\nProcessing Approval Matrix: {matrix.name}")
        print(f"  Target DocType: {matrix.target_doctype}")
        print(f"  Dimension: {matrix.dimension}")
        
        # Get the dimension field name (scrubbed)
        dimension_fieldname = frappe.scrub(matrix.dimension)
        
        # Get all transitions for this matrix
        transitions = frappe.get_all(
            "Approval Matrix Detail",
            filters={"parent": matrix.name},
            fields=["name", "condition", "dimension_value", "idx"],
            order_by="idx asc"
        )
        
        print(f"  Found {len(transitions)} transitions")
        
        for transition in transitions:
            try:
                # Skip if dimension_value is already set
                if transition.dimension_value:
                    print(f"    Row {transition.idx}: dimension_value already set to '{transition.dimension_value}'")
                    continue
                
                condition = transition.condition or ""
                
                # Extract dimension value from condition
                dimension_value = extract_dimension_value(condition, dimension_fieldname)
                
                if dimension_value:
                    # Update the transition with extracted dimension value
                    frappe.db.set_value(
                        "Approval Matrix Detail",
                        transition.name,
                        "dimension_value",
                        dimension_value,
                        update_modified=False
                    )
                    
                    # Remove the dimension condition from the condition field
                    new_condition = remove_dimension_from_condition(condition, dimension_fieldname, dimension_value)
                    
                    frappe.db.set_value(
                        "Approval Matrix Detail",
                        transition.name,
                        "condition",
                        new_condition,
                        update_modified=False
                    )
                    
                    print(f"    Row {transition.idx}: Extracted '{dimension_value}' and updated condition")
                    total_updated += 1
                else:
                    print(f"    Row {transition.idx}: WARNING - Could not extract dimension value from condition")
                    print(f"      Condition: {condition}")
                    total_failed += 1
                    
            except Exception as e:
                print(f"    Row {transition.idx}: ERROR - {str(e)}")
                frappe.log_error(
                    f"Error processing Approval Matrix Detail {transition.name}: {str(e)}",
                    "Dimension Value Migration Error"
                )
                total_failed += 1
    
    frappe.db.commit()  # v16: OK - patch script
    
    print(f"\n{'='*60}")
    print(f"Migration completed:")
    print(f"  Total updated: {total_updated}")
    print(f"  Total failed: {total_failed}")
    print(f"{'='*60}")


def extract_dimension_value(condition, dimension_fieldname):
    """
    Extract the dimension value from a condition string.
    
    Examples:
        execution_department == 'House Keeping' and type == 'CAPEX'
        -> Returns: 'House Keeping'
        
        execution_department == "Vehicle" and type == 'REVEX'
        -> Returns: 'Vehicle'
    """
    if not condition:
        return None
    
    # Pattern to match: dimension_fieldname == 'value' or dimension_fieldname == "value"
    patterns = [
        rf"{dimension_fieldname}\s*==\s*['\"]([^'\"]+)['\"]",
        rf"{dimension_fieldname}\s*==\s*'([^']+)'",
        rf'{dimension_fieldname}\s*==\s*"([^"]+)"',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, condition)
        if match:
            return match.group(1)
    
    return None


def remove_dimension_from_condition(condition, dimension_fieldname, dimension_value):
    """
    Remove the dimension condition from the condition string.
    
    Examples:
        Input: execution_department == 'House Keeping' and type == 'CAPEX' and grand_total <=5000
        Output: type == 'CAPEX' and grand_total <=5000
    """
    if not condition:
        return ""
    
    # Patterns to remove
    patterns = [
        rf"{dimension_fieldname}\s*==\s*['\"]({re.escape(dimension_value)})['\"]",
        rf"{dimension_fieldname}\s*==\s*'({re.escape(dimension_value)})'",
        rf'{dimension_fieldname}\s*==\s*"({re.escape(dimension_value)})"',
    ]
    
    new_condition = condition
    
    for pattern in patterns:
        new_condition = re.sub(pattern, "", new_condition)
    
    # Clean up extra 'and' keywords
    new_condition = re.sub(r'\s+and\s+and\s+', ' and ', new_condition)
    new_condition = re.sub(r'^\s*and\s+', '', new_condition)  # Remove leading 'and'
    new_condition = re.sub(r'\s+and\s*$', '', new_condition)  # Remove trailing 'and'
    
    # Clean up extra spaces
    new_condition = re.sub(r'\s+', ' ', new_condition).strip()
    
    return new_condition
