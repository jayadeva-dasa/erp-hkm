# Copyright (c) 2013, NRHD and contributors
# For license information, please see license.txt

import frappe
from frappe import _
def execute(filters=None):
	columns, data = [], []
	columns = get_columns(filters)
	data, message, summary = get_data(filters)
	return columns, data, message, None, summary

def get_data(filters):
	data=[]
	summary=[]
	message=""
	
	if filters.get("report_type") =='Ticket Wise':
		data = get_ticket_wise_data(filters)
	elif filters.get("report_type") =='Seat Summary':
		data = get_seat_summary(filters)
	elif filters.get("report_type") =='Yatri Wise':
		data = get_yatri_wise_data(filters)

	# summary = get_report_summary(data, filters) or []

	return data, summary, message

def get_conditions(filters):
		conditions = ""
		if filters.get("train"):
			conditions += " and fttt.train = %(train)s"
		# if filters.get("from_date"):
		# 	conditions += " and jv.posting_date >= %(from_date)s"
		# if filters.get("to_date"):
		# 	conditions += " and jv.posting_date <= %(to_date)s"	
		# if filters.get("jv_entry"):
		# 	conditions += " and jv.name = %(jv_entry)s"
		return conditions

def get_columns(filters):
	columns = []
	if filters.get("report_type") =='Ticket Wise':
		columns.extend([
			{
				"label":_("Ticket Name"),
				"fieldname": "ticket_name",
				"fieldtype": "Data",
				"width": 180
			},
			{
				"label":_("PNR"),
				"fieldname": "pnr_number",
				"fieldtype": "Data",
				"width": 120
			},
			{
				"label":_("From-To"),
				"fieldname": "fromto",
				"fieldtype": "Data",
				"width": 120
			},		
			{
				"label":_("Coach"),
				"fieldname": "coach",
				"fieldtype": "Data",
				"width": 70
			},	
			{
				"label":_("Seat"),
				"fieldname": "seat",
				"fieldtype": "Data",
				"width": 70
			},		
			{
				"label": _("Alloted To"),
				"fieldname": "allocated_name",
				"fieldtype": "Link",
				"options": "FOLK Trip Yatri",
				"width": 130
			},
			{
				"label": _("FOLK Guide"),
				"fieldname": "folk_guide",
				"fieldtype": "Link",
				"options": "FOLK Guide",
				"width": 130
			},
			{
				"label": _("Mobile Number"),
				"fieldname": "mobile_no",
				"fieldtype": "Data",
				"width": 130
			}
		])
	elif filters.get("report_type") =='Seat Summary':
		columns.extend([
			{
				"label":_("Coach Number"),
				"fieldname": "coach",
				"fieldtype": "Data",
				"width": 180
			},
			{
				"label":_("Total Seats"),
				"fieldname": "seats",
				"fieldtype": "Int",
				"width": 120
			},
		])
	elif filters.get("report_type") =='Yatri Wise':
		columns.extend([
			{
				"label":_("Yatri Name"),
				"fieldname": "full_name",
				"fieldtype": "Data",
				"width": 180
			},
			{
				"label":_("Mobile Number"),
				"fieldname": "mobile_no",
				"fieldtype": "Data",
				"width": 180
			},
			{
				"label":_("FOLK Guide"),
				"fieldname": "folk_guide",
				"fieldtype": "Link",
				"options":"FOLK Guide",
				"width": 180
			}
		])
		# trip = frappe.get_doc("FOLK Trip",filters.get("trip"))
		trains = frappe.db.get_all('FOLK Trip Train',filters={'trip':filters.get("trip")}, fields = ['from','to','name'])
		columns.extend([dict(
							label = train['from']+'-'+train['to'],
							fieldname = train['name'],
							fieldtype = "Data",
							width = 120
							) for train in trains])

	return columns


def get_ticket_wise_data(filters):
	conditions = get_conditions(filters)
	return frappe.db.sql("""
			select fttp.ticket_name,fttt.pnr_number,
				fttp.coach_number as coach,
				fttp.seat_number as seat,
				concat(ftt.from,"-",ftt.to) as fromto,
				fttp.allocated_name,
				fty.mobile_no,fty.folk_guide
			from `tabFOLK Trip Train Ticket` fttt
			join `tabFOLK Trip Train Passenger` fttp on (fttp.parent = fttt.name)
			left join `tabFOLK Trip Yatri` fty on (fttp.allocated_to = fty.name)
			join `tabFOLK Trip Train` ftt on (ftt.name = fttt.train)
			where 1 {conditions}
			order by fttt.pnr_number
			""".format(conditions=conditions), filters, as_dict=1)

def get_seat_summary(filters):
	conditions = get_conditions(filters)
	data = frappe.db.sql("""
			select fttp.coach_number as coach,count(fttp.coach_number) as seats
			from `tabFOLK Trip Train Ticket` fttt
			join `tabFOLK Trip Train Passenger` fttp on (fttp.parent = fttt.name)
			where 1 {conditions}
			group by coach
			""".format(conditions=conditions), filters, as_dict=1)
	data.append(dict(coach = '<b>Total</b>',seats = sum([d['seats'] for d in data])))
	return data
def get_yatri_wise_data(filters):
	trains = frappe.db.get_all('FOLK Trip Train',filters={'trip':filters.get("trip")}, fields = ['from','to','name'])
	yatris = frappe.db.get_all('FOLK Trip Yatri',filters={'trip':filters.get("trip")}, fields = ['name','type','full_name','folk_guide','mobile_no'])
	# fty.full_name,fty.type,fty.folk_guide,fty.mobile_no,
	combined = frappe.db.sql("""
					select 
						fty.name,
						fttp.ticket_name,fttp.coach_number,fttp.seat_number,
						fttt.pnr_number,fttt.train
					from `tabFOLK Trip Yatri` fty
					join `tabFOLK Trip Train Passenger` fttp on (fttp.allocated_to = fty.name) 
					join `tabFOLK Trip Train Ticket` fttt on (fttp.parent = fttt.name)
					where fty.trip = '{}'
					""".format(filters.get("trip")),as_dict=1)
	data = yatris
	for d in data:
		for train in trains:
			d[train['name']]  = None
	for com in combined:
		yatri_ind = next(i for i,y in enumerate(data) if y["name"] == com["name"])
		data[yatri_ind][com['train']] = com['coach_number'] +"/"+ str(com['seat_number'])
	return data
