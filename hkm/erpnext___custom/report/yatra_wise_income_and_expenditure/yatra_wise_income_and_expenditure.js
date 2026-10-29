// Copyright (c) 2026, HKM and contributors
// For license information, please see license.txt

frappe.query_reports["Yatra Wise Income and Expenditure"] = {
  filters: [
    {
      fieldname: "company",
      label: __("Company"),
      fieldtype: "Link",
      options: "Company",
      reqd: 1,
      default: frappe.defaults.get_user_default("Company"),
    },
    {
      fieldname: "fiscal_year",
      label: __("Fiscal Year"),
      fieldtype: "Link",
      options: "Fiscal Year",
      on_change: function (query_report) {
        const fiscal_year = query_report.get_values().fiscal_year;
        if (!fiscal_year) return;
        frappe.model.with_doc("Fiscal Year", fiscal_year, function () {
          const fy = frappe.model.get_doc("Fiscal Year", fiscal_year);
          frappe.query_report.set_filter_value({
            from_date: fy.year_start_date,
            to_date: fy.year_end_date,
          });
        });
      },
    },
    {
      fieldname: "from_date",
      label: __("From Date"),
      fieldtype: "Date",
      reqd: 1,
      default: erpnext.utils.get_fiscal_year(frappe.datetime.get_today(), true)[1],
    },
    {
      fieldname: "to_date",
      label: __("To Date"),
      fieldtype: "Date",
      reqd: 1,
      default: erpnext.utils.get_fiscal_year(frappe.datetime.get_today(), true)[2],
    },
    {
      fieldname: "pk_yatra",
      label: __("Yatra"),
      fieldtype: "MultiSelectList",
      get_data: (txt) => frappe.db.get_link_options("PK Yatra", txt),
    },
    {
      fieldname: "pk_yatra_batch",
      label: __("Yatra Batch"),
      fieldtype: "MultiSelectList",
      get_data: (txt) => frappe.db.get_link_options("PK Yatra Batch", txt),
    },
    {
      fieldname: "show",
      label: __("Show"),
      fieldtype: "Select",
      options: ["Yatra", "Yatra and Batch", "Yatra, Batch and Account"],
      default: "Yatra and Batch",
      reqd: 1,
    },
    {
      fieldname: "include_untagged",
      label: __("Include Entries without a Yatra"),
      fieldtype: "Check",
      default: 1,
    },
  ],
  tree: true,
  name_field: "name",
  parent_field: "parent",
  initial_depth: 1,

  formatter: function (value, row, column, data, default_formatter) {
    value = default_formatter(value, row, column, data);
    if (!data) return value;

    if (column.fieldname === "label" && data.drill_down) {
      const args = JSON.stringify({
        account: data.account,
        yatra: data.yatra,
        batch: data.batch,
      }).replace(/"/g, "&quot;");
      value = `<a onclick="frappe.query_reports['Yatra Wise Income and Expenditure'].open_general_ledger(${args})">${value}</a>`;
    }
    if (["surplus", "margin"].includes(column.fieldname) && data[column.fieldname] < 0) {
      value = `<span class="text-danger">${value}</span>`;
    }
    if (data.indent === 0) {
      value = `<b>${value}</b>`;
    }
    return value;
  },

  open_general_ledger: function (data) {
    frappe.route_options = {
      company: frappe.query_report.get_filter_value("company"),
      from_date: frappe.query_report.get_filter_value("from_date"),
      to_date: frappe.query_report.get_filter_value("to_date"),
      account: [data.account],
      pk_yatra: [data.yatra],
      pk_yatra_batch: [data.batch],
    };
    frappe.set_route("query-report", "General Ledger");
  },
};
