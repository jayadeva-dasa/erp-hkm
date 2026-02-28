import frappe
from frappe import _
from .constants import (
    REPORT_TYPE,
    REPORT_VIEW,
    DIMENSION_VIEW,
    ACCOUNT_VIEW,
    SUMMARY,
    ONLY_INCOME,
    ONLY_EXPENSE,
    NET_PROFIT,
    TIME_PERIOD,
    CUMULATIVE,
    MONTH_WISE,
    QUARTER_WISE,
    DAY_WISE,
    WEEK_WISE,
    VOUCHER_VIEW,
    INCLUDE_ADJUSTMENT,
    INTERNAL_ADJUSTMENT_TYPE,
    FROM_DATE,
    TO_DATE,
)
from .date_utils import (
    get_monthly_ranges,
    get_fiscal_quarters,
    get_weekly_ranges,
    get_daywise_dates,
)


class ColumnBuilder:
    def __init__(self, filters):
        self.filters = filters
        self.columns = []

    def get_columns(self):
        if not self.filters.get(REPORT_VIEW) == VOUCHER_VIEW:
            self.columns = MainColumnBuilder(self.filters).get_columns()
        else:
            self.columns = VoucherColumnBuilder(self.filters).get_columns()
        return self.columns


class MainColumnBuilder:
    def __init__(self, filters):
        self.filters = filters
        self.columns = []
        self._initialize_settings()

    def _initialize_settings(self):
        """Initialize column builder settings"""
        self.dimension_meta = frappe.get_meta(self.filters.get("dimension"))

        # Get the correct fieldname from Accounting Dimension doctype
        dimension_doctype = self.filters.get("dimension")
        self.dimension = frappe.db.get_value(
            "Accounting Dimension", {"document_type": dimension_doctype}, "fieldname"
        )
        if not self.dimension:
            # Fallback to scrubbed name if not found in Accounting Dimension
            self.dimension = frappe.scrub(dimension_doctype)
        self.report_type = self.filters.get(REPORT_TYPE)
        self.include_adjustment = self._get_boolean_value(INCLUDE_ADJUSTMENT)
        self.internal_adjustment_type = self.filters.get(INTERNAL_ADJUSTMENT_TYPE)
        self.from_date = self.filters.get(FROM_DATE)
        self.to_date = self.filters.get(TO_DATE)

    def _get_boolean_value(self, key):
        """Convert checkbox value to boolean"""
        value = self.filters.get(key)
        return bool(value) if value is not None else False

    def get_columns(self):
        """Get columns based on time period"""
        self._build_base_columns()

        time_period = self.filters.get(TIME_PERIOD)
        if time_period == CUMULATIVE:
            self._build_cumulative_columns()
        else:
            self._build_time_based_columns(time_period)

        return self.columns

    def _build_time_based_columns(self, time_period):
        """Build columns for time-based reports"""
        period_map = {
            DAY_WISE: get_daywise_dates,
            WEEK_WISE: get_weekly_ranges,
            QUARTER_WISE: get_fiscal_quarters,
            MONTH_WISE: get_monthly_ranges,
        }

        if time_period in period_map:
            periods = period_map[time_period](self.from_date, self.to_date)
            self._build_period_columns(periods)

    def _build_period_columns(self, periods):
        """Build columns for specific periods"""
        self._add_total_columns()

        for period in periods:
            self._add_period_columns(period)

    def _add_total_columns(self):
        """Add total columns based on report type"""
        total_columns = {
            SUMMARY: [
                {"fieldname": "total_inc", "label": _("Total Income")},
                {"fieldname": "total_exp", "label": _("Total Expense")},
            ],
            ONLY_INCOME: [{"fieldname": "total_inc", "label": _("Total Income")}],
            ONLY_EXPENSE: [{"fieldname": "total_exp", "label": _("Total Expense")}],
            NET_PROFIT: [{"fieldname": "total_net", "label": _("Total Net Profit")}],
        }

        columns = total_columns.get(self.report_type, [])
        for col in columns:
            col.update({"fieldtype": "Currency", "width": 150})
            self.columns.extend([col])

    def _add_period_columns(self, period):
        """Add columns for a specific period"""
        if self.report_type in [SUMMARY, ONLY_INCOME]:
            self._add_income_columns(period)
        if self.report_type in [SUMMARY, ONLY_EXPENSE]:
            self._add_expense_columns(period)
        if self.report_type == NET_PROFIT:
            self._add_net_columns(period)

    def _add_income_columns(self, period):
        """Add income columns for a period"""
        label = period.label
        if self.include_adjustment and self.report_type == ONLY_INCOME:
            label += " (Main)"

        if self.report_type == SUMMARY:
            label += " (Inc.)"
        self.columns.extend(
            [
                {
                    "fieldname": period.key + "_inc",
                    "label": label,
                    "fieldtype": "Currency",
                    "width": 150,
                }
            ]
        )

        if self.include_adjustment and self.report_type == ONLY_INCOME:
            self._add_adjustment_columns(period, "inc")

    def _add_expense_columns(self, period):
        """Add expense columns for a period"""
        label = period.label
        if self.include_adjustment and self.report_type == ONLY_EXPENSE:
            label += " (Main)"

        if self.report_type == SUMMARY:
            label += " (Exp.)"
        self.columns.extend(
            [
                {
                    "fieldname": period.key + "_exp",
                    "label": label,
                    "fieldtype": "Currency",
                    "width": 150,
                }
            ]
        )

        if self.include_adjustment and self.report_type == ONLY_EXPENSE:
            self._add_adjustment_columns(period, "exp")

    def _add_net_columns(self, period):
        """Add net profit columns for a period"""
        self.columns.extend(
            [
                {
                    "fieldname": period.key + "_net",
                    "label": period.label,
                    "fieldtype": "Currency",
                    "width": 150,
                }
            ]
        )

    def _add_adjustment_columns(self, period, column_type):
        """Add adjustment columns for a period"""
        adj_types = self._get_adjustment_types()

        for adj_type in adj_types:
            self.columns.extend(
                [
                    {
                        "fieldname": f"{period.key}_{frappe.scrub(adj_type)}_{column_type}_adj",
                        "label": f"{period.label} ({adj_type})",
                        "fieldtype": "Currency",
                        "options": "Currency",
                        "precision": 0,
                        "width": 150,
                    }
                ]
            )

    def _get_adjustment_types(self):
        """Get adjustment types for columns"""
        if not self.internal_adjustment_type:
            adj_types = frappe.get_all("Internal Adjustment Type", pluck="name")
            return adj_types
        return self.internal_adjustment_type

    def _build_cumulative_columns(self):
        """Build columns for cumulative report"""
        self._add_total_columns()
        self._build_adjustment_columns()

    def _build_adjustment_columns(self):
        """Build adjustment columns"""
        adj_types = self._get_adjustment_types()

        if (
            self.include_adjustment
            and self.report_type in [ONLY_INCOME, ONLY_EXPENSE]
            and self.filters.get(REPORT_VIEW) == DIMENSION_VIEW
            and self.filters.get(TIME_PERIOD) == CUMULATIVE
            and adj_types
        ):
            self.columns.extend(
                [
                    {
                        "fieldname": "total_main",
                        "label": "Total (Main)",
                        "fieldtype": "Currency",
                        "options": "Currency",
                        "precision": 0,
                        "width": 150,
                    }
                ]
            )

            for adj_type in adj_types:
                column_key = frappe.scrub(adj_type)
                self.columns.extend(
                    [
                        {
                            "fieldname": f"total_{column_key}_adj",
                            "label": f"Total ({adj_type})",
                            "fieldtype": "Currency",
                            "options": "Currency",
                            "precision": 0,
                            "width": 150,
                        }
                    ]
                )

    def _build_base_columns(self):
        """Build base columns"""
        if self.filters.get(REPORT_VIEW) == DIMENSION_VIEW:
            self.columns = [
                {
                    "fieldname": "name",
                    "label": _(self.dimension_meta.name),
                    "fieldtype": "Link",
                    "options": self.dimension_meta.name,
                    "width": 300,
                },
            ]
        else:
            self.columns = [
                {
                    "fieldname": "account",
                    "label": _("Account"),
                    "fieldtype": "Link",
                    "options": "Account",
                    "width": 300,
                },
            ]


class VoucherColumnBuilder:
    def __init__(self, filters):
        self.filters = filters
        self.columns = []
        self.dimension_meta = frappe.get_meta(self.filters.get("dimension"))

        # Get the correct fieldname from Accounting Dimension doctype
        dimension_doctype = self.filters.get("dimension")
        self.dimension = frappe.db.get_value(
            "Accounting Dimension", {"document_type": dimension_doctype}, "fieldname"
        )
        if not self.dimension:
            # Fallback to scrubbed name if not found in Accounting Dimension
            self.dimension = frappe.scrub(dimension_doctype)
        self.accounting_dimension = frappe.get_all(
            "Accounting Dimension",
            filters={"document_type": ["!=", self.dimension_meta.name]},
            pluck="fieldname",
        )

    def get_columns(self):
        """Get voucher columns"""
        self.columns = [
            {
                "fieldname": "posting_date",
                "label": _("Date"),
                "fieldtype": "Date",
                "width": 150,
            },
            {
                "fieldname": "company",
                "label": _("Company"),
                "fieldtype": "Data",
                "width": 150,
            },
            {
                "fieldname": "voucher_type",
                "label": _("Voucher Type"),
                "fieldtype": "Data",
                "width": 150,
            },
            {
                "fieldname": "voucher_no",
                "label": _("Voucher No"),
                "fieldtype": "HTML",
                "width": 150,
            },
            {
                "fieldname": self.dimension,
                "label": _(self.dimension_meta.name),
                "fieldtype": "Link",
                "options": self.dimension_meta.name,
                "width": 80,
            },
        ]
        for i in self.accounting_dimension:
            self.columns.append(
                {
                    "fieldname": i,
                    "label": _(i),
                    "fieldtype": "Link",
                    "options": "Accounting Dimension",
                    "width": 80,
                }
            )

        self.columns.extend(
            [
                {
                    "fieldname": "account_head",
                    "label": _("Account Head"),
                    "fieldtype": "Link",
                    "options": "Account",
                    "width": 180,
                },
                {
                    "fieldname": "amount",
                    "label": _("Amount"),
                    "fieldtype": "Currency",
                    "width": 130,
                },
                {
                    "fieldname": "remarks",
                    "label": _("Remarks"),
                    "fieldtype": "Data",
                    "width": 150,
                },
                {
                    "fieldname": "files_html",
                    "label": _("Attachments"),
                    "fieldtype": "HTML",
                    "width": 300,
                },
            ]
        )
        return self.columns
