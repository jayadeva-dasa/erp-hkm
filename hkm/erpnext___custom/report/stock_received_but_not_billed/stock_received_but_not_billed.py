# Copyright (c) 2022, Tara Technologies and contributors
# For license information, please see license.txt

import frappe
from erpnext.accounts.utils import get_company_default
from frappe import _, scrub
from frappe.utils import flt, cint

def execute(filters=None):
	data, summary = StockNotBilledReportGenerator(filters).get_data_with_summary()
	columns = get_columns(filters)
	return columns, data, None, None, summary

def get_columns(filters):
	columns = [
		{
		"fieldname": "transaction_date",
		"label" : _("Date"),
		"fieldtype": "Date",
		"width": "100",
		"hidden": 1
		},
		{
			"label": _("Voucher Type"),
			"fieldname": "against_voucher_type",
			"width": 120,
			"hidden": 1
		},
		{
			"label": _("Voucher No"),
			"fieldname": "against_voucher_no",
			"fieldtype": "Dynamic Link",
			"options": "against_voucher_type",
			"width": 180
		},
		{
		"fieldname": "supplier",
		"label" : _("Supplier"),
		"fieldtype": "Data",
		"width": 180,
		},	
		{
		"fieldname": "type",
		"label" : _("Type"),
		"fieldtype": "Data",
		"width": 70,
		},
		{
		"fieldname": "department",
		"label" : _("Department"),
		"fieldtype": "Data",
		"width": 150,
		},
		{
		"fieldname": "receipt",
		"label" : _("Receipt"),
		"fieldtype": "Currency",
		"options": "currency",		
		"width": 120,
		},	
		{
		"fieldname": "billed",
		"label" : _("Billed"),
		"fieldtype": "Currency",
		"options": "currency",		
		"width": 120,
		},
		{
		"fieldname": "difference",
		"label" : _("Difference"),
		"fieldtype": "Currency",
		"options": "currency",		
		"width": 120,
		},
	]
	columns.append({
		"fieldname": "currency",
		"label" : _("Currency"),
		"fieldtype": "Link",
		"options": "Currency",
		"hidden": 1
	})

	return columns	

class StockNotBilledReportGenerator(object):
	def __init__(self, filters=None):
		self.filters = frappe._dict(filters)
		if filters.get("company"):
			self.stock_not_billed_account = get_company_default(filters.get("company"), "stock_received_but_not_billed")

		self.show_difference = cint(self.filters.get("show_difference"))
		self.load_data()

	def load_data(self):
		self.load_gl_entries()
		self.load_purchase_receipt()		
		self.load_purchase_invoice()
		self.load_purchase_order()
		self.process_data()

	def process_data(self):
		self.data = []
		self.against_voucher_no = frappe._dict()

		self.other_voucher = []
		for d in self.gl_entries:
			against_voucher_no = d.voucher_no
			against_voucher_type = d.voucher_type

			if against_voucher_type == "Purchase Receipt" and self.receipt_po_map.get(d.voucher_no):
				against_voucher_no = self.receipt_po_map.get(d.voucher_no)
				against_voucher_type = 'Purchase Order'

			elif against_voucher_type == "Purchase Invoice" and self.invoice_po_map.get(d.voucher_no):
				against_voucher_no = self.invoice_po_map.get(d.voucher_no)
				against_voucher_type = 'Purchase Order'

			self.against_voucher_no.setdefault(against_voucher_no, frappe._dict(
					debit = 0,				
					credit = 0,
					against_voucher_type=against_voucher_type,
				))

			if flt(d.debit) > 0:
				self.against_voucher_no[against_voucher_no]["debit"] += flt(d.debit)
			else:
				self.against_voucher_no[against_voucher_no]["credit"] += flt(d.credit)

		for against_voucher_no, d in self.against_voucher_no.items():
			difference = flt(d.debit, 2) - flt(d.credit, 2)
			row = frappe._dict(
				against_voucher_no = against_voucher_no,
				against_voucher_type = d.against_voucher_type,
				receipt = d.credit,
				billed = d.debit,
				difference = difference,
			)	
			row.update(self.purchase_order_map.get(against_voucher_no, {}))			
			if self.show_difference:
				if difference != 0:
					self.data.append(row)
			else:
				self.data.append(row)

	def get_data(self):
		return self.data

	def get_data_with_summary(self):
		return self.data, self.get_report_summary()

	def load_gl_entries(self):
		fields = ["posting_date", "voucher_type", "voucher_no", "debit", "credit", "company"]
		filters = self.get_conditions()
		filters.extend([
				["is_cancelled", "=", 0], 
				["account", "=", self.stock_not_billed_account],
			])
		self.gl_entries = frappe.db.get_all("GL Entry", filters=filters, fields=fields, order_by="posting_date")

	def load_purchase_receipt(self):
		self.receipt_po_map = frappe._dict()
		self.purchase_receipts = []	

		purchase_receipts = [ d for d in self.gl_entries if d.voucher_type == 'Purchase Receipt']
		if not purchase_receipts:
			return self.receipt_po_map

		self.purchase_receipts = frappe.db.sql("""
			select purchase_order, parent as name
			from `tabPurchase Receipt Item`
			where parent in (%s)
			group by purchase_order, parent
			"""%
			', '.join(['%s']*len(purchase_receipts)), tuple([d.voucher_no for d in purchase_receipts]), as_dict=1)

		for d in self.purchase_receipts:
			if d.purchase_order:
				self.receipt_po_map.setdefault(d.name, d.purchase_order)

	def load_purchase_invoice(self):
		self.invoice_po_map = frappe._dict()	
		self.purchase_invoices = []

		purchase_invoices = [ d for d in self.gl_entries if d.voucher_type == 'Purchase Invoice']
		if not purchase_invoices:
			return self.invoice_po_map

		self.purchase_invoices = frappe.db.sql("""
			select purchase_order, parent as name
			from `tabPurchase Invoice Item`
			where parent in (%s)
			group by purchase_order, parent
			"""%
			', '.join(['%s']*len(purchase_invoices)), tuple([d.voucher_no for d in purchase_invoices]), as_dict=1)

		for d in self.purchase_invoices:
			if d.purchase_order:						
				self.invoice_po_map.setdefault(d.name, d.purchase_order)

	def load_purchase_order(self):
		self.purchase_order_map = frappe._dict()		
		purchase_orders = [d.purchase_order for d in self.purchase_receipts]
		purchase_orders.extend([d.purchase_order for d in self.purchase_invoices])
		purchase_orders = list(set(purchase_orders))
		if not purchase_orders:
			return self.purchase_order_map

		fields = ["name", "transaction_date", "type", "supplier", "department", "company"]
		filters = [["company", "=", self.filters.company]]
		filters.append(["name", "in", purchase_orders])

		for d in frappe.db.get_all("Purchase Order", filters=filters, fields=fields):
			self.purchase_order_map.setdefault(d.name, d)


	def get_conditions(self, is_list=True):
		conditions = []

		if self.filters.get("from_date"):
			conditions.append(["posting_date", ">=", self.filters.from_date])

		if self.filters.get("to_date"):
			conditions.append(["posting_date", "<=", self.filters.to_date])		

		if self.filters.get("company"):
			conditions.append(["company", "=", self.filters.company])

		if is_list:
			return conditions	
		else:
			return "and {}".format(" and ".join(conditions)) if conditions else ""

	def get_report_summary(self):
		summary = frappe._dict(
			total_receipt = 0,
			total_billed = 0,
			difference = 0,
		)
		for d in self.data:
			summary["total_receipt"] += flt(d.receipt, 2)
			summary["total_billed"] += flt(d.billed, 2)
			summary["difference"] += flt(d.difference, 2)	

		return [
			dict(
				label="Total Billed", 
				value= summary.total_billed, 
				indicator="Green",
				datatype= "Currency",
			),
			{ "type": "separator", "value": "-"},
			dict(
				label="Total Receipt", 
				value= summary.total_receipt, 
				indicator="Blue",
				datatype= "Currency",
			),			
			{ "type": "separator", "value": "="},
			dict(
				label="Difference", 
				value= summary.difference, 
				indicator="Orange",
				datatype= "Currency",
			),				
		]			
