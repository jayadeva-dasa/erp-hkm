# Copyright (c) 2013, Narahari Das and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import copy
from frappe import _
from frappe.utils import flt, date_diff, getdate

def execute(filters=None):

	if not filters:
		return [], []

	validate_filters(filters)

	columns = get_columns(filters)

	conditions = get_conditions(filters)

	data = get_data(conditions, filters)

	if not data:
		return [], [], None, []

	data = prepare_data(data, filters)

	return columns, data, None, None

def get_conditions(filters):
	conditions = ""
	if filters.get("from_date") and filters.get("to_date"):
		conditions += " and po.transaction_date between %(from_date)s and %(to_date)s"

	if filters.get("company"):
		conditions += " and po.company = %(company)s"

	if filters.get("department"):
		conditions += " and po.department = %(department)s"

	return conditions

def get_data(conditions, filters):
	sql_string = """
		SELECT tab_PRI.*, SUM(IFNULL(pii.qty, 0)) as billed_qty  # v16: TODO - Use pypika Field objects for ifnull
		FROM
		(SELECT tab_PI.*
		FROM 
		(SELECT
			po.transaction_date as date,
			poi.schedule_date as required_date,
			po.name as purchase_order,
			po.status, po.supplier, poi.item_code,poi.item_name,
			poi.qty, poi.received_qty,
			(poi.qty - poi.received_qty) AS pending_qty,
			-- IFNULL(pii.qty, 0) as billed_qty,  # v16: TODO - Use pypika Field objects for ifnull
			poi.base_amount as amount,
			(poi.received_qty * poi.base_rate) as received_qty_amount,
			(poi.billed_amt * IFNULL(po.conversion_rate, 1)) as billed_amount,  # v16: TODO - Use pypika Field objects for ifnull
			(poi.base_amount - (poi.billed_amt * IFNULL(po.conversion_rate, 1))) as pending_amount,  # v16: TODO - Use pypika Field objects for ifnull
			po.set_warehouse as warehouse,po.naming_series,
			po.company, poi.name,po.department
		FROM
			`tabPurchase Order` po
		JOIN
			`tabPurchase Order Item` poi
			ON poi.parent = po.name
		WHERE
			po.status not in ('Stopped', 'Closed')
			and po.docstatus = 1
			{0}
		-- GROUP BY poi.name
		
		) as tab_PI
		LEFT JOIN `tabPurchase Receipt Item` pri
			ON pri.purchase_order = tab_PI.purchase_order AND pri.docstatus = 1
		-- WHERE
		-- 	pri.docstatus = 1
		GROUP BY tab_PI.name) as tab_PRI
		LEFT JOIN `tabPurchase Invoice Item` pii
			ON pii.po_detail = tab_PRI.name AND pii.docstatus = 1
		
		GROUP BY tab_PRI.name
		ORDER BY tab_PRI.date ASC
		
	""".format(conditions)
	data = frappe.db.sql(sql_string, filters, as_dict=1)

	return data


def validate_filters(filters):
	from_date, to_date = filters.get("from_date"), filters.get("to_date")

	if not from_date and to_date:
		frappe.throw(_("From and To Dates are required."))
	elif date_diff(to_date, from_date) < 0:
		frappe.throw(_("To Date cannot be before From Date."))

def get_columns(filters):
	columns = [
		{
			"label":_("Date"),
			"fieldname": "date",
			"fieldtype": "Date",
			"width": 90
		},
		{
			"label":_("Department"),
			"fieldname": "department",
			"fieldtype": "Link",
			"options":"Department",
			"width": 100
		},
		{
			"label": _("Purchase Order"),
			"fieldname": "purchase_order",
			"fieldtype": "Link",
			"options": "Purchase Order",
			"width": 160
		},
		{
			"label": _("Supplier"),
			"fieldname": "supplier",
			"fieldtype": "Link",
			"options": "Supplier",
			"width": 130
		},
		{
			"label":_("Item Code"),
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 100
		},
		{
			"label":_("Item Name"),
			"fieldname": "item_name",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Qty"),
			"fieldname": "qty",
			"fieldtype": "Float",
			"width": 120
		},
		{
			"label": _("Warehouse"),
			"fieldname": "warehouse",
			"fieldtype": "Link",
			"options": "Warehouse",
			"width": 100
		},
		{
			"label": _("Received Qty"),
			"fieldname": "received_qty",
			"fieldtype": "Float",
			"width": 120
		},
		{
			"label": _("Billed Qty"),
			"fieldname": "billed_qty",
			"fieldtype": "Float",
			"width": 80,
			"convertible": "qty"
		},
		{
			"label": _("Ordered Qty to Bill"),
			"fieldname": "ord_qty_to_bill",
			"fieldtype": "Float",
			"width": 120,
			"convertible": "qty"
		},
		{
			"label": _("Recd Qty to Bill"),
			"fieldname": "recd_qty_to_bill",
			"fieldtype": "Float",
			"width": 120,
			"convertible": "qty"
		},
		{
			"label": _("Amount"),
			"fieldname": "amount",
			"fieldtype": "Currency",
			"width": 110,
			"options": "Company:company:default_currency",
			"convertible": "rate"
		},
		{
			"label": _("Billed Amount"),
			"fieldname": "billed_amount",
			"fieldtype": "Currency",
			"width": 110,
			"options": "Company:company:default_currency",
			"convertible": "rate"
		},
		{
			"label": _("Pending Amount"),
			"fieldname": "pending_amount",
			"fieldtype": "Currency",
			"width": 110,
			"options": "Company:company:default_currency",
			"convertible": "rate"
		},
		{
			"label": _("Company"),
			"fieldname": "company",
			"fieldtype": "Link",
			"width": 110,
			"options": "Company"
		},
		{
			"label": _("POI Name"),
			"fieldname": "name",
			"fieldtype": "Data",
			"width": 110
		}]

	return columns

def prepare_data(data, filters):
	for row in data:
		row['ord_qty_to_bill'] = row['qty'] - row['billed_qty']
		if row['naming_series'] == 'WOR-ORD-.YYYY.-':
			row['recd_qty_to_bill'] = 0
		else:
			row['recd_qty_to_bill'] = row['received_qty'] - row['billed_qty']
	return data
