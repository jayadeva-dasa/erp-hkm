// Copyright (c) 2025, Narahari Dasa and contributors
// For license information, please see license.txt

frappe.query_reports["HKM Eagle View"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Select",
			options: [],
			reqd: 0,
		},

		{
			fieldname: "report_view",
			label: __("Report View"),
			fieldtype: "Select",
			options: ["Dimension View", "Account View", "Voucher View"],
			default: "Dimension View",
			reqd: 1,
			on_change: function (report) {
				const report_view = report.get_filter_value("report_view");
				const time_period_filter = report.get_filter("time_period");
				const report_type_filter = report.get_filter("report_type");
				const include_disabled_filter = report.get_filter("include_disabled_dimension");
				const hide_not_tagged_filter = report.get_filter("hide_not_tagged_entries");
				const render_as_tree_view_filter = report.get_filter("render_as_tree_view");

				if (report_view === "Voucher View") {
					// Hide time period filter
					if (time_period_filter) {
						time_period_filter.df.hidden = 1;
						time_period_filter.refresh();
					}

					// Change report type options for Voucher Wise
					if (report_type_filter) {
						report_type_filter.df.options = ["Detailed Income", "Detailed Expense"];
						report_type_filter.df.default = "Detailed Income";
						report_type_filter.set_value("Detailed Income");
						report_type_filter.refresh();
					}

					// Hide include disabled dimension filter for Voucher View
					if (include_disabled_filter) {
						include_disabled_filter.df.hidden = 1;
						include_disabled_filter.set_value(0);
						include_disabled_filter.refresh();
					}

					// Show hide_not_tagged_entries filter for Voucher View
					if (hide_not_tagged_filter) {
						hide_not_tagged_filter.df.hidden = 0;
						hide_not_tagged_filter.set_value(1);
						hide_not_tagged_filter.refresh();
					}

					// Hide render_as_tree_view filter for Voucher View
					if (render_as_tree_view_filter) {
						render_as_tree_view_filter.df.hidden = 1;
						render_as_tree_view_filter.refresh();
					}
				} else if (report_view === "Dimension View") {
					// Show time period filter for Dimension View
					if (time_period_filter) {
						time_period_filter.df.hidden = 0;
						time_period_filter.refresh();
					}

					// Restore original report type options
					if (report_type_filter) {
						report_type_filter.df.options = ["Both Income and Expenses", "Only Incomes", "Only Expense", "Net Profit"];
						report_type_filter.df.default = "Both Income and Expenses";
						report_type_filter.set_value("Both Income and Expenses");
						report_type_filter.refresh();
					}

					// Show include disabled dimension filter for Dimension View
					if (include_disabled_filter) {
						include_disabled_filter.df.hidden = 0;
						include_disabled_filter.refresh();
					}

					// Hide hide_not_tagged_entries filter for Dimension View
					if (hide_not_tagged_filter) {
						hide_not_tagged_filter.df.hidden = 1;
						hide_not_tagged_filter.set_value(0);
						hide_not_tagged_filter.refresh();
					}

					// Show render_as_tree_view filter for Dimension View (will be controlled by dimension type)
					if (render_as_tree_view_filter) {
						// Check if current dimension has tree type
						const selected_dimension = report.get_filter_value("dimension") || "Cost Head";
						frappe.model.with_doctype(selected_dimension).then(() => {
							const dimension_meta = frappe.get_meta(selected_dimension);
							if (dimension_meta.is_tree) {
								render_as_tree_view_filter.df.hidden = 0;
								render_as_tree_view_filter.refresh();
							} else {
								render_as_tree_view_filter.df.hidden = 1;
								render_as_tree_view_filter.refresh();
							}
						});
					}
				} else {
					// Account View - show time period filter but hide include disabled dimension
					if (time_period_filter) {
						time_period_filter.df.hidden = 0;
						time_period_filter.refresh();
					}

					// Restore original report type options
					if (report_type_filter) {
						report_type_filter.df.options = ["Both Income and Expenses", "Only Incomes", "Only Expense", "Net Profit"];
						report_type_filter.df.default = "Both Income and Expenses";
						report_type_filter.set_value("Both Income and Expenses");
						report_type_filter.refresh();
					}

					// Hide include disabled dimension filter for Account View
					if (include_disabled_filter) {
						include_disabled_filter.df.hidden = 1;
						include_disabled_filter.set_value(0);
						include_disabled_filter.refresh();
					}

					// Hide hide_not_tagged_entries filter for Account View
					if (hide_not_tagged_filter) {
						hide_not_tagged_filter.df.hidden = 1;
						hide_not_tagged_filter.set_value(1);
						hide_not_tagged_filter.refresh();
					}

					// Hide render_as_tree_view filter for Account View
					if (render_as_tree_view_filter) {
						render_as_tree_view_filter.df.hidden = 1;
						render_as_tree_view_filter.refresh();
					}
				}
				frappe.query_report.refresh();
			},
		},
		{
			fieldname: "time_period",
			label: __("Time Period"),
			fieldtype: "Select",
			options: ["Cumulative", "Day Wise", "Week Wise", "Quarter Wise", "Month Wise"],
			default: "Cumulative",
			reqd: 1,
		},
		{
			fieldname: "report_type",
			label: __("Report Type"),
			fieldtype: "Select",
			options: ["Both Income and Expenses", "Only Incomes", "Only Expense", "Net Profit"],
			default: "Both Income and Expenses",
			reqd: 1,
		},
		{
			fieldname: "dimension",
			label: __("Select Dimension"),
			fieldtype: "Select",
			default: "Cost Head",
			options: ["Cost Head", "Cost Center", "Project"],
			reqd: 1,
			on_change: function (report) {
				const dimension_value_filter = report.get_filter("dimension_value");
				const include_disabled_filter = report.get_filter("include_disabled_dimension");

				// --- Restrict dimension filter based on user role ---
				const user_roles = frappe.user_roles;
				if (
					!(
						user_roles.includes("Accounts Manager") ||
						user_roles.includes("Accounts User") ||
						user_roles.includes("Accounts Admin")
					)
				) {
					// If not admin → force "Cost Head"
					const dim_filter = report.get_filter("dimension");
					dim_filter.df.options = ["Cost Head"]; // only one option
					dim_filter.set_value("Cost Head");
					dim_filter.df.read_only = 1; // prevent user from changing
					dim_filter.refresh();
				}

				if (dimension_value_filter) {
					dimension_value_filter.set_value([]);
					dimension_value_filter.refresh();
					dimension_value_filter.get_data();
				}

				const selected_dimension = report.get_filter_value("dimension") || "Cost Head";
				frappe.model.with_doctype(selected_dimension).then(() => {
					const has_disabled = frappe.meta.has_field(selected_dimension, "disabled");
					const has_enabled = frappe.meta.has_field(selected_dimension, "enabled");

					if (include_disabled_filter) {
						if (has_disabled) {
							include_disabled_filter.df.hidden = 0;
							include_disabled_filter.df.label = __("Include Disabled {0}'s", [selected_dimension]);
							include_disabled_filter.refresh();
						} else if (has_enabled) {
							include_disabled_filter.df.hidden = 0;
							include_disabled_filter.df.label = __("Include Disabled {0}'s", [selected_dimension]);
							include_disabled_filter.refresh();

							frappe.call({
								method: "hkm.erpnext___custom.report.hkm_eagle_view.hkm_eagle_view.get_disabled_dimension_values",
								args: {
									dimension: selected_dimension
								}
							}).then((result) => {
								const disabled_records = result.message || [];
								include_disabled_filter.set_value(0);
								include_disabled_filter.refresh();
							});
						} else {
							include_disabled_filter.df.hidden = 1;
							include_disabled_filter.set_value(0);
							include_disabled_filter.refresh();
						}
					}
				});

				// Handle render_as_tree_view filter visibility based on dimension type and report view
				const render_as_tree_view_filter = report.get_filter("render_as_tree_view");
				const report_view = report.get_filter_value("report_view");
				
				if (render_as_tree_view_filter && report_view === "Dimension View") {
					frappe.model.with_doctype(selected_dimension).then(() => {
						const dimension_meta = frappe.get_meta(selected_dimension);
						if (dimension_meta.is_tree) {
							render_as_tree_view_filter.df.hidden = 0;
							render_as_tree_view_filter.refresh();
						} else {
							render_as_tree_view_filter.df.hidden = 1;
							render_as_tree_view_filter.refresh();
						}
					});
				} else if (render_as_tree_view_filter) {
					// Hide for non-Dimension View
					render_as_tree_view_filter.df.hidden = 1;
					render_as_tree_view_filter.refresh();
				}

				frappe.query_report.refresh();
			},
		},

		{
			fieldname: "dimension_value",
			label: __("Select Value"),
			fieldtype: "MultiSelectList",
			reqd: 0,
			get_data: async function (txt) {
				const dimension = frappe.query_report.get_filter_value("dimension") || "Cost Head";
				// const dimension_value = txt.get_filter("dimension_value");
				try {
					await frappe.model.with_doctype(dimension);
					const has_disabled = frappe.meta.has_field(dimension, "disabled");
					const has_enabled = frappe.meta.has_field(dimension, "enabled");

					let filters = {};
					if (has_disabled) {
						filters = { disabled: 0 };
					} else if (has_enabled) {
						filters = { enabled: 1 };
					}

					const user_roles = frappe.user_roles;

					if (dimension === "Cost Head" && !(
						user_roles.includes("Accounts Manager") ||
						user_roles.includes("Accounts User") ||
						user_roles.includes("Accounts Admin")
					)) {
						const res = await frappe.call({
							method: "hkm.erpnext___custom.report.hkm_eagle_view.hkm_eagle_view.get_cost_head_values",
						});




						return (res && res.message) || [];



					}




					return await frappe.db.get_link_options(dimension, txt, filters);
				} catch (error) {
					frappe.msgprint({
						title: __("Error"),
						indicator: "red",
						message: __("Could not fetch values for dimension: {0}", [dimension]),
					});
					return [];
				}
			},
		},
		{
			fieldname: "account",
			label: __("Account"),
			fieldtype: "MultiSelectList",
			options: "Account",
			reqd: 0,
			get_data: async function (txt) {
				try {
					return await frappe.db.get_link_options("Account", txt, {});
				} catch (error) {
					frappe.msgprint({
						title: __("Error"),
						indicator: "red",
						message: __("Could not fetch account options"),
					});
					return [];
				}
			},
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: erpnext.utils.get_fiscal_year(frappe.datetime.get_today(), true)[1],
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: erpnext.utils.get_fiscal_year(frappe.datetime.get_today(), true)[2],
			reqd: 1,
		},
		{
			fieldname: "include_adjustment",
			label: __("Include Adjustment"),
			fieldtype: "Check",
			default: 1,
			reqd: 0,
			on_change: async function (report) {
				const include_adjustment = report.get_filter_value("include_adjustment");
				const adjustment_type_filter = report.get_filter("internal_adjustment_type");
				if (adjustment_type_filter) {
					if (include_adjustment) {
						// Show the filter without pre-selecting all types
						adjustment_type_filter.df.hidden = 0;
						adjustment_type_filter.refresh();
					} else {
						// Hide the filter and clear its value
						adjustment_type_filter.df.hidden = 1;
						adjustment_type_filter.set_value([]);
						adjustment_type_filter.refresh();
					}
				}
				frappe.query_report.refresh();
			},
		},
		{
			fieldname: "internal_adjustment_type",
			label: __("Internal Adjustment Type"),
			fieldtype: "MultiSelectList",
			options: "Internal Adjustment Type",
			reqd: 0,
			hidden: 1,
			get_data: async function (txt) {
				try {
					return await frappe.db.get_link_options("Internal Adjustment Type", txt, {});
				} catch (error) {
					frappe.msgprint({
						title: __("Error"),
						indicator: "red",
						message: __("Could not fetch internal adjustment type options"),
					});
					return [];
				}
			},
		},
		{
			fieldname: "include_stock_asset",
			label: __("Include Stock & Asset Expenses"),
			fieldtype: "Check",
			default: 1,
			reqd: 0,
		},
		{
			fieldname: "include_disabled_dimension",
			label: __("Include Disabled Dimension"),
			fieldtype: "Check",
			default: 0,
			reqd: 0,
			hidden: 1,
		},
		{
			fieldname: "hide_not_tagged_entries",
			label: __("Hide Not Tagged Entries"),
			fieldtype: "Check",
			default: 0,
			reqd: 0,
			hidden: 1,
		},
		{
			fieldname: "exclude_period_closing_entries",
			label: __("Exclude Period Closing Entries"),
			fieldtype: "Check",
			default: 1,
			reqd: 0,

		},
		{
			fieldname: "render_as_tree_view",
			label: __("Render as Tree View"),
			fieldtype: "Check",
			default: 1,
			reqd: 0,
			hidden: 1,
		}
	],

	onload: async function (report) {
		enforce_dimension_restriction(report);

		await _loadAccountingDimensions(report);
		await _loadCompanyOptions(report);
		_applySmartDisabledBehavior(report);

		// Use setTimeout to ensure filters are fully initialized and values are restored
		setTimeout(() => {
			// Get the actual saved report view value from the filter
			const report_view_filter = report.get_filter("report_view");
			const report_view = report_view_filter ? report_view_filter.get_value() : "Dimension View";


			const include_disabled_filter = report.get_filter("include_disabled_dimension");
			const hide_not_tagged_filter = report.get_filter("hide_not_tagged_entries");
			const report_type_filter = report.get_filter("report_type");



			// Set report type filter options based on current report view
			if (report_type_filter) {
				// Get the current value before changing options
				const current_report_type_value = report_type_filter.get_value();

				// Update options based on report view but preserve current value if compatible
				if (report_view === "Voucher View") {
					const voucher_options = ["Detailed Income", "Detailed Expense"];
					report_type_filter.df.options = voucher_options;

					// Only set default value if current value is empty or not compatible
					if (!current_report_type_value || !voucher_options.includes(current_report_type_value)) {
						report_type_filter.df.default = "Detailed Income";
						report_type_filter.set_value("Detailed Income");
					}
				} else {
					const standard_options = ["Both Income and Expenses", "Only Incomes", "Only Expense", "Net Profit"];
					report_type_filter.df.options = standard_options;

					// Only set default value if current value is empty or not compatible
					if (!current_report_type_value || !standard_options.includes(current_report_type_value)) {
						report_type_filter.df.default = "Both Income and Expenses";
						report_type_filter.set_value("Both Income and Expenses");
					}
				}

				// Refresh the filter
				report_type_filter.refresh();
			}

			if (include_disabled_filter) {
				if (report_view === "Dimension View") {
					include_disabled_filter.df.hidden = 0;
				} else {
					include_disabled_filter.df.hidden = 1;
					include_disabled_filter.set_value(0);
				}
				include_disabled_filter.refresh();
			}

			if (hide_not_tagged_filter) {
				if (report_view === "Voucher View") {
					hide_not_tagged_filter.df.hidden = 0;
					hide_not_tagged_filter.set_value(1);
				} else {
					hide_not_tagged_filter.df.hidden = 1;
					hide_not_tagged_filter.set_value(0);
				}
				hide_not_tagged_filter.refresh();
			}

			// Handle render_as_tree_view filter visibility
			const render_as_tree_view_filter = report.get_filter("render_as_tree_view");
			if (render_as_tree_view_filter) {
				if (report_view === "Dimension View") {
					// Check if current dimension has tree type
					const selected_dimension = report.get_filter_value("dimension") || "Cost Head";
					frappe.model.with_doctype(selected_dimension).then(() => {
						const dimension_meta = frappe.get_meta(selected_dimension);
						if (dimension_meta.is_tree) {
							render_as_tree_view_filter.df.hidden = 0;
							render_as_tree_view_filter.refresh();
						} else {
							render_as_tree_view_filter.df.hidden = 1;
							render_as_tree_view_filter.refresh();
						}
					});
				} else {
					// Hide for non-Dimension View
					render_as_tree_view_filter.df.hidden = 1;
					render_as_tree_view_filter.refresh();
				}
			}
		}, 200); // Increased timeout to ensure filters are fully loaded
	},
};

async function _loadAccountingDimensions(report) {
	try {
		const res = await frappe.db.get_list("Accounting Dimension", {
			fields: ["label", "document_type"],
			limit: 100,
		});

		const base_options = ["Cost Head", "Cost Center", "Project"];
		const extra = res
			.map((d) => d.document_type)
			.filter((d) => !base_options.includes(d));
		const final_options = [...base_options, ...extra];

		const dimension_filter = report.get_filter("dimension");
		if (dimension_filter) {
			dimension_filter.df.options = final_options;
			dimension_filter.refresh();

			// Reset dimension_value filter on load
			const dimension_value_filter = report.get_filter("dimension_value");
			if (dimension_value_filter) {
				dimension_value_filter.set_value([]);
				dimension_value_filter.refresh();
				dimension_value_filter.get_data();
			}
		}
	} catch (error) {
		frappe.msgprint({
			title: __("Error"),
			indicator: "red",
			message: __("Could not fetch accounting dimensions"),
		});
	}
}

function _applySmartDisabledBehavior(report) {
	const include_disabled_filter = report.get_filter("include_disabled_dimension");
	const selected_dimension = report.get_filter_value("dimension") || "Cost Head";


	frappe.model.with_doctype(selected_dimension).then(() => {
		const has_disabled = frappe.meta.has_field(selected_dimension, "disabled");
		const has_enabled = frappe.meta.has_field(selected_dimension, "enabled");

		if (include_disabled_filter) {
			if (has_disabled) {
				// Dimension has disabled field - show the filter and update label
				include_disabled_filter.df.hidden = 0;
				include_disabled_filter.df.label = __("Include Disabled {0}'s", [selected_dimension]);
				include_disabled_filter.refresh();
			} else if (has_enabled) {
				// Dimension has enabled field - show the filter and update label
				include_disabled_filter.df.hidden = 0;
				include_disabled_filter.df.label = __("Include Disabled {0}'s", [selected_dimension]);
				include_disabled_filter.refresh();

				// Check if any disabled records exist
				frappe.call({
					method: "hkm.erpnext___custom.report.hkm_eagle_view.hkm_eagle_view.get_disabled_dimension_values",
					args: {
						dimension: selected_dimension
					}
				}).then((result) => {
					const disabled_records = result.message || [];
					if (disabled_records && disabled_records.length > 0) {
						// Disabled values exist - keep include_disabled_dimension unchecked by default
						include_disabled_filter.set_value(0);
						include_disabled_filter.refresh();
					} else {
						// No disabled values exist - keep include_disabled_dimension unchecked (default)
						include_disabled_filter.set_value(0);
						include_disabled_filter.refresh();
					}
				});
			} else {
				// Dimension doesn't have disabled field - hide the filter completely
				include_disabled_filter.df.hidden = 1;
				include_disabled_filter.set_value(0);
				include_disabled_filter.refresh();
			}
		} else {
		}
	});
}



function enforce_dimension_restriction(report) {
	const user_roles = frappe.user_roles;
	const dim_filter = report.get_filter("dimension");

	if (
		!(
			user_roles.includes("Accounts Manager") ||
			user_roles.includes("Accounts User") ||
			user_roles.includes("Accounts Admin")
		)
	) {
		dim_filter.df.options = ["Cost Head"];   // only allow Cost Head
		dim_filter.set_value("Cost Head");
		dim_filter.df.read_only = 1;             // lock it
		dim_filter.refresh();
	}
}

async function _loadCompanyOptions(report) {
	try {
		const companies = await frappe.db.get_list("Company", {
			fields: ["name"],
			limit: 100
		});
		const company_options = ["", ...companies.map(company => company.name)];

		const company_filter = report.get_filter("company");
		if (company_filter) {
			company_filter.df.options = company_options;
			company_filter.refresh();
		}
	} catch (error) {
		frappe.msgprint({
			title: __("Error"),
			indicator: "red",
			message: __("Could not fetch company options"),
		});
	}
}



