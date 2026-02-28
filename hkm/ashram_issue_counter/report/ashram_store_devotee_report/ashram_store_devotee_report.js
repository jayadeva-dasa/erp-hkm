// Copyright (c) 2016, NRHD and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Ashram Store Devotee Report"] = {
	"filters": [
		{
			"fieldname": "user",
			"label": __("User"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Ashram Store User"

		},
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"width": "100",
			"default":frappe.datetime.nowdate()
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"width": "100",
			"default":frappe.datetime.nowdate()
		}
	]
};
