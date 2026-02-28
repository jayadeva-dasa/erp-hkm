# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

from .constants import SUMMARY, ONLY_INCOME, ONLY_EXPENSE, NET_PROFIT


def add_empty_rows(data, report_type, months, count=2):
    """Add empty rows to the data based on the report type"""

    if report_type == SUMMARY:
        for _ in range(count):
            data.append(
                {
                    "name": "",
                    **{
                        key: None
                        for m in months
                        for key in (m.key + "_inc", m.key + "_exp")
                    },
                    "total_inc": None,
                    "total_exp": None,
                }
            )
    elif report_type == ONLY_INCOME:
        for _ in range(count):
            data.append(
                {
                    "name": "",
                    **{(k.key + "_inc"): None for k in months},
                    "total": None,
                }
            )
    elif report_type == ONLY_EXPENSE:
        for _ in range(count):
            data.append(
                {
                    "name": "",
                    **{(k.key + "_exp"): None for k in months},
                    "total": None,
                }
            )
    else:
        for _ in range(count):
            data.append(
                {
                    "name": "",
                    **{(k.key + "_net"): None for k in months},
                    "total": None,
                }
            )
    return data 