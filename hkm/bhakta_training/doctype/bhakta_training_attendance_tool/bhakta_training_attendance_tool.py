# Copyright (c) 2022, Narahari Dasa and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document

class BhaktaTrainingAttendanceTool(Document):
	pass

@frappe.whitelist()
def get_bhaktas_records(session):
	session = frappe.get_doc("Bhakta Training Session", session)
	bhaktas = frappe.db.sql("""
				select * 
				from `tabBhakta`
				where sem = '{}' 
					""".format(session.semester),as_dict = 1)
	return bhaktas