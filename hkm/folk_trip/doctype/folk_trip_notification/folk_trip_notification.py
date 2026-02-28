# Copyright (c) 2022, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class FOLKTripNotification(Document):
	def on_change(self):
		data = frappe.db.sql("""
			select fty.name
			from `tabFOLK Trip Yatri` fty
			join `tabFOLK Trip Train Passenger` fttp on (fttp.allocated_to = fty.name)
			join `tabFOLK Trip Train Ticket` fttt on (fttt.name = fttp.parent)
			where fttt.train = '{}' 
			""".format(self.train),as_dict = 0)
		self.total = len(data)
		return