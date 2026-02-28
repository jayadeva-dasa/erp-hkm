# Copyright (c) 2024, Narahari Dasa and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class HKMPaymentRequestDetail(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amount: DF.Currency
		bank_account_name: DF.Data
		bank_account_number: DF.Data
		document_name: DF.DynamicLink | None
		document_type: DF.Literal["", "Purchase Invoice", "Purchase Order", "Journal Entry"]
		ifsc_code: DF.Data
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		reference_number: DF.Data | None
		supplier: DF.Link | None
		supplier_bank_account: DF.Link | None
	# end: auto-generated types
	pass
