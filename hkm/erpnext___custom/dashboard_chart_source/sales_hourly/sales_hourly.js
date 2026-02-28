frappe.provide('frappe.dashboards.chart_sources');

frappe.dashboards.chart_sources["Sales Hourly"] = {
	method: "hkm.erpnext___custom.dashboard_chart_source.sales_hourly.sales_hourly.get",
	filters: [
		{
			fieldname: "pos_profile",
			label: __("POS Profile"),
			fieldtype: "Link",
			options: "POS Profile"
		},
		{
			fieldname: "date_range",
			label: __("Date Range"),
			fieldtype: "DateRange",
			default: [frappe.datetime.add_days(frappe.datetime.get_today(),-7), frappe.datetime.get_today()],
		}
	]
};