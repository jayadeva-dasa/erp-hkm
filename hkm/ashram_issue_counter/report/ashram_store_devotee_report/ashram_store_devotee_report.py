# Copyright (c) 2013, NRHD and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import msgprint, _
from frappe.utils import flt
import pandas as pd
from datetime import datetime

def execute(filters=None):
	if not filters: filters = {}
	columns = get_columns(filters)
	conditions = get_conditions(filters)
	item_map = {}

	for i in frappe.db.sql("""
		SELECT ASROIT.item, SUM(ASROIT.quantity) as qty
		FROM `tabAshram Store Item Issue` as ASRIS
			JOIN `tabAshram Store Outward Item` as ASROIT
			ON ASROIT.parent = ASRIS.name
		WHERE ASRIS.docstatus = 1 {}
		GROUP BY ASROIT.item
		ORDER BY ASROIT.item
	 	""".format(conditions),values = filters, as_dict=1):
	 		item_map.setdefault(i.item, i)
	data=[]
	for item in sorted(item_map):
		item_data =[]
		item_data.append(item)
		item_data.append(item_map[item]['qty'])
		data.append(item_data)
		
	return columns, data #, None, chart_data

def get_columns(filters):
	"""return columns based on filters"""
	columns = [
		{
		"fieldname": "id",
		"label":"Item",
		"fieldtype": "Link",
		"options":"Ashram Store Item",
		"width": 150
		},
		{
		"fieldname": "qty",
		"label":"Quantity",
		"fieldtype": "Data",
		"width": 150
		}
	]
	return columns

def get_conditions(filters):
	conditions = ""
	if ('user' not in filters) or ( not filters['user']):
		frappe.throw("User is required.")
	else:
		conditions+= " and issued_to = %(user)s"

	if ('from_date' not in filters) or (not filters['from_date']):
		frappe.throw("From Date is required.")
	else:
		conditions+= " and date >= %(from_date)s"
	
	if ('to_date' not in filters) or (not filters['to_date']):
		frappe.throw("To Date is required.")
	else:
		conditions+= " and date <= %(to_date)s"

	return conditions