frappe.provide('frappe.dashboards.chart_sources');

frappe.dashboards.chart_sources["Visitors Hourly"] = {
	method: "hkm.security.dashboard_chart_source.visitors_hourly.visitors_hourly.get",
	filters: [
		{
			fieldname: "date_range",
			label: __("Date Range"),
			fieldtype: "DateRange",
			default: [frappe.datetime.add_days(frappe.datetime.get_today(), -7), frappe.datetime.get_today()],
		}
	]
};