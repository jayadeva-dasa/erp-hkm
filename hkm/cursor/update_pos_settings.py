"""
Update POS Settings to create Sales Invoice instead of POS Invoice
Run: bench execute hkm.cursor.update_pos_settings.update_pos_settings
"""
import frappe


def update_pos_settings():
	"""Update POS Settings to set invoice_type to 'Sales Invoice'"""
	
	try:
		# Get the POS Settings single doctype
		pos_settings = frappe.get_single("POS Settings")
		
		# Check current setting
		current_type = pos_settings.invoice_type
		print(f"Current invoice type: {current_type}")
		
		# Update to Sales Invoice
		pos_settings.invoice_type = "Sales Invoice"
		pos_settings.save(ignore_permissions=True)
		
		frappe.db.commit()
		
		print(f"✓ Updated POS Settings: invoice_type changed from '{current_type}' to 'Sales Invoice'")
		return f"Updated POS Settings to use Sales Invoice"
		
	except Exception as e:
		print(f"✗ Error updating POS Settings: {str(e)}")
		frappe.db.rollback()
		return f"Error: {str(e)}"
