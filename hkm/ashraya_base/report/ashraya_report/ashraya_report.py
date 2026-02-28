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
	candidate_map = {}

	for i in frappe.db.sql("""
		SELECT *
		FROM `tabAshraya Candidate` as ASYCND
		WHERE enabled = true {}
	 	""".format(conditions),values = filters, as_dict=1):
		candidate_map.setdefault(i.name, i)	 	 
	data = []
	for candidate in sorted(candidate_map):
		candidate_data =[]
		candidate_data.append(candidate)
		candidate_data.append(candidate_map[candidate]['full_name'])
		candidate_data.append(candidate_map[candidate]['mobile'])
		candidate_data.append(candidate_map[candidate]['guide'])
		candidate_data.append(candidate_map[candidate]['latest_level_of_ashraya'])
		data.append(candidate_data)
		
	return columns, data #, None, chart_data

def get_columns(filters):
	"""return columns based on filters"""
	columns = [
		{
		"fieldname": "cand_id",
		"label":"Candidate ID",
		"fieldtype": "Link",
		"options":"Ashraya Candidate",
		"width": 150
		},
		{
		"fieldname": "full_name",
		"label":"Candidate Name",
		"fieldtype": "Data",
		"width": 150
		},
		{
		"fieldname": "mobile",
		"label":"Mobile",
		"fieldtype": "Data",
		"width": 150
		},
		{
		"fieldname": "guide",
		"label":"Guide",
		"fieldtype": "Link",
		"options":"Ashraya Guide",
		"width": 150
		},
		{
		"fieldname": "last_ashraya",
		"label":"Last Ashraya",
		"fieldtype": "Link",
		"options":"Ashraya Level",
		"width": 150
		}
	]
	return columns


def get_chart_data(data):
	if not (data):
		return []
	devotees = [item[0] for item in data]

	labels = list(set(devotees))
   	
	datapoints = [0] * len(labels)

	for row in data:
		for idx, label in enumerate(labels):
			if row[0] == label:
				datapoints[idx] = datapoints[idx] + row[5]

	return {
		"data" : {
			"labels" : labels,
			"datasets" : [
				{
					"name" : "Donation Report",
					"values" : datapoints
				}
			]
		},
		"type" : "bar",
		"lineOptions": {
			"regionFill": 1
		}
	}
def get_conditions(filters):
	conditions = ""
	if 'last_ashraya' in filters and filters['last_ashraya']:
		conditions+= " and ASYCND.latest_level_of_ashraya = %(last_ashraya)s"
	if 'guide' in filters and filters['guide']:
		conditions+= " and ASYCND.guide = %(guide)s"

	return conditions