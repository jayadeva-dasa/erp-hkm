# -*- coding: utf-8 -*-
# Copyright (c) 2021, NRHD and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
# import frappe
from frappe.model.document import Document

class FOLKResidency(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from hkm.folk_base.doctype.folk_residency_guide.folk_residency_guide import FOLKResidencyGuide

		address_line_1: DF.Data
		address_line_2: DF.Data | None
		amended_from: DF.Link | None
		city: DF.Data | None
		disabled: DF.Check
		guides: DF.Table[FOLKResidencyGuide]
		pin_code: DF.Data | None
		residency_title: DF.Data
	# end: auto-generated types
	pass
