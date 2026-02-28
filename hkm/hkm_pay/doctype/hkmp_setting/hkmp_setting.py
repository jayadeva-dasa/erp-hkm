# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class HKMPSetting(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from hkm.hkm_pay.doctype.hkmp_bank_settings.hkmp_bank_settings import HKMPBankSettings

		bank_settings: DF.Table[HKMPBankSettings]
		enable_period_restriction_for_bill_submission: DF.Check
		firebase_admin_app: DF.Link
		primary_bank: DF.Link
	# end: auto-generated types
	pass
