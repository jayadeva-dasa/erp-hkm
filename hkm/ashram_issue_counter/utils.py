import frappe

def update_ashram_book_ledger_on_submit(doc):
	for book in doc.books:
		last_entry = get_last_abl_entry_for_submit(book.book,doc.datetime)
		current_qty = 0 if last_entry is None else int(last_entry['qty_after_transaction'])
		qty_after_transaction = current_qty + book.quantity 

		ledger_doc = frappe.get_doc({
		    'doctype': 'Ashram Library Book Ledger',
		    'voucher_type':doc.doctype,
		    'voucher_no':doc.name,
		    'book':book.book,
		    'datetime': doc.datetime,
		    'qty': current_qty,
		    'qty_after_transaction': qty_after_transaction,
		    'transaction':'Inward'
		})
		ledger_doc.insert(ignore_permissions=True)
		update_after_entries(ledger_doc,book.book)

def get_last_abl_entry_for_submit(book,datetime):

	earlier_entries = frappe.db.sql("""
					select name,qty,qty_after_transaction,datetime from `tabAshram Library Book Ledger` 
					where datetime <= '{0}' and book = '{1}'
					""".format(datetime,book),as_dict=1)
	if len(earlier_entries) == 0:
		return None
	last_entry = earlier_entries[0]
	for index, entry in enumerate(earlier_entries):
		if entry['datetime']>last_entry['datetime']:
			last_entry = earlier_entries[index]
		elif entry['datetime'] == last_entry['datetime'] and entry['qty']>last_entry['qty']:
			last_entry = earlier_entries[index]
	return last_entry

def update_after_entries(current_ledger,book):
	after_entries = frappe.db.sql("""
					select name,qty,qty_after_transaction,datetime from `tabAshram Library Book Ledger` 
					where datetime > '{0}' and book = '{1}'
					""".format(current_ledger.datetime,book),as_dict=1)
	if len(after_entries) == 0:
		return
	else:
		qty = current_ledger.qty_after_transaction

		for entry in after_entries:
			change = entry['qty_after_transaction']-entry['qty']
			frappe.db.sql("""
							update `tabAshram Library Book Ledger` 
							set qty = {0}, qty_after_transaction = {1}
							where name = '{2}'
							""".format(qty,qty+change,entry['name']))
			qty = qty+change
	return

def update_ashram_book_ledger_on_cancel(doc):	
	for book in doc.books:
		ledgers = frappe.db.get_all("Ashram Library Book Ledger", 
						filters={'book': book.book},
						fields =['name','voucher_no','voucher_type','datetime','qty','qty_after_transaction'],
						order_by='qty')
		associated_ledger = [(ind, l) for ind,l in enumerate(ledgers) if l['voucher_no'] == doc.name]
		associated_index = associated_ledger[0][0]
		qty = 0 if associated_index == 0 else ledgers[associated_index-1]['qty_after_transaction'] #Before Ledger Quantity
		for index in range(associated_index+1,len(ledgers)):
			change = ledgers[index]['qty_after_transaction']-ledgers[index]['qty']
			frappe.db.sql("""
							update `tabAshram Library Book Ledger` 
							set qty = {0}, qty_after_transaction = {1}
							where name = '{2}'
							""".format(qty,qty+change,ledgers[index]['name']))
			qty = qty+change
		frappe.db.delete("Ashram Library Book Ledger", {
				    'book': book.book,
			        'voucher_no':doc.name,
			        'voucher_type':doc.doctype,
			        'datetime':doc.datetime
				})
	return

def issue_update_ashram_book_ledger_on_submit(doc):
	for book in doc.books:
		last_entry = get_last_abl_entry_for_submit(book.book,doc.datetime)
		current_qty = 0 if last_entry is None else int(last_entry['qty_after_transaction'])
		qty_after_transaction = current_qty - book.quantity

		ledger_doc = frappe.get_doc({
		    'doctype': 'Ashram Library Book Ledger',
		    'voucher_type':doc.doctype,
		    'voucher_no':doc.name,
		    'book':book.book,
		    'datetime': doc.datetime,
		    'qty': current_qty,
		    'transaction_user':doc.issued_to,
		    'transaction':'Issue',
		    'qty_after_transaction': qty_after_transaction
		})
		ledger_doc.insert(ignore_permissions=True)
		update_after_entries(ledger_doc,book.book)

def issue_update_ashram_book_ledger_on_cancel(doc):	
	for book in doc.books:
		ledgers = frappe.db.get_all("Ashram Library Book Ledger", 
						filters={'book': book.book},
						fields =['name','voucher_no','voucher_type','datetime','qty','qty_after_transaction'],
						order_by='qty')
		associated_ledger = [(ind, l) for ind,l in enumerate(ledgers) if l['voucher_no'] == doc.name]
		associated_index = associated_ledger[0][0]
		qty = 0 if associated_index == 0 else ledgers[associated_index-1]['qty_after_transaction'] #Before Ledger Quantity
		for index in range(associated_index+1,len(ledgers)):
			change = ledgers[index]['qty_after_transaction']-ledgers[index]['qty']
			frappe.db.sql("""
							update `tabAshram Library Book Ledger` 
							set qty = {0}, qty_after_transaction = {1}
							where name = '{2}'
							""".format(qty,qty+change,ledgers[index]['name']))
			qty = qty+change
		frappe.db.delete("Ashram Library Book Ledger", {
				    'book': book.book,
			        'voucher_no':doc.name,
			        'voucher_type':doc.doctype,
			        'datetime':doc.datetime
				})
	return

def return_update_ashram_book_ledger_on_submit(doc):
	for book in doc.books:
		last_entry = get_last_abl_entry_for_submit(book.book,doc.datetime)
		current_qty = 0 if last_entry is None else int(last_entry['qty_after_transaction'])
		qty_after_transaction = current_qty + book.quantity

		ledger_doc = frappe.get_doc({
		    'doctype': 'Ashram Library Book Ledger',
		    'voucher_type':doc.doctype,
		    'voucher_no':doc.name,
		    'book':book.book,
		    'datetime': doc.datetime,
		    'qty': current_qty,
		    'transaction_user':doc.returned_from,
		    'transaction':'Return',
		    'qty_after_transaction': qty_after_transaction
		})
		ledger_doc.insert(ignore_permissions=True)
		update_after_entries(ledger_doc,book.book)

def return_update_ashram_book_ledger_on_cancel(doc):	
	for book in doc.books:
		ledgers = frappe.db.get_all("Ashram Library Book Ledger", 
						filters={'book': book.book},
						fields =['name','voucher_no','voucher_type','datetime','qty','qty_after_transaction'],
						order_by='qty')
		associated_ledger = [(ind, l) for ind,l in enumerate(ledgers) if l['voucher_no'] == doc.name]
		associated_index = associated_ledger[0][0]
		qty = 0 if associated_index == 0 else ledgers[associated_index-1]['qty_after_transaction'] #Before Ledger Quantity
		for index in range(associated_index+1,len(ledgers)):
			change = ledgers[index]['qty_after_transaction']-ledgers[index]['qty']
			frappe.db.sql("""
							update `tabAshram Library Book Ledger` 
							set qty = {0}, qty_after_transaction = {1}
							where name = '{2}'
							""".format(qty,qty+change,ledgers[index]['name']))
			qty = qty+change
		frappe.db.delete("Ashram Library Book Ledger", {
				    'book': book.book,
			        'voucher_no':doc.name,
			        'voucher_type':doc.doctype,
			        'datetime':doc.datetime
				})
	return

def current_qty_in_stock(book):
	book_ledgers = frappe.db.sql("""select * from `tabAshram Library Book Ledger` 
									where book = '{}' order by datetime desc limit 1
								""".format(book),as_dict=1)

	if len(book_ledgers) == 0:
		return 0
	return book_ledgers[0]['qty_after_transaction']

def current_qty_with_user(user):
	books_qty = {}
	# books = frappe.db.get_all('Ashram Library Book', pluck='name')
	# for book in books:
	# 	book_issues = frappe.db.sql("""select bisit.book as book, sum(bisit.quantity) as qty
	# 									from `tabAshram Library Book Issue` bis
	# 									join `tabAshram Library Book Issue Item` bisit on bisit.parent = bis.name
	# 									group by bisit.book
	# 									where bis.issued_to = '{}' and bis.docstatus = 1 
	# 								""".format(user),as_dict=1)

	# 	if len(book_ledgers) == 0:
	# 		continue
	# 	books_qty[book] = book_ledgers[0]['qty_after_transaction']

	book_issues = frappe.db.sql("""select bisit.book as book, sum(bisit.quantity) as qty
										from `tabAshram Library Book Issue` bis
										join `tabAshram Library Book Issue Item` bisit on bisit.parent = bis.name
										where bis.issued_to = '{}' and bis.docstatus = 1 
										group by bisit.book
									""".format(user),as_dict=1)
	book_returns = frappe.db.sql("""select brtit.book as book, sum(brtit.quantity) as qty
										from `tabAshram Library Book Return` br
										join `tabAshram Library Book Return Item` brtit on brtit.parent = br.name
										where br.returned_from = '{}' and br.docstatus = 1 
										group by brtit.book
									""".format(user),as_dict=1)
	for book_issue in book_issues:
		books_qty[book_issue['book']] = book_issue['qty']

	for book_return in book_returns:
		if book_return['book'] not in books_qty:
			frappe.throw("Books Ledger Issue : Book was returned before it could have been issued. Contact Admin.")
		books_qty[book_return['book']] = books_qty[book_return['book']] - book_return['qty']

	return books_qty