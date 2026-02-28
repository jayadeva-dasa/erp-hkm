# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

from hkm.erpnext___custom.report.hkm_eagle_view.utils.date_utils import get_weekly_ranges
from hkm.erpnext___custom.report.hkm_eagle_view.report.account_wise_report.time_based_report import TimeBasedReport


class AccountWeekWise(TimeBasedReport):
    def __init__(self, filters):
        weeks = get_weekly_ranges(filters.get("from_date"), filters.get("to_date"))
        super().__init__(filters, weeks)

    def _get_date_condition(self, week, adjustment=False):
        """Get date condition for week-wise reports (using parameterized query)"""
        if adjustment:
            return f"AND ia.posting_date BETWEEN %(week_{week.key}_start)s AND %(week_{week.key}_end)s"
        return f"AND gl.posting_date BETWEEN %(week_{week.key}_start)s AND %(week_{week.key}_end)s"
    
    def _get_period_param_prefix(self):
        """Return parameter prefix for weeks"""
        return "week"        