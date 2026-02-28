# Copyright (c) 2013, NRHD and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import msgprint, _
from frappe.utils import flt
import pandas as pd
from datetime import datetime

def execute(filters=None):
    # columns, data = [], []
    # return columns, data
    if not filters: filters = {}
    #filters.update({"from_date": filters.get("date_range") and filters.get("date_range")[0], "to_date": filters.get("date_range") and filters.get("date_range")[1]})
    # start = datetime.strptime("01/{}/{}".format(filters['from_month'],filters['from_year']), '%d/%B/%Y')
    # end = datetime.strptime("01/{}/{}".format(filters['to_month'],filters['to_year']), '%d/%B/%Y')
    # ranges = pd.date_range(start, end, freq='MS')
    # mon_yrs = []
    # for r in ranges:
    # 	mon = r.strftime('%B')
    # 	yr = r.strftime('%Y')
    # 	small_m =  r.strftime('%b')
    # 	small_y = r.strftime('%y')
    # 	mon_yrs.append([mon, yr, small_m, small_y])

    columns = get_columns(filters)
    #conditions = get_condition(filters)
    # data =[]
    # data_map={}

    item_map = {}
    conditions = ""
    # if 'residency' in filters:
    # 	conditions += "AND FS.residency= %(residency)s"
    for i in frappe.db.sql("""
        SELECT 
        name, uom
        FROM `tabAshram Store Item` as ASI
         """,as_dict=1):
             item_map.setdefault(i.name, i)
    data=[]
    for item in sorted(item_map):
        item_data =[]
        inward = frappe.db.sql("""
            SELECT SUM(ASINI.quantity) as total_inward
            FROM `tabAshram Store Inward` as ASIN
            JOIN `tabAshram Store Inward Item` as ASINI
                ON ASIN.name= ASINI.parent
             WHERE ASIN.docstatus = 1 
             AND ASINI.item=%(item)s""",{"item":item},as_dict=0)
        outward = frappe.db.sql("""
            SELECT SUM(ASINI.quantity) as total_outward
            FROM `tabAshram Store Item Issue` as ASIN
            JOIN `tabAshram Store Outward Item` as ASINI
                ON ASIN.name= ASINI.parent
             WHERE ASIN.docstatus = 1 
             AND ASINI.item=%(item)s""",{"item":item},as_dict=0)
        inward_sum = inward[0][0] if inward[0][0] else 0
        outward_sum = outward[0][0] if outward[0][0] else 0
        item_data.append(item)
        item_data.append(item_map[item]['uom'])
        item_data.append(inward_sum)
        item_data.append(outward_sum)
        item_data.append(inward_sum-outward_sum)
        data.append(item_data)
    return columns, data #, None, chart_data

def get_columns(filters):
    """return columns based on filters"""
    columns = [
        {
        "fieldname": "item_name",
        "label":"Item Name",
        "fieldtype": "Link",
        "options":"Ashram Store Item",
        "width": 150
        },
        {
        "fieldname": "uom",
        "label":"UOM",
        "fieldtype": "Data",
        "width": 150
        },
        {
        "fieldname": "total_inward",
        "label":"Total Inward",
        "fieldtype": "Float",
        "width": 150
        },
        {
        "fieldname": "total_issue",
        "label":"Total Issue",
        "fieldtype": "Float",
        "width": 150
        },
        {
        "fieldname": "balance",
        "label":"Balance",
        "fieldtype": "Float",
        "width": 150
        }

    ]
    return columns