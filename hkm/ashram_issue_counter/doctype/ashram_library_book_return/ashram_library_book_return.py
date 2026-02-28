# Copyright (c) 2022, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from hkm.ashram_issue_counter.utils import return_update_ashram_book_ledger_on_submit,return_update_ashram_book_ledger_on_cancel,current_qty_with_user

class AshramLibraryBookReturn(Document):
	def on_submit(self):
		return_update_ashram_book_ledger_on_submit(self)
		return
	def on_cancel(self):
		return_update_ashram_book_ledger_on_cancel(self)
		return
	def validate(self):
		self.check_issuance()

	def check_issuance(self):
		books_qty  = current_qty_with_user(self.returned_from)
		for returning_book in self.books:
			if returning_book.book not in books_qty:
				frappe.throw("Book <b>{}</b> is not issued to this User.".format(returning_book.book))
			if returning_book.quantity > books_qty[returning_book.book]:
				frappe.throw("Book <b>{}</b>'s returning quantity <b>{}</b> is more that what was issued (<b>{}</b>)".format(returning_book.book, returning_book.quantity, books_qty[returning_book.book]))
		return