# Copyright (c) 2026, Narahari Dasa and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class IndusIndBankIntegrationDetail(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		company: DF.Link | None
		encryption_key: DF.Password | None
		ibl_client_id: DF.Data | None
		ibl_client_password: DF.Password | None
		mcc: DF.Data | None
		merchant_id: DF.Data | None
		merchant_name: DF.Data | None
		merchant_vpa: DF.Data | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		payment_url: DF.Data | None
		transaction_status_url: DF.Data | None
	# end: auto-generated types
	pass
