// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Student Rent Report"] = {
	"filters": [
		{
			"fieldname": "residency",
			"label": __("FOLK Residency"),
			"fieldtype": "Link",
			"options": "FOLK Residency",
			"width":80,
		},
		{
			"fieldname": "from_month",
			"label": __("From Month"),
			"fieldtype": "Select",
			"options": ['January','February', 'March', 'April', 'May', 'June', 'July','August', 'September', 'October', 'November', 'December'],
			"default": moment().startOf("month").format('MMMM'),
			"width":80,
		},
		{
			"fieldname": "from_year",
			"label": __("From Year"),
			"fieldtype": "Int",
			"default": moment().format('YYYY'),
			"width":80,
		},
		{
			"fieldname": "to_month",
			"label": __("From Month"),
			"fieldtype": "Select",
			"options": ['January','February', 'March', 'April', 'May', 'June', 'July','August', 'September', 'October', 'November', 'December'],
			"default": moment().startOf("month").format('MMMM'),
			"width":80,
		},
		{
			"fieldname": "to_year",
			"label": __("To Year"),
			"fieldtype": "Int",
			"default": moment().format('YYYY'),
			"width":80,
		},
	]
};
