"""
Update POS Profile to set Sales Invoice Print Formats
Run: bench execute hkm.cursor.update_pos_profile_print_formats.update_pos_profiles
"""
import frappe


def update_pos_profiles():
	"""Update all POS Profiles to use Sales Invoice print formats"""
	
	# Mapping of standard print formats to new Sales Invoice print formats
	format_mapping = {
		"POS GST Invoice": "HKM - Sales Invoice GST",
		"POS Non-GST Invoice": "HKM - Sales Invoice Non-GST",
		"POS Restaurant Invoice": "HKM - Sales Invoice Restaurant",
		"HKM - POS Invoice GST": "HKM - Sales Invoice GST",
		"HKM - POS Invoice Non GST": "HKM - Sales Invoice Non-GST",
		"HKM - POS Invoice Restaurant": "HKM - Sales Invoice Restaurant",
	}
	
	pos_profiles = frappe.get_all("POS Profile", fields=["name", "print_format", "sales_invoice_print_format"])
	
	updated_count = 0
	for profile in pos_profiles:
		old_format = profile.get("print_format")
		current_si_format = profile.get("sales_invoice_print_format")
		
		# Check if the old format is in our mapping and sales_invoice_print_format is not already set
		if old_format in format_mapping and not current_si_format:
			new_format = format_mapping[old_format]
			
			# Update the POS Profile
			pos_profile_doc = frappe.get_doc("POS Profile", profile.name)
			pos_profile_doc.sales_invoice_print_format = new_format
			pos_profile_doc.save(ignore_permissions=True)
			
			updated_count += 1
			print(f"✓ Updated POS Profile: {profile.name}")
			print(f"  Old format: {old_format}")
			print(f"  New Sales Invoice format: {new_format}")
		elif current_si_format:
			print(f"⊘ Skipped POS Profile: {profile.name} (already has {current_si_format})")
	
	frappe.db.commit()
	print(f"\n✓ Updated {updated_count} POS Profile(s)")
	return f"Updated {updated_count} POS Profile(s)"
