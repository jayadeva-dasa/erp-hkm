# Copyright (c) 2022, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from hkm.ashram_issue_counter.utils import update_ashram_book_ledger_on_submit,update_ashram_book_ledger_on_cancel

class AshramLibraryBookInward(Document):
	def on_submit(self):
		update_ashram_book_ledger_on_submit(self)
		return
	def on_cancel(self):
		update_ashram_book_ledger_on_cancel(self)
		return
