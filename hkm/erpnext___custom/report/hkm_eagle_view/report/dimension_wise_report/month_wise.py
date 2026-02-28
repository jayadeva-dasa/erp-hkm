# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

from hkm.erpnext___custom.report.hkm_eagle_view.utils.date_utils import get_monthly_ranges
from hkm.erpnext___custom.report.hkm_eagle_view.report.dimension_wise_report.time_based_report import TimeBasedReport


class DimensionMonthWise(TimeBasedReport):
    def __init__(self, filters):
        months = get_monthly_ranges(filters.get("from_date"), filters.get("to_date"))
        super().__init__(filters, months)

    def _get_date_condition(self, month, adjustment=False):
        """Get date condition for month-wise reports (using parameterized query)"""
        if adjustment:
            return f"AND ia.posting_date BETWEEN %(month_{month.key}_start)s AND %(month_{month.key}_end)s"
        return f"AND gl.posting_date BETWEEN %(month_{month.key}_start)s AND %(month_{month.key}_end)s"
    
    def _get_period_param_prefix(self):
        """Return parameter prefix for months"""
        return "month"        