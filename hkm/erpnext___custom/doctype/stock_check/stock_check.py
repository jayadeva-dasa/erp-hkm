# Copyright (c) 2021, Narahari Das and contributors
# For license information, please see license.txt

import frappe
from erpnext.stock.utils import get_stock_balance
from frappe.model.mapper import get_mapped_doc
from frappe.model.document import Document

class StockCheck(Document):
	def before_save(self):
		for item in self.items:
			item.current_stock = get_stock_balance(item.item,self.warehouse)
			item.difference = item.audit_stock - item.current_stock

@frappe.whitelist()
def make_stock_reconcillation_entry(source_name, target_doc=None):
	
	def update_item(source, target, source_parent):
		target.warehouse = source_parent.warehouse

	doclist = get_mapped_doc("Stock Check", source_name, {
		"Stock Check": {
			"doctype": "Stock Reconciliation"
			# "validation": {
			# 	# "docstatus": ["=", 1],
			# 	# "material_request_type": ["=", "Purchase"]
			# }
			},
		"Stock Check Item": {
			"doctype": "Stock Reconciliation Item",
			"field_map": {
				"item": "item_code",
				"audit_stock": "qty",
				"warehouse":"warehouse"
			},
			"postprocess": update_item
			# "condition": select_item
		}
	}, target_doc)
	return doclist