// Copyright (c) 2025, Narahari Dasa and contributors
// For license information, please see license.txt

frappe.query_reports["Asset Lifewise"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"reqd":1,
			"width":80,
			"default": frappe.defaults.get_user_default("Company")
		},
		{
			"fieldname": "from_fiscal_year",
			"label": __("From Fiscal Year"),
			"fieldtype": "Link",
			"options": "Fiscal Year",
			"reqd":1,
			"width":80,
			"default": frappe.defaults.get_user_default("Fiscal Year")
		},
		{
			"fieldname": "to_fiscal_year",
			"label": __("To Fiscal Year"),
			"fieldtype": "Link",
			"options": "Fiscal Year",
			"reqd":1,
			"width":80,
			"default": frappe.defaults.get_user_default("Fiscal Year")
		}
	]
};
