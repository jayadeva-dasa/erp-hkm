# Copyright (c) 2021, NRHD and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class FOLKCallingGroup(Document):
	pass

@frappe.whitelist()
def clear_all_members(group):
	students = frappe.db.get_list('FOLK Student',pluck='name', filters={'calling_group': group},)
	for s in students:
		frappe.db.set_value('FOLK Student', s, 'calling_group', None)
	return 1
