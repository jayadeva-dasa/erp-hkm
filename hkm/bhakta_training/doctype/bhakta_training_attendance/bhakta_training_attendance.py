# Copyright (c) 2022, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class BhaktaTrainingAttendance(Document):
	def validate(self):
		self.validate_duplication()

	def validate_duplication(self):
		"""Check if the Attendance Record is Unique"""
		attendance_record = None
		
		attendance_record = frappe.db.exists('Bhakta Training Attendance', {
			'bhakta': self.bhakta,
			'session': self.session,
			'status': self.status,
			'docstatus': ('!=', 2),
			'name': ('!=', self.name)
		})

		if attendance_record:
			record = get_link_to_form('Bhakta Training Attendance', attendance_record)
			frappe.throw(_('Bhakta Training Attendance record {0} already exists against the Bhakta {1}')
				.format(record, frappe.bold(self.bhakta)), title=_('Duplicate Entry'))
