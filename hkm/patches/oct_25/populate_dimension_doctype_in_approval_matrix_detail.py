import frappe

def execute():
	"""
	Populate dimension_doctype field in Approval Matrix Detail child table.
	This field is required for the Dynamic Link (dimension_value) to work properly.
	It fetches the dimension from the parent Approval Matrix document.
	"""
	frappe.reload_doc("erpnext___custom", "doctype", "approval_matrix_detail")
	frappe.reload_doc("erpnext___custom", "doctype", "approval_matrix")
	
	# Get all Approval Matrix documents
	matrices = frappe.get_all("Approval Matrix", fields=["name", "dimension"])
	
	for matrix in matrices:
		if not matrix.dimension:
			continue
			
		# Update all child records with the parent's dimension
		frappe.db.sql("""
			UPDATE `tabApproval Matrix Detail`
			SET dimension_doctype = %s
			WHERE parent = %s
		""", (matrix.dimension, matrix.name))
		
		frappe.db.commit()  # v16: OK - patch script
	
	print(f"Updated dimension_doctype for {len(matrices)} Approval Matrix documents")
