# Copyright (c) 2022, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class DormitoryBed(Document):
	def autoname(self):
		self.validate_abbr()
		self.name = self.abbr

	def validate(self):
		self.validate_abbr()

	def validate_abbr(self):
		if not self.abbr and self.dormitory_abbr and self.bed:
			self.abbr = "{0}-{1}".format(self.dormitory_abbr, self.bed)

		self.abbr = self.abbr.strip()

		if not self.abbr.strip():
			frappe.throw(_("Abbreviation is mandatory"))

		if frappe.db.sql("select abbr from `tabDormitory Bed` where name!=%s and abbr=%s", (self.name, self.abbr)):
			frappe.throw(_("Abbreviation already used for another Dormitory Bed"))

