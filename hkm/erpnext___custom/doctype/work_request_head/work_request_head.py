# Copyright (c) 2022, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class WorkRequestHead(Document):
	def save(self, *args, **kwargs):
		super().save(*args, **kwargs)
		self.update_mrn_status()
	def update_mrn_status(doc):
		completed =  0 if doc.status == "In Process" else 1
		mrns = frappe.get_all("Material Request",filters={ 'work_head': doc.name, 'docstatus':1 }, pluck="name")
		for mrn in mrns:
			frappe.db.set_value('Material Request', mrn, 'completed', completed)
