# import frappe,requests,json,re

# @frappe.whitelist()
# def query(values):
# 	values = json.loads(values)
	
# 	frappe.db.delete('Item Price', {
# 				    'item_code': values['item_code'],
# 				    'price_list':values['type']
# 				})
# 	frappe.db.delete('Item Tax', {
# 				    'parent': values['item_code']
# 				})
	
# 	gstper = re.findall('[0-9]+', values['tax_template'])
# 	price_rate = values['price']/(1+gstper/100)

# 	doc = frappe.get_doc('Item', values['item_code'])
# 	doc.append("taxes", {
# 					    'doctype': 'Item Tax',
# 					    'item_tax_template': values['tax_template']
# 					})
# 	doc.save()

# 	doc = frappe.get_doc({
# 					    'doctype': 'Item Price',
# 					    'price_list': values['type'],
# 					    'item_code': values['item_code'],
# 					    'selling':1,
# 					    'price_list_rate':price_rate
# 					})
# 	doc.insert()

# 	return values