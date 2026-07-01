from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import flt
from erpnext.selling.doctype.sales_order.sales_order import SalesOrder


class HKMSalesOrder(SalesOrder):
	"""
	HKM Sales Order override.

	Adds a hard stock-availability check before submission so that a Sales
	Order cannot be submitted when the ordered quantity exceeds the actual
	stock available in the warehouse.

	The check is skipped when "Allow Negative Stock" is enabled in
	Stock Settings, keeping behaviour consistent with the rest of ERPNext.
	"""

	def before_submit(self):
		# Run the parent's before_submit first (if any)
		super().before_submit() if hasattr(super(), "before_submit") else None
		self.check_stock_availability_before_submit()

	def check_stock_availability_before_submit(self):
		"""
		Block submission if ordered qty exceeds available (actual) stock
		for any stock item.

		Skips:
		  - Items with no item_code or warehouse set
		  - Non-stock items
		  - Drop-ship items (delivered_by_supplier = 1)
		  - When 'Allow Negative Stock' is enabled globally
		"""
		if frappe.get_single_value("Stock Settings", "allow_negative_stock"):
			return

		insufficient_items = []

		for item in self.items:
			if not item.item_code or not item.warehouse:
				continue

			# Skip non-stock items
			if not frappe.get_cached_value("Item", item.item_code, "is_stock_item"):
				continue

			# Skip drop-ship items — stock is not consumed from our warehouse
			if item.delivered_by_supplier:
				continue

			actual_qty = flt(
				frappe.db.get_value(
					"Bin",
					{"item_code": item.item_code, "warehouse": item.warehouse},
					"actual_qty",
				)
				or 0
			)

			if flt(item.qty) > actual_qty:
				insufficient_items.append(
					_("Row #{0}: Item {1} — Ordered Qty: {2}, Available Stock in {3}: {4}").format(
						item.idx,
						frappe.bold(item.item_code),
						item.qty,
						item.warehouse,
						actual_qty,
					)
				)

		if insufficient_items:
			frappe.throw(
				_("Cannot submit Sales Order. Insufficient stock for the following items:")
				+ "<br><br>"
				+ "<br>".join(insufficient_items),
				title=_("Insufficient Stock"),
			)
