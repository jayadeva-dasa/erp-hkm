# Copyright (c) 2022, Tara Technologies and Contributors
# License: GNU General Public License v3. See license.txt


import json

import frappe
from frappe import _
from frappe.utils import cint, flt

def validate_expense_account_for_non_stock_item(doc, method=None):
	if doc.doctype == "Stock Entry" and doc.stock_entry_type != "Material Issue":
		return

	item_map = frappe._dict()
	stock_not_billed_account, default_expense_account = frappe.get_cached_value('Company', doc.company, ['stock_received_but_not_billed', 'default_expense_account'])
	invalid_non_stock_items = []
	filters = {
		'disabled':0, 
		'is_stock_item':0,
		'is_fixed_asset': 0,
		'name': ['in', [d.item_code for d in doc.get("items")]]
		}

	for d in frappe.get_all('Item', filters=filters, fields=['name']):
		item_map.setdefault(d.name, d)

	for d in doc.get("items"):
		if item_map.get(d.item_code, None) and (
				d.expense_account == stock_not_billed_account
				or d.expense_account == default_expense_account
			):
			invalid_non_stock_items.append(d)

	if invalid_non_stock_items:
		for d in invalid_non_stock_items:
			frappe.msgprint(
				_('Row #{0}: Expense Account {1} is not allowed for non-stock item {2} : {3}.')
				.format(
					d.idx,
					frappe.bold(d.expense_account),
					frappe.bold(d.item_code),
					frappe.bold(d.item_name)
				)
			)
		frappe.throw(_("<b class='text-danger'>Please select correct expense account.</b>"), title=_("Invalid Expense Account"))

def validate_gst_entry(doc, method=None):
	blocked_gst_settings = frappe.get_single('Block GST Entry Settings')
	if not cint(blocked_gst_settings.get("enabled")):
		return

	doctype = doc.doctype
	company = doc.company
	department = doc.get("department")
	is_blocked = False

	block_input_gst = block_output_gst = 0
	for d in blocked_gst_settings.get("entries"):
		if d.company == company and d.department and d.department == department:
			block_input_gst = cint(d.block_input_gst)
			block_output_gst = cint(d.block_output_gst)
			break
		elif d.company == company and not d.department:
			block_input_gst = cint(d.block_input_gst)
			block_output_gst = cint(d.block_output_gst)
			break

	invalid_entries = []
	gst_accounts = get_gst_accounts(company)

	if not gst_accounts:
		return

	def add_invalid_entries(entry):
		invalid_entries.append(frappe._dict(
			idx = entry.get("idx"),
			account = entry.get('account') or entry.get("account_head")
		))

	def validate_blocked_gst_entry():
		if block_input_gst and doctype in ["Purchase Order", "Purchase Invoice"]:
			for tax in doc.get('taxes'):
				if tax.account_head in gst_accounts:
					add_invalid_entries(tax)

		elif block_output_gst and doctype in ["POS Invoice", "Sales Invoice"]:
			for tax in doc.get('taxes'):
				if tax.account_head in gst_accounts:
					add_invalid_entries(tax)

		elif (block_input_gst or block_output_gst) and doctype == "Journal Entry":
			for entry in doc.get("accounts"):
				if entry.account in gst_accounts:
					if block_input_gst and flt(entry.credit) > 0:
						add_invalid_entries(entry)
					elif block_output_gst and flt(entry.debit) > 0:
						add_invalid_entries(entry)

	def validate_unblocked_gst_entry():
		if block_input_gst and doctype in ["POS Invoice", "Sales Invoice"]:
			for tax in doc.get('taxes'):
				if tax.account_head not in gst_accounts:
					add_invalid_entries(tax)

	if not block_input_gst and not block_output_gst:
		return
		#validate_unblocked_gst_entry() # For future implementation
	else:
		is_blocked = True
		validate_blocked_gst_entry()

	if invalid_entries:
		message = "GST Entry {0} under Company : {1}".format("is not allowed" if is_blocked else "required", company)
		if department:
			message += " for Deparment : {0}".format(department)

		for entry in invalid_entries:
			frappe.msgprint("Row #{0}: Account {1}.".format(entry.idx, entry.account))

		frappe.throw(_("<b class='text-danger'>{0}.</b>"
			.format(message)),
			title=_("{0} GST Entry".format("Blocked" if is_blocked else "Required"))
			)


def get_gst_accounts(company):
	account_list = []
	gst_accounts = [d for d in frappe.get_single('GST Settings').get("gst_accounts") if d.company == company]
	for account in gst_accounts:
		for fieldname in ['cgst_account', 'sgst_account', 'igst_account', 'cess_account']:
			if account.get(fieldname):
				account_list.append(account.get(fieldname))	

	return account_list
