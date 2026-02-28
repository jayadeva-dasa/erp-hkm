# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class HKMAssetSpecificationValue(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		data_type: DF.Literal["Text", "Number", "Select", "Date", "Checkbox"]
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		specification: DF.Link | None
		specification_name: DF.Data | None
		value: DF.Data | None
	# end: auto-generated types
	pass

