import frappe


@frappe.whitelist()
def check_ashraya(code):
	return code
