# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import data
from frappe.utils.jinja import set_filters
from hkm.erpnext___custom.report.hkm_eagle_view.utils.columns_builder import (
    ColumnBuilder,
)
from hkm.erpnext___custom.report.hkm_eagle_view.utils.base_report import BaseReport
from hkm.erpnext___custom.report.hkm_eagle_view.report.account_wise_report.cummulative import (
    AccountCummulative,
)
from hkm.erpnext___custom.report.hkm_eagle_view.report.account_wise_report.day_wise import (
    AccountDayWise,
)
from hkm.erpnext___custom.report.hkm_eagle_view.report.account_wise_report.week_wise import (
    AccountWeekWise,
)
from hkm.erpnext___custom.report.hkm_eagle_view.report.account_wise_report.quarters_wise import (
    AccountQuarterWise,
)
from hkm.erpnext___custom.report.hkm_eagle_view.report.account_wise_report.month_wise import (
    AccountMonthWise,
)
from hkm.erpnext___custom.report.hkm_eagle_view.utils.constants import (
    ACCOUNT_VIEW,
    CUMULATIVE,
    REPORT_VIEW,
    TIME_PERIOD,
    DAY_WISE,
    WEEK_WISE,
    QUARTER_WISE,
    MONTH_WISE,
    DIMENSION_VIEW,
    VOUCHER_VIEW,
    ALL_ACCESS_ROLE,
)
from hkm.erpnext___custom.report.hkm_eagle_view.report.dimension_wise_report.cummulative import (
    DimensionCummulative,
)

from hkm.erpnext___custom.report.hkm_eagle_view.report.dimension_wise_report.month_wise import (
    DimensionMonthWise,
)
from hkm.erpnext___custom.report.hkm_eagle_view.report.dimension_wise_report.time_based_report import (
    TimeBasedReport,
)
from hkm.erpnext___custom.report.hkm_eagle_view.report.dimension_wise_report.quarters_wise import (
    DimensionQuarterWise,
)
from hkm.erpnext___custom.report.hkm_eagle_view.report.dimension_wise_report.week_wise import (
    DimensionWeekWise,
)
from hkm.erpnext___custom.report.hkm_eagle_view.report.dimension_wise_report.day_wise import (
    DimensionDayWise,
)
from hkm.erpnext___custom.report.hkm_eagle_view.report.voucher_wise_report.main import (
    VoucherWise,
)

from hkm.erpnext___custom.report.hkm_eagle_view.utils.dimension_utils import get_heads


# apps/hkm/hkm/erpnext___custom/report/hkm_eagle_view/hkm_eagle_view.py
def test():
    filters = {
        "report_view": "Dimension View",
        "time_period": "Cumulative",
        "report_type": "Both Income and Expenses",
        "dimension": "Cost Head",
        "dimension_value": [],
        "from_date": "2025-01-01",
        "to_date": "2025-12-31",
    }
    args, a = execute(filters)
    print(a)


class HKM_MASTER_REPORT(BaseReport):
    def __init__(self, filters):
        super().__init__(filters)
        self.data = []
        self._initialize_report_handlers()

    def _initialize_report_handlers(self):
        """Initialize report handlers for different time periods"""
        self.account_report_handlers = {
            CUMULATIVE: AccountCummulative,
            DAY_WISE: AccountDayWise,
            WEEK_WISE: AccountWeekWise,
            QUARTER_WISE: AccountQuarterWise,
            MONTH_WISE: AccountMonthWise,
        }

        self.dimension_report_handlers = {
            CUMULATIVE: DimensionCummulative,
            MONTH_WISE: DimensionMonthWise,
            QUARTER_WISE: DimensionQuarterWise,
            WEEK_WISE: DimensionWeekWise,
            DAY_WISE: DimensionDayWise,
        }

    def load_data(self):

        user_roles = frappe.get_roles(frappe.session.user)
        have_role = any(role in ALL_ACCESS_ROLE for role in user_roles)

        if not have_role and self.filters.get("dimension") != "Cost Head":
            frappe.throw("Please select Cost Head")

        """Load data from database based on filters"""
        if self.filters.get(REPORT_VIEW) == DIMENSION_VIEW:
            time_period = self.filters.get(TIME_PERIOD)
            handler_class = self.dimension_report_handlers.get(time_period)
            if handler_class:
                self.data = handler_class(self.filters).get_data()
            else:
                frappe.throw(f"Unsupported time period: {time_period}")
        if self.filters.get(REPORT_VIEW) == ACCOUNT_VIEW:
            time_period = self.filters.get(TIME_PERIOD)
            handler_class = self.account_report_handlers.get(time_period)
            if handler_class:
                self.data = handler_class(self.filters).get_data()
            else:
                frappe.throw(f"Unsupported time period: {time_period}")
        if self.filters.get(REPORT_VIEW) == VOUCHER_VIEW:
            self.data = VoucherWise(self.filters).get_data()

        return self.data

    def get_data(self):
        """Get data for the report"""
        return self.load_data()


def execute(filters=None):

    # filters = set_filters_value(filters)
    """Main entry point for the report"""
    columns = ColumnBuilder(filters).get_columns()
    data = HKM_MASTER_REPORT(filters).get_data()

    return columns, data


# def set_filters_value(filters):
#     dimension_meta = frappe.get_meta(filters.get("dimension"))
#     if dimension_meta.name == "Cost Head" and not any(
#         role in frappe.get_roles(frappe.session.user)
#         for role in [ALL_ACCESS_ROLE, "System Manager"]
#     ):

#         filters["dimension_value"] = allowed_heads()
#         return filters
#     return filters


@frappe.whitelist()
def get_disabled_dimension_values(dimension):
    """Get disabled dimension values"""
    dimension_meta = frappe.get_meta(dimension)

    if dimension_meta.has_field("disabled"):
        return frappe.get_all(dimension, filters={"disabled": 1}, pluck="name")
    elif dimension_meta.has_field("enabled"):
        return frappe.get_all(dimension, filters={"enabled": 0}, pluck="name")
    else:
        # If neither disabled nor enabled field exists, return empty list
        return []


@frappe.whitelist()
def get_cost_head_values():
    user = frappe.session.user

    # Get all Cost Heads linked to user
    cost_heads = frappe.db.sql_list(
        """
        SELECT ch.name
        FROM `tabCost Head` ch
        JOIN `tabCost Head Concerned Person` c ON ch.name = c.parent
        WHERE c.user = %s AND ch.disabled = 0
        """,
        (user,),
    )

    if not cost_heads:
        return []

    dimension_meta = frappe.get_meta("Cost Head")
    all_heads = []

    for c in cost_heads:
        child_nodes = get_heads(dimension_meta, c, detailed=False)
        if child_nodes:
            all_heads.extend(child_nodes)

    if not all_heads:
        frappe.throw("No Cost Heads found for user")

    data = [
        {
            "value": h,
            "description": h,
        }
        for h in all_heads
    ]

    return data


def allowed_heads():
    user = frappe.session.user

    # Get all Cost Heads linked to user
    cost_heads = frappe.db.sql_list(
        """
        SELECT ch.name
        FROM `tabCost Head` ch
        JOIN `tabCost Head Concerned Person` c ON ch.name = c.parent
        WHERE c.user = %s AND ch.disabled = 0
        LIMIT 1
        """,
        (user,),
    )

    if not cost_heads:
        return []
    return cost_heads[0] if cost_heads else None




def log_sql_query():


    dimension = "FOLK Residency"
    dimension_value = ["FOLK Keshav Niwas-Jaipur"]
    from_date = "2025-04-01"
    to_date = "2026-03-31"
    dimension_view_filters = {
            "from_date": from_date,
            "to_date": to_date,
            "report_view": "Dimension View",
            "time_period": "Cumulative",
            "report_type": "Net Profit",
            "dimension": dimension,
            "dimension_value": dimension_value,
            "include_adjustment": 1,
            "include_stock_asset": 1,
            "include_disabled_dimension": 0,
            "exclude_period_closing_entries": 0,
        }

    dimension_view_data = HKM_MASTER_REPORT(dimension_view_filters).get_data()

@frappe.whitelist()
def get_test_data():
    """
    Test function to validate report data for expense accounts.
    Returns comparison data between Account View and Dimension View reports.
    """
    try:
        expenses_list = frappe.get_all(
            "Account",
            filters={"root_type": ["in", ["Expense", "Income"]]},
            pluck="name",
        )

        cost_head = "Festivals"
        # cost_head = "Expense Incurring Departments"
        # cost_head = "Revenue Generation Departments"
        # cost_head = "Self Sustainable Departments"
        # cost_head = "Others"
        # cost_head = ["Expense Incurring Departments" , "Revenue Generation Departments" , "Self Sustainable Departments" , "Others"]
        # cost_head = "Festivals"
        # Fixed date format to YYYY-MM-DD
        from_date = "2025-04-01"
        to_date = "2026-03-31"

        account_view_filters = {
            "from_date": from_date,
            "to_date": to_date,
            "report_view": "Account View",
            "time_period": "Cumulative",
            "report_type": "Both Income and Expenses",
            "dimension": "Cost Head",
            "dimension_value": [cost_head],
            "include_adjustment": 1,
            "include_stock_asset": 0,
            "include_disabled_dimension": 0,
            "exclude_period_closing_entries": 0,
        }

        cost_head_view_filters = {
            "from_date": from_date,
            "to_date": to_date,
            "report_view": "Dimension View",
            "time_period": "Cumulative",
            "report_type": "Both Income and Expenses",
            "dimension": "Cost Head",
            "dimension_value": [cost_head],
            "include_adjustment": 1,
            "include_stock_asset": 0,
            "include_disabled_dimension": 0,
            "exclude_period_closing_entries": 0,
        }

        test_results = []

        for account in expenses_list:
            try:
                account_view_filters["account"] = account
                cost_head_view_filters["account"] = account

                account_view_data = HKM_MASTER_REPORT(account_view_filters).get_data()
                cost_head_view_data = HKM_MASTER_REPORT(
                    cost_head_view_filters
                ).get_data()

                # print(account)

                # Get values with proper fallback to 0
                account_exp = account_view_data[0]["total_exp"] or 0
                cost_head_exp = cost_head_view_data[0]["total_exp"] or 0
                account_inc = account_view_data[0]["total_inc"] or 0
                cost_head_inc = cost_head_view_data[0]["total_inc"] or 0

                # Calculate differences
                exp_difference = abs(account_exp - cost_head_exp)
                inc_difference = abs(account_inc - cost_head_inc)

                # Check if expense difference is greater than 10
                if exp_difference > 10:
                    print("Mismatch found in expense")
                    print(account)
                    print(f"Difference: {exp_difference}")
                    print("--------------------------------")
                    print(account_view_data[0])
                    print("--------------------------------")
                    print(cost_head_view_data[0])
                    print("--------------------------------")
                    print()
                    print()
                    print()

                # Check if income difference is greater than 10
                if inc_difference > 10:
                    print("Mismatch found in income")
                    print(account)
                    print(f"Difference: {inc_difference}")
                    print("--------------------------------")
                    print(account_view_data[0])
                    print("--------------------------------")
                    print(cost_head_view_data[0])
                    print("--------------------------------")
                # print("--------------------------------")
                # print(account_view_data[0])
                # print("--------------------------------")
                # print(cost_head_view_data[0])
                # print("--------------------------------")
                # print()
                # print()
                # print()

            except Exception as e:
                error_result = {"account": account, "error": str(e), "status": "error"}
                test_results.append(error_result)
                print(f"Error processing account {account}: {str(e)}")

        return {
            "status": "completed",
            "total_accounts": len(expenses_list),
            "successful_tests": len(
                [r for r in test_results if r["status"] == "success"]
            ),
            "failed_tests": len([r for r in test_results if r["status"] == "error"]),
            "results": test_results,
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to execute test data function",
        }
