# Copyright (c) 2022, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Dormitory(Document):
	def validate(self):
		self.validate_abbr()

	def validate_abbr(self):
		if not self.abbr:
			self.abbr = '-'.join(c[:2] for c in self.dormitory_name.split()).upper()

		self.abbr = self.abbr.strip()

		if not self.abbr.strip():
			frappe.throw(_("Abbreviation is mandatory"))

		if frappe.db.sql("select abbr from tabDormitory where name!=%s and abbr=%s", (self.name, self.abbr)):
			frappe.throw(_("Abbreviation already used for another Dormitory"))
