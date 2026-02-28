# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
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
	start = datetime.strptime("01/{}/{}".format(filters['from_month'],filters['from_year']), '%d/%B/%Y')
	end = datetime.strptime("01/{}/{}".format(filters['to_month'],filters['to_year']), '%d/%B/%Y')
	ranges = pd.date_range(start, end, freq='MS')
	mon_yrs = []
	for r in ranges:
		mon = r.strftime('%B')
		yr = r.strftime('%Y')
		small_m =  r.strftime('%b')
		small_y = r.strftime('%y')
		mon_yrs.append([mon, yr, small_m, small_y])

	columns = get_columns(filters,mon_yrs)
	#conditions = get_condition(filters)
	data =[]
	data_map={}

	students_map = {}
	conditions = ""
	if 'residency' in filters:
		conditions += "AND FS.residency= %(residency)s"
	for i in frappe.db.sql("""
		SELECT 
		name, full_name
		FROM `tabFOLK Student` as FS
	 	WHERE FS.enabled = 1 AND FS.folk_resident =1 %s"""%conditions,filters,as_dict=1):
		students_map.setdefault(i.name, i)
	data=[]
	for student in sorted(students_map):
		total = 0
		security_amount = 0
		for i in frappe.db.sql("""
					SELECT name,amount
					FROM `tabFOLK Residency Rent` as FRS
				 	WHERE FRS.docstatus = 1 AND FRS.rent_type = 'Security' AND FRS.folk_student= %(student)s""",{"student":student},as_dict=1):
			security_amount = security_amount + i.amount
		total+= security_amount
		single_student_data = [student,students_map[student]["full_name"], security_amount]
		for my in mon_yrs:
				docs = frappe.db.get_list('FOLK Residency Rent', 
									filters = {
				                        "rent_type": 'Hostel Rent',
				                        "folk_student": student,
				                        "month": my[0],
				                        "year":my[1],
				                        "docstatus":1
				                    	},
									fields = ['name', 'amount'],
									as_list=True)
				my_amount = 0
				for doc in docs:
					my_amount+= doc[1]
				total+= my_amount
				single_student_data.append(my_amount)
		single_student_data.append(total)
		data.append(single_student_data)
	return columns, data #, None, chart_data

def get_columns(filters,mon_yrs):
	"""return columns based on filters"""
	columns = [
		{
		"fieldname": "studentID",
		"label":"SID",
		"fieldtype": "Link",
		"options":"FOLK Student",
		"width": 150
		},
		{
		"fieldname": "student",
		"label":"Student Name",
		"fieldtype": "Data",
		"width": 150
		},
		{
		"fieldname": "security",
		"label":"Security",
		"fieldtype": "Currency",
		"width": 100
		},
	]
	for r in mon_yrs:

		columns.append({
			"fieldname": r[0]+"-"+r[1],
			"label":r[2]+"-"+r[3],
			"fieldtype": "Currency",
			"width": 100
			})
	columns.append({
			"fieldname": 'total',
			"label":'Total',
			"fieldtype": "Currency",
			"width": 120
			})
	return columns