"""
Migration patch to remove dimension field from 'Fields Applicable' in Approval Matrix.
Since dimension is already specified separately, it should not be part of fields_applicable.
"""

import frappe


def execute():
    """
    Remove dimension field from fields_applicable in all Approval Matrix records.
    Fields Applicable should only contain additional fields used in conditions,
    not the dimension field itself.
    """
    print("Starting migration: Cleanup Fields Applicable in Approval Matrix")
    
    # Get all approval matrices
    approval_matrices = frappe.get_all(
        "Approval Matrix",
        fields=["name", "dimension", "fields_applicable"]
    )
    
    if not approval_matrices:
        print("No approval matrices found")
        return
    
    total_updated = 0
    
    for matrix in approval_matrices:
        print(f"\nProcessing Approval Matrix: {matrix.name}")
        print(f"  Dimension: {matrix.dimension}")
        print(f"  Current Fields Applicable: {matrix.fields_applicable}")
        
        if not matrix.fields_applicable:
            print("  No fields_applicable set, skipping")
            continue
        
        # Get the dimension field name (scrubbed)
        dimension_fieldname = frappe.scrub(matrix.dimension)
        
        # Parse the fields_applicable (comma-separated)
        fields_list = [f.strip() for f in matrix.fields_applicable.split(',')]
        
        # Remove the dimension field if present
        original_count = len(fields_list)
        fields_list = [f for f in fields_list if f != dimension_fieldname]
        
        if len(fields_list) < original_count:
            # Dimension field was removed
            new_fields_applicable = ', '.join(fields_list)
            
            frappe.db.set_value(
                "Approval Matrix",
                matrix.name,
                "fields_applicable",
                new_fields_applicable,
                update_modified=False
            )
            
            print(f"  ✓ Updated Fields Applicable: {new_fields_applicable}")
            print(f"  Removed: {dimension_fieldname}")
            total_updated += 1
        else:
            print(f"  No change needed (dimension field not in fields_applicable)")
    
    frappe.db.commit()  # v16: OK - patch script
    
    print(f"\n{'='*60}")
    print(f"Migration completed:")
    print(f"  Total updated: {total_updated}")
    print(f"{'='*60}")
