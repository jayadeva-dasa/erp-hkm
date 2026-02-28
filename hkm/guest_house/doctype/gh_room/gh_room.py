# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class GHRoom(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		enabled: DF.Check
		floor: DF.Literal["0", "1", "2", "3", "4", "5", "6", "7", "8"]
		room_number: DF.Data
		room_type: DF.Link | None
	# end: auto-generated types

	pass
