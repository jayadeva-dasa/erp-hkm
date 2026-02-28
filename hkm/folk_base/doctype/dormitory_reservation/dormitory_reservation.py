# Copyright (c) 2022, Narahari Dasa and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext.controllers.queries import get_match_cond
from frappe.utils import getdate

class DormitoryReservation(Document):
	def update_checkout_date(self, checkout_date=None):
		pass

def update_checkout_date(checkout_date):
	pass
	
@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def dormitory_bed_query(doctype, txt, searchfield, start, page_len, filters):
	if not filters: filters = {}

	condition = ""
	if filters.get("dormitory"):
		condition = " and dormitory = %(dormitory)s"

	if filters.get("bed_type"):
		condition += " and bed_type = %(bed_type)s"

	sub_condition = """ and (res.checkin between %(checkin)s and %(checkout)s
					or res.actual_checkout between %(checkin)s and %(checkout)s
					or res.expected_checkout between %(checkin)s and %(checkout)s
					)"""
	return frappe.db.sql("""
		select name, dormitory, bed, bed_type
		from `tabDormitory Bed`
		where disabled = 0
		and not exists(
			select 1 
			from `tabDormitory Reservation` res
			where res.docstatus < 2
			and res.dormitory = `tabDormitory Bed`.dormitory
			and res.dormitory_bed = `tabDormitory Bed`.name
			{sub_condition}
		)
		and (
			name like %(txt)s
			or bed_type like %(txt)s
			or bed like %(txt)s
		)
		{condition} {match_condition}
		order by
			if(locate(%(_txt)s, bed), locate(%(_txt)s, bed), 99999),
			name
		limit %(start)s, %(page_len)s
		""".format(condition=condition, sub_condition=sub_condition, key=searchfield,
			match_condition=get_match_cond(doctype)), {
			'dormitory': filters.get("dormitory"),
			'checkin': filters.get("checkin") or getdate(),
			'checkout': filters.get("checkout") or getdate(),
			'bed_type': filters.get("bed_type"),
			"txt": "%%%s%%" % txt,
			"_txt": txt.replace("%", ""),
			"start": start,
			"page_len": page_len
		})			
