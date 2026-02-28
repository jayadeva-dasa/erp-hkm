# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class HKMAssetMovement(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		asset: DF.Link
		asset_category: DF.Link | None
		asset_name: DF.Data | None
		department: DF.Link | None
		from_location: DF.Data | None
		from_sub_custodian: DF.Link | None
		movement_date: DF.Date
		remarks: DF.SmallText | None
		to_location: DF.Data | None
		to_sub_custodian: DF.Link
	# end: auto-generated types
	
	def validate(self):
		self.validate_asset()
	
	def validate_asset(self):
		"""Check if asset is submitted and available for movement"""
		if self.asset:
			asset = frappe.get_doc("Asset", self.asset)
			
			
			if asset.status in ("Scrapped", "Sold", "Lost"):
				frappe.throw(_("Cannot move asset with status {0}").format(asset.status))
	
	
	
	