# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class QZPrinter(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		company: DF.Link | None
		date: DF.Date | None
		day_after_expiry: DF.Int
		general_item_code: DF.Link | None
		general_print_date: DF.Date | None
		general_print_quantity: DF.Int
		item_code: DF.Link | None
		manufacturing_date: DF.Date | None
		old_stock_item_code: DF.Link | None
		old_stock_print_quantity: DF.Int
		price_list: DF.Link | None
		printer_name: DF.Data | None
		quantity: DF.Int
		quantity_date: DF.Int
		quantity_exp: DF.Int
	# end: auto-generated types
	def autoname (self):
		if self.printer_name :
			self.name = self.printer_name
		if self.item_code :
				self.name = self.item_code
    