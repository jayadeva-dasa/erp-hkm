// Copyright (c) 2016, Narahari Das and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Stock Received But Not Billed"] = {
	"filters": [
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
			"reqd": 1
		},
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			//"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			//"reqd": 1,
			"width": "60px",
			"hidden": 1
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1,
			"width": "60px"
		},	
		{
			"fieldname":"show_difference",
			"label": __("Show Difference"),
			"fieldtype": "Check",
			"default": 1,
		},	
	]
};
