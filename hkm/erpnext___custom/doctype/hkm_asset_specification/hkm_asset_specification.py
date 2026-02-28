# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class HKMAssetSpecification(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		asset_category: DF.Link
		data_type: DF.Literal["Text", "Number", "Select", "Date", "Checkbox"]
		description: DF.Text | None
		is_mandatory: DF.Check
		options: DF.SmallText | None
		specification_name: DF.Data
	# end: auto-generated types
	
	def validate(self):
		if self.data_type == "Select" and not self.options:
			frappe.throw("Options are required for Select data type")

