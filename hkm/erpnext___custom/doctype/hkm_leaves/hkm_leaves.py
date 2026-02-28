# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class HKMLeaves(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		cl_opening_balance: DF.Float
		coff_opening_balance: DF.Float
		el_opening_balance: DF.Float
		employee: DF.Link | None
	# end: auto-generated types
	pass
