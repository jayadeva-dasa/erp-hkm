# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class AUBankIntegrationDetail(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		access_token: DF.Password | None
		account_number: DF.Data | None
		auth_url: DF.Data | None
		client_id: DF.Password | None
		client_secret: DF.Password | None
		company: DF.Link | None
		iv: DF.Password | None
		merchant__name: DF.Data | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		secret_key: DF.Password | None
		transaction_status_url: DF.Data | None
		upi_payout_url: DF.Data | None
		verify_vpa_url: DF.Data | None
		vpa: DF.Data | None
	# end: auto-generated types
	pass
