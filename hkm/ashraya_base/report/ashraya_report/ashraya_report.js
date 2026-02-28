// Copyright (c) 2016, NRHD and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Ashraya Report"] = {
	"filters": [
		{
			"fieldname": "guide",
			"label": __("Ashraya Guide"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Ashraya Guide"
		},
		{
			"fieldname": "last_ashraya",
			"label": __("Latest Ashraya Level"),
			"fieldtype": "Link",
			"width": "200",
			"options": "Ashraya Level"
		}
	]
};
