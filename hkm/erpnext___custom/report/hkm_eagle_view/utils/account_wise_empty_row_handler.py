# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

from hkm.erpnext___custom.report.hkm_eagle_view.utils.constants import (
    ONLY_INCOME,
    ONLY_EXPENSE,
    SUMMARY,
    NET_PROFIT,
)


class AccountWiseEmptyRowHandler:
    """Handles empty row operations for reports"""

    def __init__(self, report_type, time_periods):
        self.report_type = report_type
        self.time_periods = time_periods

    def add_empty_rows(self, data, not_tagged_entry):
        """Add empty rows to the data"""
        empty_row_count = 2
        empty_dict = self._create_empty_dict()

        # Add empty rows after not tagged entries
        if not_tagged_entry:
            for _ in range(empty_row_count):
                data.append(empty_dict)
            data = sorted(
                data, key=lambda row: row["account"] in ["Not Tagged"]
            )

        # Add empty rows at the end
        for _ in range(empty_row_count):
            data.append(empty_dict)

        return data

    def _create_empty_dict(self):
        """Create empty dictionary based on report type"""
        if self.report_type == SUMMARY:
            return {
                "account": "",
                **{
                    key: None
                    for m in self.time_periods
                    for key in (m.key + "_inc", m.key + "_exp")
                },
                "total_inc": None,
                "total_exp": None,
            }
        elif self.report_type == ONLY_INCOME:
            return {
                "account": "",
                **{key: None for m in self.time_periods for key in (m.key + "_inc")},
                "total_inc": None,
            }
        elif self.report_type == ONLY_EXPENSE:
            return {
                "account": "",
                **{key: None for m in self.time_periods for key in (m.key + "_exp")},
                "total_exp": None,
            }
        elif self.report_type == NET_PROFIT:
            return {
                "account": "",
                **{(k.key + "_net"): None for k in self.time_periods},
                "total": None,
            }
        else:
            return {"account": ""} 