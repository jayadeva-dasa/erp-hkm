# Copyright (c) 2025, HKM and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class RTLDepartment(Document):
	def validate(self):
		"""Validate department data."""
		self.validate_hod_not_in_members()
		self.validate_unique_members()

	def validate_hod_not_in_members(self):
		"""Ensure HOD is not listed as a regular member."""
		if self.head_of_department:
			for member in self.department_members:
				if member.user == self.head_of_department:
					frappe.throw(f"Head of Department {self.head_of_department} cannot be listed as a regular member.")

	def validate_unique_members(self):
		"""Ensure no duplicate members."""
		seen = set()
		for member in self.department_members:
			if member.user in seen:
				frappe.throw(f"User {member.user} is listed multiple times in department members.")
			seen.add(member.user)
