import frappe

@frappe.whitelist(allow_guest=True)
def checkCode(code):
	frappe.response["error"] = True
	if not code:
		frappe.response["message"] = 'Please enter code'
		return
	if frappe.db.exists('Stock Check', code):
		frappe.response["error"] = False
		frappe.response["message"] = "Exists"
		data = frappe.db.sql("""
			SELECT accept
			FROM `tabStock Check`
			WHERE name = '{}'
			""".format(code),as_dict=1);
		frappe.response["accept"] = data[0]['accept']
		#doc = frappe.get_doc('Stock Check', code)
		#frappe.response["doc"] = doc
		return
	else:
		frappe.response["message"] = "Not Exists"
		return