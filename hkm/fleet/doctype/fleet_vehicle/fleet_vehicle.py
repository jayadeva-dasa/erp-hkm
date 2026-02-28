# Copyright (c) 2021, NRHD and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class FleetVehicle(Document):

	@frappe.whitelist()
	def get_last_odometer(self):
		return None