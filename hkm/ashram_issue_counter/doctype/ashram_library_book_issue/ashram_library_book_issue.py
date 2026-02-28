# Copyright (c) 2022, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from hkm.ashram_issue_counter.utils import issue_update_ashram_book_ledger_on_submit,issue_update_ashram_book_ledger_on_cancel

class AshramLibraryBookIssue(Document):
	def on_submit(self):
		issue_update_ashram_book_ledger_on_submit(self)
		return
	def on_cancel(self):
		issue_update_ashram_book_ledger_on_cancel(self)
		return
	def validate(self):
		self.check_availability()
		return

	def check_availability(self):
		for book in self.books:
			book_ledgers = frappe.db.sql("""select * from `tabAshram Library Book Ledger` where book = '{}' order by datetime desc limit 1""".format(book.book),as_dict=1)
			latest_quantity_available = book_ledgers[0]['qty_after_transaction']
			if book.quantity > latest_quantity_available:
				frappe.throw("Book quantity for <b>{}</b> is not avaialble in Stock. <br>(AVL QTY = <b>{}</b>)".format(book.book,latest_quantity_available))
		return