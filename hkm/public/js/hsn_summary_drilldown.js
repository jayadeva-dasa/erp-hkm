function attach_hsn_formatter_once_ready(retries) {
    if (frappe.get_route().join("/") !== "query-report/HSN-wise-summary of outward supplies") {
        return;
    }

    const report_config = frappe.query_reports["HSN-wise-summary of outward supplies"];

    if (!report_config) {
        if (retries > 0) {
            setTimeout(() => attach_hsn_formatter_once_ready(retries - 1), 300);
        }
        return;
    }

    if (report_config.__hsn_drilldown_patched) return;
    report_config.__hsn_drilldown_patched = true;

    const original_formatter = report_config.formatter;

    report_config.formatter = function (value, row, column, data, default_formatter) {
        if (column.fieldname === "hsn_code" && data && data.hsn_code && data.hsn_code !== "Total") {
            return `<a href="javascript:void(0)" onclick="window.__open_hsn_voucher_register('${data.hsn_code}')">${data.hsn_code}</a>`;
        }
        if (original_formatter) {
            return original_formatter(value, row, column, data, default_formatter);
        }
        return default_formatter(value, row, column, data);
    };

    if (frappe.query_report && frappe.query_report.report_name === "HSN-wise-summary of outward supplies") {
        frappe.query_report.refresh();
    }
}

frappe.router.on("change", () => attach_hsn_formatter_once_ready(20));
attach_hsn_formatter_once_ready(20);

window.__open_hsn_voucher_register = function (hsn_code) {
    const filters = frappe.query_report.get_filter_values();
    frappe.route_options = {
        company: filters.company,
        from_date: filters.from_date,
        to_date: filters.to_date,
        hsn_code: hsn_code,
    };
    frappe.set_route("query-report", "HSN Voucher Register");
};
