"""
Update POS Settings on all sites to create Sales Invoice
Run: bench --site all execute hkm.cursor.update_all_sites_pos_settings.update_pos_settings
"""
import frappe


def update_pos_settings():
	"""Update POS Settings to set invoice_type to 'Sales Invoice'"""
	
	site_name = frappe.local.site
	
	try:
		# Get the POS Settings single doctype
		pos_settings = frappe.get_single("POS Settings")
		
		# Check current setting
		current_type = pos_settings.invoice_type
		
		# Update to Sales Invoice if not already set
		if current_type != "Sales Invoice":
			pos_settings.invoice_type = "Sales Invoice"
			pos_settings.save(ignore_permissions=True)
			frappe.db.commit()
			print(f"[{site_name}] ✓ Updated: '{current_type}' → 'Sales Invoice'")
			return f"[{site_name}] Updated to Sales Invoice"
		else:
			print(f"[{site_name}] ✓ Already set to 'Sales Invoice'")
			return f"[{site_name}] Already set to Sales Invoice"
		
	except Exception as e:
		print(f"[{site_name}] ✗ Error: {str(e)}")
		frappe.db.rollback()
		return f"[{site_name}] Error: {str(e)}"
