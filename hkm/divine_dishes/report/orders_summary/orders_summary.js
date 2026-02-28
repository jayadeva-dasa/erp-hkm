// Copyright (c) 2023, Narahari Dasa and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Orders Summary"] = {
	"filters": [
		{
			"fieldname": "date_range",
			"label": __("Date Range"),
			"fieldtype": "DateRange",
			"default": [frappe.datetime.add_months(frappe.datetime.get_today(), -1), frappe.datetime.get_today()],
			"reqd": 1
		},
		{
			"fieldname": "customer",
			"label": __("Customer"),
			"width": 80,
			"fieldtype": "Link",
			"options": "User"
		},
		// {
		// 	"fieldname": "area",
		// 	"label": __("Area"),
		// 	"width": 80,
		// 	"fieldtype": "Data"
		// },
	],
	"formatter": function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		return "<span style='font-size: 12px;'>" + value + "</span>";
	},
};
