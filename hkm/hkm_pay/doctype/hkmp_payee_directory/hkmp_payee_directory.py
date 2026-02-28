# Copyright (c) 2026, Narahari Dasa and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class HKMPPayeeDirectory(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		beneficiary: DF.Data | None
		beneficiary_vpa: DF.Data | None
		hkmp_user: DF.Link | None
		paid_amount: DF.Currency
		payment_date: DF.Date | None
	# end: auto-generated types
	pass
