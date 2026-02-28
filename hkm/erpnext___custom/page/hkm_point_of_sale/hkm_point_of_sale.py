# Copyright (c) 2025, HKM and Contributors
# License: GNU General Public License v3. See license.txt

"""
HKM Point of Sale - Backend wrapper for ERPNext v16
Reuses ERPNext POS business logic while serving a custom frontend
"""

import frappe
from frappe.query_builder import DocType, Order
from erpnext.selling.page.point_of_sale.point_of_sale import (
	check_opening_entry,
	create_opening_voucher,
	get_items,
	get_parent_item_group,
	get_past_order_list,
	item_group_query,
	set_customer_info,
)
from erpnext.stock.utils import scan_barcode

# Re-export all whitelisted methods for HKM POS frontend


@frappe.whitelist()
def hkm_get_items(start, page_length, price_list, item_group, pos_profile, search_term=""):
	"""Fetch items for HKM POS with GST-inclusive prices"""
	result = get_items(start, page_length, price_list, item_group, pos_profile, search_term)
	
	if result and result.get("items"):
		# Batch fetch all GST rates in one query to reduce DB calls
		item_codes = [item.get("item_code") for item in result["items"]]
		gst_rates = get_item_gst_rates_batch(item_codes)
		
		# Calculate selling price (base price + GST from Item Tax Template)
		for item in result["items"]:
			base_price = frappe.utils.flt(item.get("price_list_rate", 0))
			item_code = item.get("item_code")
			gst_rate = frappe.utils.flt(gst_rates.get(item_code, 0))
			
			# Calculate selling price: base_price + (base_price * gst_rate / 100)
			# Handle None/null values by converting to 0
			if gst_rate:
				item["selling_price"] = base_price * (1 + gst_rate / 100)
			else:
				item["selling_price"] = base_price
	
	return result


def get_item_gst_rates_batch(item_codes):
	"""
	Batch fetch GST rates for multiple items in a single query
	Returns dict: {item_code: gst_rate}
	"""
	if not item_codes:
		return {}
	
	try:
		# Single query to get all item tax templates and their GST rates
		# Uses JOIN to fetch both Item Tax and Item Tax Template data in one go
		result = frappe.db.sql("""
			SELECT 
				it.parent as item_code,
				itt.gst_rate
			FROM `tabItem Tax` it
			INNER JOIN `tabItem Tax Template` itt ON it.item_tax_template = itt.name
			WHERE it.parent IN %(item_codes)s
			ORDER BY it.idx ASC
		""", {"item_codes": item_codes}, as_dict=1)
		
		# Build dict with first (primary) tax template per item
		gst_rates = {}
		for row in result:
			if row.item_code not in gst_rates:
				gst_rates[row.item_code] = frappe.utils.flt(row.gst_rate or 0)
		
		return gst_rates
		
	except Exception as e:
		frappe.log_error(f"Error batch fetching GST rates: {str(e)}")
		return {}


@frappe.whitelist()
def hkm_search_serial_or_batch_or_barcode(search_value: str) -> dict[str, str | None]:
	"""Search by barcode/serial/batch - v16 compatible"""
	return scan_barcode(search_value)


@frappe.whitelist()
def hkm_get_parent_item_group(pos_profile):
	"""Get root item group for POS Profile - v16 compatible"""
	return get_parent_item_group(pos_profile)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def hkm_item_group_query(doctype, txt, searchfield, start, page_len, filters):
	"""Item group query for filters"""
	return item_group_query(doctype, txt, searchfield, start, page_len, filters)


@frappe.whitelist()
def hkm_check_opening_entry(user):
	"""Check if POS opening entry exists"""
	return check_opening_entry(user)


@frappe.whitelist()
def get_applicable_pos_profiles():
	"""
	Return list of POS Profile names the current user is allowed to use.
	Uses POS Profile's "Applicable for Users" child table:
	- If a profile has no users in Applicable for Users, it is shown to all.
	- If it has users, only those users see it.
	"""
	user = frappe.session.user
	if not user:
		return []

	# Profiles not disabled where current user is in applicable_for_users
	profiles_for_user = frappe.db.sql_list("""
		SELECT DISTINCT pf.name
		FROM `tabPOS Profile` pf
		INNER JOIN `tabPOS Profile User` pfu ON pfu.parent = pf.name
		WHERE pf.disabled = 0 AND pfu.user = %s
	""", (user,))

	# Profiles with no applicable_for_users rows (show to all users)
	profiles_no_restriction = frappe.db.sql_list("""
		SELECT pf.name
		FROM `tabPOS Profile` pf
		LEFT JOIN `tabPOS Profile User` pfu ON pfu.parent = pf.name
		WHERE pf.disabled = 0 AND pfu.parent IS NULL
	""")

	all_allowed = list(set(profiles_for_user) | set(profiles_no_restriction))
	return sorted(all_allowed)


@frappe.whitelist()
def hkm_create_opening_voucher(pos_profile, company, balance_details):
	"""Create POS opening voucher"""
	return create_opening_voucher(pos_profile, company, balance_details)


@frappe.whitelist()
def hkm_get_past_order_list(search_term, status, limit=20):
	"""Get past orders"""
	return get_past_order_list(search_term, status, limit)


@frappe.whitelist()
def hkm_set_customer_info(fieldname, customer, value=""):
	"""Update customer info"""
	return set_customer_info(fieldname, customer, value)


@frappe.whitelist()
def create_pos_invoice(customer, pos_profile, company, items, payment_amount, discount_amount=0):
	"""
	Create and submit Sales Invoice (from POS) with proper paid_amount and payment method from POS Profile
	"""
	import json
	from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_accounting_dimensions
	
	# Parse items if it's a string
	if isinstance(items, str):
		items = json.loads(items)
	
	# Get POS Profile with all accounting dimensions
	pos_profile_doc = frappe.get_cached_doc("POS Profile", pos_profile)
	default_mode_of_payment = "Cash"  # Fallback
	
	if pos_profile_doc.payments:
		# Get the first (default) payment method from POS Profile
		default_mode_of_payment = pos_profile_doc.payments[0].mode_of_payment
	
	# Create Sales Invoice document (not POS Invoice)
	doc = frappe.get_doc({
		"doctype": "Sales Invoice",
		"customer": customer,
		"pos_profile": pos_profile,
		"company": company,
		"posting_date": frappe.utils.today(),
		"posting_time": frappe.utils.nowtime(),
		"is_pos": 1,
		"is_created_using_pos": 1,  # Important: marks it as created from POS screen
		"items": items,
		"payments": [
			{
				"mode_of_payment": default_mode_of_payment,
				"amount": float(payment_amount) - float(discount_amount),
			}
		],
	})
	
	# Copy accounting dimensions from POS Profile to Sales Invoice
	dimensions = get_accounting_dimensions(as_list=True)
	for dimension in dimensions:
		dimension_value = pos_profile_doc.get(dimension)
		if dimension_value:
			doc.set(dimension, dimension_value)
			# Also set on each item
			for item in doc.items:
				item.set(dimension, dimension_value)
	
	# Apply discount if provided
	if float(discount_amount) > 0:
		doc.discount_amount = float(discount_amount)
		doc.apply_discount_on = "Grand Total"
	
	# Calculate totals before insert
	doc.run_method("set_missing_values")
	doc.run_method("calculate_taxes_and_totals")
	
	# Update payment amount to match grand_total (includes taxes)
	if doc.payments:
		doc.payments[0].amount = doc.rounded_total or doc.grand_total
	
	# Set paid_amount to match rounded_total
	doc.paid_amount = doc.rounded_total or doc.grand_total
	
	# Now insert the document with correct payment amount
	doc.insert(ignore_permissions=True)
	
	# Submit the document
	doc.submit()
	
	return doc


@frappe.whitelist()
def get_recent_pos_invoices(pos_profile, limit=20):
	"""
	Get recent Sales Invoices created from POS for a specific POS Profile - ONLY by current user
	"""
	invoices = frappe.get_all(
		"Sales Invoice",
		filters={
			"pos_profile": pos_profile,
			"owner": frappe.session.user,  # Only invoices created by current user
			"is_pos": 1,
			"is_created_using_pos": 1,  # Only POS-created Sales Invoices
			"docstatus": 1,
		},
		fields=["name", "customer", "customer_name", "posting_date", "posting_time", "grand_total", "currency"],
		order_by="posting_date desc, posting_time desc",
		limit=int(limit),
	)
	
	return invoices


@frappe.whitelist()
def cancel_pos_invoice(name: str):
	"""
	Cancel a Sales Invoice (created from POS) from Recent Orders dialog.
	Only allows the current user to cancel their own submitted Sales Invoices.
	"""
	if not name:
		frappe.throw("Missing invoice name")

	# Fetch minimal fields to validate
	inv = frappe.db.get_value(
		"Sales Invoice",
		name,
		["name", "owner", "docstatus", "status", "is_pos", "is_created_using_pos"],
		as_dict=True,
	)
	if not inv:
		frappe.throw("Sales Invoice not found")

	# Must be a POS-created invoice
	if not inv.is_pos or not inv.is_created_using_pos:
		frappe.throw("This is not a POS-created Sales Invoice")

	# Must belong to the current user
	if inv.owner != frappe.session.user:
		frappe.throw("You can cancel only your own Sales Invoices")

	# Must be submitted
	if inv.docstatus != 1:
		frappe.throw("Only submitted Sales Invoices can be cancelled")

	# Proceed to cancel
	doc = frappe.get_doc("Sales Invoice", name)
	doc.cancel()
	return {"name": name, "status": "Cancelled"}

@frappe.whitelist()
def calculate_taxes(pos_profile, customer, company, items):
	"""
	Calculate taxes for cart items based on POS Profile settings
	"""
	import json
	
	# Parse items if it's a string
	if isinstance(items, str):
		items = json.loads(items)
	
	# Create a temporary Sales Invoice document (not saved)
	doc = frappe.get_doc({
		"doctype": "Sales Invoice",
		"customer": customer,
		"pos_profile": pos_profile,
		"company": company,
		"posting_date": frappe.utils.today(),
		"posting_time": frappe.utils.nowtime(),
		"is_pos": 1,
		"is_created_using_pos": 1,
		"items": items,
	})
	
	# Calculate taxes without saving
	doc.run_method("set_missing_values")
	doc.run_method("calculate_taxes_and_totals")
	
	return {
		"total_taxes_and_charges": doc.total_taxes_and_charges,
		"grand_total": doc.grand_total,
		"rounded_total": doc.rounded_total,
	}


@frappe.whitelist()
def hkm_get_child_item_groups(parent: str):
	"""
	Return immediate child Item Groups for a given parent to populate nested filters.
	Includes both leaf and non-leaf groups.
	"""
	if not parent:
		return []
	children = frappe.get_all(
		"Item Group",
		filters={"parent_item_group": parent},
		fields=["name", "is_group"],
		order_by="lft asc",
	)
	return children


@frappe.whitelist()
def get_closing_data(pos_opening_entry):
	"""
	Get data for POS closing summary - Sales Invoices created from POS
	"""
	from frappe.utils.data import get_datetime
	
	# Use get_cached_doc for better performance
	opening = frappe.get_cached_doc("POS Opening Entry", pos_opening_entry)
	
	# Use parameterized query for safety and performance
	start_datetime = get_datetime(opening.period_start_date).strftime("%Y-%m-%d %H:%M:00")
	end_datetime = get_datetime(frappe.utils.now()).strftime("%Y-%m-%d %H:%M:59")
	
	# Get all Sales Invoices created from POS for this opening entry
	invoices = frappe.db.sql(
		"""
		SELECT name, grand_total,
			   CONVERT(CONCAT(posting_date, ' ', posting_time), DATETIME) as posting_datetime
		FROM `tabSales Invoice`
		WHERE
			docstatus = 1
			and is_pos = 1
			and is_created_using_pos = 1
			and pos_profile = %(pos_profile)s
			and owner = %(owner)s
		HAVING
			posting_datetime >= %(start_datetime)s
			and posting_datetime <= %(end_datetime)s
		""",
		{
			"pos_profile": opening.pos_profile,
			"owner": opening.user,
			"start_datetime": start_datetime,
			"end_datetime": end_datetime
		},
		as_dict=1,
	)
	
	total_sales = sum([inv.grand_total for inv in invoices])
	opening_amount = opening.balance_details[0].opening_amount if opening.balance_details else 0
	
	return {
		"opening_amount": opening_amount,
		"total_invoices": len(invoices),
		"total_sales": total_sales,
		"expected_amount": opening_amount + total_sales,
	}


@frappe.whitelist()
def create_closing_entry(pos_opening_entry, cash_collection=None):
	"""
	Create POS Closing Entry manually
	"""
	try:
		# Get the opening entry
		opening = frappe.get_doc("POS Opening Entry", pos_opening_entry)
		
		# Get current datetime for period end
		from frappe.utils.data import get_datetime
		current_datetime = frappe.utils.now()
		
		# Create closing entry document
		closing_entry = frappe.new_doc("POS Closing Entry")
		closing_entry.pos_opening_entry = opening.name
		closing_entry.period_start_date = opening.period_start_date
		closing_entry.period_end_date = get_datetime(current_datetime)
		closing_entry.posting_date = frappe.utils.nowdate()
		closing_entry.posting_time = frappe.utils.nowtime()
		closing_entry.user = opening.user
		closing_entry.pos_profile = opening.pos_profile
		closing_entry.company = opening.company

		# Set cash collection if provided
		if cash_collection is not None and cash_collection:
			frappe.logger().info(f"Setting cash_collection: {cash_collection}")
			closing_entry.cash_collection = float(cash_collection)
		
		# Get all Sales Invoices created from POS for this opening - ONLY by the same user
		# Use parameterized query for safety
		start_datetime = get_datetime(opening.period_start_date).strftime("%Y-%m-%d %H:%M:00")
		end_datetime = get_datetime(current_datetime).strftime("%Y-%m-%d %H:%M:59")
		
		invoices = frappe.db.sql(
			"""
			SELECT name, customer, grand_total, posting_date,
				CONVERT(CONCAT(posting_date, ' ', posting_time), DATETIME) as posting_datetime
			FROM `tabSales Invoice`
			WHERE
				docstatus = 1
				and is_pos = 1
				and is_created_using_pos = 1
				and pos_profile = %(pos_profile)s
				and owner = %(owner)s
			HAVING
				posting_datetime >= %(start_datetime)s
				and posting_datetime <= %(end_datetime)s
			ORDER BY posting_datetime
			""",
			{
				"pos_profile": opening.pos_profile,
				"owner": opening.user,
				"start_datetime": start_datetime,
				"end_datetime": end_datetime
			},
			as_dict=1,
		)
		
		# Add Sales Invoices to closing entry - use 'sales_invoices' child table
		for inv in invoices:
			closing_entry.append("sales_invoices", {
				"sales_invoice": inv.name,
				"posting_date": inv.posting_date,  # Required field
				"customer": inv.customer,
				"grand_total": inv.grand_total,
			})
		
		# Calculate payment reconciliation - from opening and/or invoice payments
		payment_totals = {}
		if invoices:
			invoice_names = [inv.name for inv in invoices]
			all_payments = frappe.db.sql(
				"""
				SELECT parent, mode_of_payment, amount, base_amount
				FROM `tabSales Invoice Payment`
				WHERE parent IN %(invoice_names)s AND parenttype = 'Sales Invoice'
				""",
				{"invoice_names": invoice_names},
				as_dict=1,
			)
			invoice_payments = {}
			for payment in all_payments:
				if payment.parent not in invoice_payments:
					invoice_payments[payment.parent] = []
				invoice_payments[payment.parent].append(payment)
			for inv in invoices:
				payments = invoice_payments.get(inv.name, [])
				if payments:
					total_payment_amount = sum([p.amount for p in payments])
					for payment in payments:
						mode = payment.mode_of_payment
						if mode not in payment_totals:
							payment_totals[mode] = 0
						if total_payment_amount > 0:
							proportion = payment.amount / total_payment_amount
							payment_totals[mode] += inv.grand_total * proportion
						else:
							payment_totals[mode] += inv.grand_total

		# Build payment reconciliation - from opening balance_details (with or without invoices)
		if opening.balance_details:
			for payment in opening.balance_details:
				mode = payment.mode_of_payment
				opening_amt = payment.opening_amount or 0
				collected_amt = payment_totals.get(mode, 0)
				expected_amt = opening_amt + collected_amt
				closing_entry.append("payment_reconciliation", {
					"mode_of_payment": mode,
					"opening_amount": opening_amt,
					"expected_amount": expected_amt,
					"closing_amount": expected_amt,
				})
		# Add any payment modes from invoices that weren't in opening
		for mode, amount in payment_totals.items():
			existing = [p.mode_of_payment for p in closing_entry.payment_reconciliation]
			if mode not in existing:
				closing_entry.append("payment_reconciliation", {
					"mode_of_payment": mode,
					"opening_amount": 0,
					"expected_amount": amount,
					"closing_amount": amount,
				})

		# Insert and submit - works for both with and without invoices
		closing_entry.insert()
		try:
			closing_entry.submit()
		except Exception as submit_error:
			try:
				opening_doc = frappe.get_doc("POS Opening Entry", opening.name)
				opening_doc.pos_closing_entry = None
				opening_doc.set_status()
				opening_doc.save()
			except Exception:
				pass
			raise submit_error

		return closing_entry
	except Exception as e:
		frappe.throw(f"Failed to create closing entry. {str(e)}")
