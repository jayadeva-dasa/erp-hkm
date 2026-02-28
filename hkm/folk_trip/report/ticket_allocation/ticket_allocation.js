// Copyright (c) 2016, NRHD and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Ticket Allocation"] = {
	"filters": [
		{
			"fieldname": "trip",
			"label": __("Trip"),
			"fieldtype": "Link",
			"width": "120",
			"reqd":1,
			"options": "FOLK Trip",
			// "depends_on": "eval:frappe.query_report.get_filter_value('report_type')=='Yatri Wise'"
		},
		{
			"fieldname": "train",
			"label": __("Train"),
			"fieldtype": "Link",
			"width": "120",
			"options": "FOLK Trip Train",
			"depends_on": "eval:frappe.query_report.get_filter_value('report_type')!='Yatri Wise'"
		},
		{
			"fieldname": "report_type",
			"label": __("Report Type"),
			"fieldtype": "Select",
			"options":["Ticket Wise","Seat Summary","Yatri Wise"],
			"width": "120",
		}
	]
};
