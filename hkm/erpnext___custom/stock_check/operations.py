import frappe,json
from erpnext.stock.utils import get_stock_balance


@frappe.whitelist(allow_guest=True)
def getItemDetails(code,stockCheckCode):
	frappe.response["error"] = True
	if not code:
		frappe.response["message"] = 'Please enter code'
		return
	if not stockCheckCode:
		frappe.response["message"] = 'Please enter Stock Check code'
		return
	if frappe.db.exists('Item', code) and frappe.db.exists('Stock Check', stockCheckCode):
		frappe.response["error"] = False
		frappe.response["message"] = "Exists"
		data = frappe.db.sql("""
			SELECT 
				`tabItem`.item_code,`tabItem`.item_name,`tabItem`.valuation_rate,
			    IF(STRCMP(`tabItem Tax`.`item_tax_template`,"")=1, 
			        ROUND(`tabItem Price`.`price_list_rate`+(`tabItem Price`.`price_list_rate`*CAST(RIGHT(`tabItem Tax`.`item_tax_template`,2) AS int)/100),2), 
			        ROUND(`tabItem Price`.`price_list_rate`)
			    ) as sale_price
			FROM `tabItem`
			LEFT JOIN `tabItem Tax` ON `tabItem Tax`.parent = `tabItem`.name
			LEFT JOIN `tabItem Price` ON `tabItem Price`.item_code=`tabItem`.item_code
			WHERE `tabItem`.name = '{}'
			""".format(code),as_dict=1);
		frappe.response["item"] = data[0]
		
		#Current Actual Stock
		stock_check_doc = frappe.get_doc('Stock Check',stockCheckCode)
		#frappe.get_doc('Stock Check','STCH-23324')
		frappe.response["actual_stock"] = get_stock_balance(code,stock_check_doc.warehouse)
		
		#Current Physical Stock
		frappe.response["physical_stock"] = 0 
		for item in stock_check_doc.items:
			if item.item == code:
				frappe.response["physical_stock"] = item.audit_stock
				break;
		return
	else:
		frappe.response["message"] = "Not Exists"
		return


@frappe.whitelist(allow_guest=True)
def addItemQty():
	data = json.loads(frappe.request.data)

	frappe.response["error"] = True
	if not data['itemCode']:
		frappe.response["message"] = 'Please enter code'
		return
	if not data['stockCheckCode']:
		frappe.response["message"] = 'Please enter Stock Check code'
		return
	if frappe.db.exists('Item', data['itemCode']) and frappe.db.exists('Stock Check', data['stockCheckCode']):
		stock_check_doc = frappe.get_doc('Stock Check',data['stockCheckCode'])
		if stock_check_doc.accept == False:
			frappe.response['message'] = "Not Accepting data"
			return

		frappe.response["error"] = False
		frappe.response["message"] = "Exists"

		itemExists = False

		for item in stock_check_doc.items:
			if item.item == data['itemCode']:
				itemExists = True
				item.audit_stock = item.audit_stock + data['qty']
				break;

		if itemExists == False:
			child = frappe.new_doc("Stock Check Item")
			child.update({
				'item':data['itemCode'],
				'audit_stock': data['qty'],
			    'parent': data['stockCheckCode'],
			    'parenttype': 'Stock Check',
			    'parentfield': 'items'
			})
			stock_check_doc.items.append(child)
		stock_check_doc.save(ignore_permissions=True, )
		return
	else:
		frappe.response["message"] = "Not Exists"
		return