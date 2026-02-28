# Copyright (c) 2023, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe,re
from frappe.model.document import Document

class SuspenseTool(Document):
	pass

@frappe.whitelist()
def update_suspense_clearing_jv():
	suspense_tool = frappe.get_doc("Suspense Tool")
	for jv in suspense_tool.jvs.splitlines():
		jv_doc = frappe.get_doc("Journal Entry",jv)
		suspense_jv = None
		for a in jv_doc.accounts:
			if re.search('suspense', a.account, re.IGNORECASE):
				suspense_jv = a
		frappe.db.set_value(
                        "Journal Entry Account",
                        suspense_jv.name,
                        {
                            'suspense_jv': suspense_tool.clearing_jv,
                        },
                        update_modified=False
                    )


