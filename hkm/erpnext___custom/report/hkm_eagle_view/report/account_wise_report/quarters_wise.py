# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

from hkm.erpnext___custom.report.hkm_eagle_view.utils.date_utils import get_fiscal_quarters
from hkm.erpnext___custom.report.hkm_eagle_view.report.account_wise_report.time_based_report import TimeBasedReport


class AccountQuarterWise(TimeBasedReport):
    def __init__(self, filters):
        quarters = get_fiscal_quarters(filters.get("from_date"), filters.get("to_date"))
        super().__init__(filters, quarters)

    def _get_date_condition(self, quarter, adjustment=False):
        """Get date condition for quarter-wise reports (using parameterized query)"""
        if adjustment:
            return f"AND ia.posting_date BETWEEN %(qtr_{quarter.key}_start)s AND %(qtr_{quarter.key}_end)s"
        return f"AND gl.posting_date BETWEEN %(qtr_{quarter.key}_start)s AND %(qtr_{quarter.key}_end)s"
    
    def _get_period_param_prefix(self):
        """Return parameter prefix for quarters"""
        return "qtr"        