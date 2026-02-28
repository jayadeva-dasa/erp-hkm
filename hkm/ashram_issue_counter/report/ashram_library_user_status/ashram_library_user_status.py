# Copyright (c) 2022, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe

from hkm.ashram_issue_counter.utils import current_qty_with_user

def execute(filters=None):
	columns, data = [], []

	columns = get_columns(filters)
	data, message, summary = get_data(filters)
	return columns, data


def get_columns(filters):
	columns = [
				{
				"label":("User"),
				"fieldname": "user",
				"fieldtype": "Link",
				"options" : "Ashram Store User",
				"width": 300
				},
				{
				"label":("Book"),
				"fieldname": "book",
				"fieldtype": "Data",
				"width": 180
				},
				{
				"label":("Book Quantity"),
				"fieldname": "qty",
				"fieldtype": "Data",
				"width": 180
				},
				# {
				# "label":("Days Before"),
				# "fieldname": "days",
				# "fieldtype": "Data",
				# "width": 180
				# },
				]
	return columns


def get_data(filters):
	data=[]
	summary=[]
	message=""
	users = frappe.db.get_all('Ashram Store User', pluck='name')
	# books = frappe.db.get_all('Ashram Library Book', pluck='name')
	for user in users:
		#userflag = 0
		issued_books_qty = current_qty_with_user(user)
		if issued_books_qty:
			row_flag = 0
			for book,qty in issued_books_qty.items():
				quantity = "<div style= 'margin: auto; padding-left: 50px;font-weight: bold;'>{}</div>".format(qty)
				if row_flag == 0:
					data.append({"user":user,"book":book,"qty":quantity})
					row_flag =+ 1
				else:
					data.append({"user":"","book":book,"qty":quantity})

	return data, summary, message
