# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

from hkm.erpnext___custom.report.hkm_eagle_view.utils.date_utils import get_daywise_dates
from hkm.erpnext___custom.report.hkm_eagle_view.report.account_wise_report.time_based_report import TimeBasedReport


class AccountDayWise(TimeBasedReport):
    def __init__(self, filters):
        days = get_daywise_dates(filters.get("from_date"), filters.get("to_date"))
        super().__init__(filters, days)

    def _get_date_condition(self, day, adjustment=False):
        """Get date condition for day-wise reports (using parameterized query)"""
        if adjustment:
            return f"AND ia.posting_date = %(day_{day.key}_start)s"
        return f"AND gl.posting_date = %(day_{day.key}_start)s"
    
    def _get_period_param_prefix(self):
        """Return parameter prefix for days"""
        return "day"