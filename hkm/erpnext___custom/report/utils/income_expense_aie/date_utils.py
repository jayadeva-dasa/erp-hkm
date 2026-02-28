# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

import calendar
from datetime import datetime
import frappe
from frappe import _
from frappe.auth import date_diff
from frappe.utils.data import add_to_date


def validate_filters(from_date, to_date):
    """Validate the input filters"""
    if not from_date and to_date:
        frappe.throw(_("From and To Dates are required."))
    elif date_diff(to_date, from_date) < 0:
        frappe.throw(_("To Date cannot be before From Date."))


def get_dates_range(from_date, to_date):
    """Generate month-wise date ranges"""
    start = datetime.strptime(from_date, "%Y-%m-%d")
    end = datetime.strptime(to_date, "%Y-%m-%d")

    current = start
    date_ranges = []

    while current <= end:
        # Start date of the current month
        month_start = current.strftime("%Y-%m-%d")

        # Total days in the month
        days = calendar.monthrange(current.year, current.month)[1]
        last_day = datetime(year=current.year, month=current.month, day=days)
        month_end = min(end, last_day).strftime("%Y-%m-%d")
        unique_key = current.strftime("%Y%m")

        # Format the output
        formatted_range = frappe._dict(
            key=unique_key,
            label=current.strftime("%B - %y"),
            start_date=month_start,
            end_date=month_end,
        )
        date_ranges.append(formatted_range)

        current = add_to_date(last_day, days=1)

    return date_ranges 