import frappe
from frappe.model.document import Document
from frappe.utils import getdate


class RTLLeaves(Document):
	def validate(self):
		self.validate_dates()
		self.check_duplicate_leaves()

	def validate_dates(self):
		"""Validate that To Date is not earlier than From Date"""
		if self.from_date and self.to_date:
			if getdate(self.to_date) < getdate(self.from_date):
				frappe.throw("To Date cannot be earlier than From Date")

	def check_duplicate_leaves(self):
		"""Check for overlapping leave dates for the same employee"""
		if self.from_date and self.to_date:
			overlapping_leaves = frappe.db.sql("""
				SELECT name, from_date, to_date
				FROM `tabRTL Leaves`
				WHERE employee = %s
				AND name != %s
				AND (
					(from_date BETWEEN %s AND %s) OR
					(to_date BETWEEN %s AND %s) OR
					(%s BETWEEN from_date AND to_date) OR
					(%s BETWEEN from_date AND to_date)
				)
			""", (self.employee, self.name, self.from_date, self.to_date,
				  self.from_date, self.to_date, self.from_date, self.to_date))

			if overlapping_leaves:
				frappe.throw(f"There are overlapping leaves for this employee: {overlapping_leaves[0][0]}")
