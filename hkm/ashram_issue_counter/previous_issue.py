import frappe

@frappe.whitelist()
def query(store_user):
	data = frappe.db.sql("""
					SELECT
						ASO.item,
						SUM(ASO.quantity)
					FROM 
						`tabAshram Store Item Issue` as ASI
					JOIN `tabAshram Store Outward Item` as ASO
						ON ASI.name = ASO.parent
					WHERE ASI.docstatus = 1
					AND ASI.issued_to = '{}'
					AND ASI.date > now() - INTERVAL 2 MONTH
					GROUP BY ASI.issued_to, ASO.item
					""".format(store_user), as_dict=0)
	return data
