# Copyright (c) 2022, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe
from hkm.ashram_issue_counter.utils import current_qty_in_stock

def execute(filters=None):
	columns, data = [], []

	columns = get_columns(filters)
	data, message, summary = get_data(filters)
	return columns, data


def get_columns(filters):
	columns = [
				{
				"label":("Book"),
				"fieldname": "book",
				"fieldtype": "Link",
				"options" : "Ashram Library Book",
				"width": 300
				},
				{
				"label":("Available Quantity"),
				"fieldname": "avl_qty",
				"fieldtype": "Data",
				"width": 180
				},
				]
	return columns


def get_data(filters):
	data=[]
	summary=[]
	message=""
	books = frappe.db.get_all('Ashram Library Book', pluck='name')
	for book in books:
		latest_quantity_available = current_qty_in_stock(book)
		data.append({"book":book,"avl_qty":"<div style= 'margin: auto; padding-left: 50px;font-weight: bold;'>"+str(latest_quantity_available)+"</div>"})

	return data, summary, message