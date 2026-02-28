# Copyright (c) 2023, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class DDWalletTx(Document):
	def before_insert(self):
		existing_docs = frappe.get_all(self.doctype,filters = {"user":self.user},fields=['*'],order_by="creation desc")
		if len(existing_docs) == 0:
			self.final_balance = self.deposit
		else:
			last_tx = existing_docs[0]
			self.final_balance = last_tx.final_balance + (self.deposit or 0) - (self.withdrawl or 0)