# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class HKMExpenseVoucherType(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from hkm.erpnext___custom.doctype.hkm_expense_voucher_type_account.hkm_expense_voucher_type_account import HKMExpenseVoucherTypeAccount

		defaults: DF.Table[HKMExpenseVoucherTypeAccount]
		volunteer_head: DF.Link | None
		voucher_type: DF.Data | None
	# end: auto-generated types
	pass
