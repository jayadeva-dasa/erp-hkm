// Copyright (c) 2023, Narahari Dasa and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Warehouse Sales & Stock Analysis"] = {
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
			"fieldname": "warehouse",
			"label": __("Warehouse"),
			"fieldtype": "Link",
			"options": "Warehouse",
			"reqd":1,
			"width":80,
			"get_query": function() {
				var company = frappe.query_report.get_filter_value('company');
				return {
					"doctype": "Warehouse",
					"filters": {
						"company": company,
					}
				}
			}
		},
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"reqd":1,
			"width":80,
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"reqd":1,
			"width":80,
		},
		{
			"fieldname": "show_for_pos_closing",
			"label": __("Show POS Closing"),
			"fieldtype": "Check",
			"width":80,
		},
	],
	"formatter": function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		
		if (["opening_balance","total_purchase_income","total_transfer_income"].includes(column.fieldname)){
				value = "<span style='color:#0F382B'><b>" + value + "</b></span>";
		}
		else if (column.fieldname.startsWith("EX-")){
			value = "<span style='color:red'>" + value + "</span>";
		}
		else if (column.fieldname.startsWith("SL-")){
			value = "<span style='color:indigo'>" + value + "</span>";
		}
		else if (column.fieldname.startsWith("TW-")){
			value = "<span style='color:purple'>" + value + "</span>";
		}
		else if (column.fieldname == "closing_balance"){
			value = "<span style='color:#025e00'><b>" + value + "</span>";
		}
		return "<span style='font-size: 12px;'>"+value+"</span>";
	},	
};
