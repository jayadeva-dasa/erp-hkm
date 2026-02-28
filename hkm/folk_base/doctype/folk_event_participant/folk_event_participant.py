# Copyright (c) 2023, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class FOLKEventParticipant(Document):
	def on_payment_authorized(self,status=None):
		if not status:
			return
		self.db_set('paid', 1)
