# -*- coding: utf-8 -*-
# Copyright (c) 2021, Tara Technologies
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import erpnext
from erpnext.controllers.queries import get_match_cond

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def uncleared_suspense_voucher_query(doctype, txt, searchfield, start, page_len, filters):
	if not filters: filters = {}
	condition = ""
	company = filters.get("company", "")
	if not company:
		return {}

	suspense_account = frappe.get_cached_value('Company', company, 'donation_suspense_account')
	condition += "and jv.company = %(company)s"

	return frappe.db.sql("""
		select jv.name, jv.posting_date, jv.uncleared_amount as amount, jv.cheque_no, jv.user_remark
		from `tabJournal Entry` jv 
		where jv.docstatus = 1
			and jv.uncleared_amount != 0
			and exists(select 1 from `tabJournal Entry Account` jva where jva.parent = jv.name and jva.account = '{suspense_account}')
			and (jv.{key} like %(txt)s
			or jv.cheque_no like %(txt)s
			or jv.user_remark like %(txt)s)
		{condition} {match_condition}
		order by
			if(locate(%(_txt)s, jv.name), locate(%(_txt)s, jv.name), 99999),
			if(locate(%(_txt)s, jv.cheque_no), locate(%(_txt)s, jv.cheque_no), 99999),
			if(locate(%(_txt)s, jv.user_remark), locate(%(_txt)s, jv.user_remark), 99999),			
			jv.idx desc,
			jv.name, jv.cheque_no, jv.user_remark
		limit %(start)s, %(page_len)s
		""".format(condition=condition, key=searchfield,
			suspense_account=suspense_account,			
			match_condition=get_match_cond(doctype)), {
			'company': company,
			"txt": "%%%s%%" % txt,
			"_txt": txt.replace("%", ""),
			"start": start,
			"page_len": page_len
		})	

