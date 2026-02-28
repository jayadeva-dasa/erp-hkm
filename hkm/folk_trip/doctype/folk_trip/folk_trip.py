# Copyright (c) 2022, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class FOLKTrip(Document):
	def validate(self):
		self.validate_participant_duplicacy()

	def validate_participant_duplicacy(self):
		participants = [pts.participant for pts in self.participants]
		list_participants = set(participants)
		unique_participants = (list(list_participants))
		if len(unique_participants) != len(participants):
			frappe.throw("Participants are duplicated. Please Check.")
		return
