# Copyright (c) 2022, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import frappe.cache_manager
from frappe.utils import date_diff, getdate,today
from frappe import _

class MRNUsabilitySettings(Document):
	def validate(self):
		self.validate_duplicate()
		# self.validate_date()

	def validate_duplicate(self):
		documents = []
		for d in self.get("setting_documents"):
			if d.company in documents:
				frappe.throw("Row#{0} Duplicate record not allowed for {1}".format(d.idx, d.company))
				
			documents.append(d.company)
	
	def on_update(self):
		self.delete_mrn_settings_key()

	def on_trash(self):
		self.delete_mrn_settings_key()

	def delete_mrn_settings_key(self):
		companies = frappe.get_all("Company",pluck="name")
		for company in companies:
			frappe.cache().hdel("mrn_settings_key", company)
	
def get_company_mrn_settings(company):
	company_document = frappe.cache().hget("mrn_settings_key", company) or frappe._dict()
	if not company_document:
		if frappe.db.exists('MRN Usability Settings'):
			doc = frappe.get_cached_doc('MRN Usability Settings')
			if doc.enabled == 1:
				for d in doc.get("setting_documents"):
					if d.company == company:
						company_document = frappe._dict(
							duration_days = d.duration_days,
							allowed_user = d.allowed_user,
						)
						frappe.cache().hset("mrn_settings_key", company, company_document)
	return company_document

def validate_mrn_settings(doc,method):
	if not doc.stock_entry_type == "Material Issue":
		return
	mrns = []
	for row in doc.get("items"):
		mrn = row.material_request
		if mrn is not None and mrn not in mrns:
			mrns.append(mrn)
	
	for mrn in mrns:
		mrn_doc = frappe.get_doc("Material Request",mrn)
		transaction_date = mrn_doc.get("transaction_date") or doc.get("posting_date")
		company = mrn_doc.get("company")
		if transaction_date and company:
			company_mrn_settings = get_company_mrn_settings(company)
			if company_mrn_settings:
				days_allowed = company_mrn_settings.get('duration_days')
				allowed_users = [company_mrn_settings.get('allowed_user'), 'Administrator']
				if date_diff(today(), transaction_date) > days_allowed and frappe.session.user not in allowed_users:
					frappe.throw(_("<p class='text-danger'>You are not authorized to make Stock Issue Entry against this MRN (<a href = {0}>{1}</a>) because of <b> {2}</b> days restriction. </p>").format(frappe.utils.get_url_to_form(mrn_doc.doctype, mrn_doc.name),mrn,days_allowed))
	return
