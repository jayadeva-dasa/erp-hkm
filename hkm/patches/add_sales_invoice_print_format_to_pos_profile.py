import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	"""
	Add custom field 'sales_invoice_print_format' to POS Profile
	for selecting print format when creating Sales Invoices from POS
	"""
	
	custom_fields = {
		"POS Profile": [
			{
				"fieldname": "sales_invoice_print_format",
				"label": "Sales Invoice Print Format",
				"fieldtype": "Link",
				"options": "Print Format",
				"insert_after": "print_format",
				"description": "Print format to use when creating Sales Invoices from POS (leave blank to use default)",
			}
		]
	}
	
	create_custom_fields(custom_fields, update=True)
	
	frappe.db.commit()
	print("✓ Added 'sales_invoice_print_format' custom field to POS Profile")
