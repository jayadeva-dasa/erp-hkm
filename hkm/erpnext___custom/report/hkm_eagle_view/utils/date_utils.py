# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

import calendar
from datetime import datetime, timedelta
import frappe
from frappe import _
from frappe.auth import date_diff
from frappe.utils.data import add_to_date
from dateutil.relativedelta import relativedelta
from hkm.erpnext___custom.report.hkm_eagle_view.utils.constants import TIME_PERIOD , DAY_WISE


class DateRangeGenerator:
    """
    A comprehensive class for generating various types of date ranges and date utilities.
    
    This class provides methods to generate:
    - Month-wise date ranges
    - Fiscal quarter-wise date ranges
    - Weekly date ranges
    - Day-wise date ranges
    """
    
    def __init__(self, from_date=None, to_date=None):
        """
        Initialize the DateRangeGenerator with optional date range.
        
        Args:
            from_date (str): Start date in 'YYYY-MM-DD' format
            to_date (str): End date in 'YYYY-MM-DD' format
        """
        self.from_date = from_date
        self.to_date = to_date
        
        if from_date and to_date:
            self.validate_filters(from_date, to_date)
    
    def validate_filters(self, from_date, to_date , time_period=None):
        """
        Validate the input date filters.
        
        Args:
            from_date (str): Start date in 'YYYY-MM-DD' format
            to_date (str): End date in 'YYYY-MM-DD' format
            
        Raises:
            frappe.ValidationError: If dates are invalid or to_date is before from_date
        """
        if not from_date and to_date:
            frappe.throw(_("From and To Dates are required."))
        elif date_diff(to_date, from_date) < 0:
            frappe.throw(_("To Date cannot be before From Date."))
            
        if time_period and time_period == DAY_WISE:
            return
            if date_diff(to_date, from_date) > 30:
                frappe.throw(_("Day Wise report can only be generated for a maximum of 30 days."))
        
    
    def set_date_range(self, from_date, to_date):
        """
        Set or update the date range for the generator.
        
        Args:
            from_date (str): Start date in 'YYYY-MM-DD' format
            to_date (str): End date in 'YYYY-MM-DD' format
        """
        self.validate_filters(from_date, to_date)
        self.from_date = from_date
        self.to_date = to_date
    
    def get_monthly_ranges(self, from_date=None, to_date=None):
        """
        Generate month-wise date ranges.
        
        Args:
            from_date (str, optional): Start date. Uses instance from_date if not provided
            to_date (str, optional): End date. Uses instance to_date if not provided
            
        Returns:
            list: List of frappe._dict objects with month-wise date ranges
        """
        from_date = from_date or self.from_date
        to_date = to_date or self.to_date
        
        if not from_date or not to_date:
            frappe.throw(_("Date range is required. Use set_date_range() or provide parameters."))
        
        start = datetime.strptime(from_date, "%Y-%m-%d")
        end = datetime.strptime(to_date, "%Y-%m-%d")

        date_ranges = []

        # Start from the first day of the month containing the start date
        current = datetime(start.year, start.month, 1)

        while current <= end:
            # Calculate the last day of the current month
            days = calendar.monthrange(current.year, current.month)[1]
            month_end_date = datetime(current.year, current.month, days)
            
            # Determine the actual start and end dates for this month
            actual_start = max(current, start)
            actual_end = min(month_end_date, end)
            
            # Only add this month if it overlaps with our date range
            if actual_start <= actual_end:
                unique_key = current.strftime("%Y%m")

                # Format the output
                formatted_range = frappe._dict(
                    key=unique_key,
                    label=current.strftime("%B- %y"),
                    start_date=actual_start.strftime("%Y-%m-%d"),
                    end_date=actual_end.strftime("%Y-%m-%d"),
                )
                date_ranges.append(formatted_range)

            # Move to the first day of the next month
            current = (current + relativedelta(months=1)).replace(day=1)

        return date_ranges
    
    def get_fiscal_quarters(self, from_date=None, to_date=None):
        """
        Generate fiscal quarter-wise date ranges with lowercase, underscore keys.
        
        Args:
            from_date (str, optional): Start date. Uses instance from_date if not provided
            to_date (str, optional): End date. Uses instance to_date if not provided
            
        Returns:
            list: List of frappe._dict objects with fiscal quarter ranges
            
        Example:
            [
                {
                    "key": "q4_2024_25",
                    "label": "Q4 2024-25",
                    "start_date": "2025-01-01",
                    "end_date": "2025-03-31"
                },
                {
                    "key": "q1_2025_26",
                    "label": "Q1 2025-26",
                    "start_date": "2025-04-01",
                    "end_date": "2025-06-30"
                }
            ]
        """
        from_date = from_date or self.from_date
        to_date = to_date or self.to_date
        
        if not from_date or not to_date:
            frappe.throw(_("Date range is required. Use set_date_range() or provide parameters."))
        
        start = datetime.strptime(from_date, "%Y-%m-%d")
        end = datetime.strptime(to_date, "%Y-%m-%d")

        ranges = []

        # Generate all possible quarters that could overlap with the date range
        # Start from the fiscal year that contains the start date
        if start.month < 4:
            fy_start_year = start.year - 1
        else:
            fy_start_year = start.year

        # End with the fiscal year that contains the end date
        if end.month < 4:
            fy_end_year = end.year - 1
        else:
            fy_end_year = end.year

        # Iterate through each fiscal year
        for fy_year in range(fy_start_year, fy_end_year + 1):
            # Generate quarters for this fiscal year
            for q_num, offset in enumerate([0, 3, 6, 9], start=1):
                q_start = datetime(fy_year, 4, 1) + relativedelta(months=offset)
                q_end = q_start + relativedelta(months=3) - relativedelta(days=1)
                
                # Check if this quarter overlaps with our date range
                if q_end < start or q_start > end:
                    continue
                
                # Adjust quarter boundaries to fit within the specified range
                actual_start = max(q_start, start)
                actual_end = min(q_end, end)

                # Determine fiscal year (April to March)
                fy_start = q_start.year if q_start.month >= 4 else q_start.year - 1
                fy_end = fy_start + 1

                fiscal_year_label = f"{fy_start}-{str(fy_end)[-2:]}"
                fiscal_year_key = f"{fy_start}_{str(fy_end)[-2:]}"  # → 2025_26

                label = f"Q{q_num} {fiscal_year_label}"  # → Q2 2025-26
                key = f"q{q_num}_{fiscal_year_key}"  # → q2_2025_26

                ranges.append(
                    frappe._dict(
                        key=key,
                        label=label,
                        start_date=actual_start.strftime("%Y-%m-%d"),
                        end_date=actual_end.strftime("%Y-%m-%d"),
                    )
                )

        return ranges
    def get_weekly_ranges(self, from_date=None, to_date=None, use_sequential_weeks=True):
        """
        Generate week-wise date ranges with flexible week key/label format.

        Args:
            from_date (str, optional): Start date.
            to_date (str, optional): End date.
            use_sequential_weeks (bool, optional): If True, use "Week 1", "Week 2", ... starting from from_date.
                                                If False, use calendar week numbers.

        Returns:
            list: List of frappe._dict objects with weekly date ranges.
        """
        from_date = from_date or self.from_date
        to_date = to_date or self.to_date

        if not from_date or not to_date:
            frappe.throw(_("Date range is required. Use set_date_range() or provide parameters."))

        start = datetime.strptime(from_date, "%Y-%m-%d")
        end = datetime.strptime(to_date, "%Y-%m-%d")

        ranges = []
        sequential_week = 1

        # Start from the actual start date, not aligned to Monday
        current = start

        while current <= end:
            # Calculate the end of the current week (Sunday)
            week_end = current + relativedelta(days=6 - current.weekday())
            
            # If week_end exceeds our end date, cap it
            if week_end > end:
                week_end = end

            if use_sequential_weeks:
                week_num = sequential_week
                key = f"week_{week_num}"
                label = f"Week {week_num}"
            else:
                week_num = int(current.strftime("%U"))  # Use "%W" if weeks start on Monday
                year = current.year
                key = f"week_{week_num}_{year}"
                label = f"Week {week_num} {year}"

            ranges.append(
                frappe._dict(
                    key=key,
                    label=label,
                    start_date=current.strftime("%Y-%m-%d"),
                    end_date=week_end.strftime("%Y-%m-%d"),
                )
            )

            # Move to the next week (Monday of next week)
            current = week_end + relativedelta(days=1)
            sequential_week += 1

        return ranges

    
    def get_daywise_dates(self, from_date=None, to_date=None):
        """
        Generate day-wise date ranges with formatted labels.
        
        Args:
            from_date (str, optional): Start date. Uses instance from_date if not provided
            to_date (str, optional): End date. Uses instance to_date if not provided
            
        Returns:
            list: List of frappe._dict objects with day-wise dates
            
        Example:
            [
                {
                    "key": "2025-07-23",
                    "label": "23/07/25",
                    "day_name": "Wednesday"
                },
                {
                    "key": "2025-07-24",
                    "label": "24/07/25",
                    "day_name": "Thursday"
                }
            ]
        """
        from_date = from_date or self.from_date
        to_date = to_date or self.to_date
        
        if not from_date or not to_date:
            frappe.throw(_("Date range is required. Use set_date_range() or provide parameters."))
        
        start = datetime.strptime(from_date, "%Y-%m-%d")
        end = datetime.strptime(to_date, "%Y-%m-%d")

        date_list = []

        while start <= end:
            date_list.append(
                frappe._dict(
                    key=start.strftime("%Y-%m-%d"),  # for filters or SQL
                    label=start.strftime("%d/%m/%y"),  # for dropdown UI (24/07/25)
                    day_name=start.strftime("%A"),  # optional: "Wednesday"
                )
            )
            start += timedelta(days=1)

        return date_list
    
    def get_all_ranges(self, from_date=None, to_date=None):
        """
        Get all types of date ranges in a single call.
        
        Args:
            from_date (str, optional): Start date. Uses instance from_date if not provided
            to_date (str, optional): End date. Uses instance to_date if not provided
            
        Returns:
            dict: Dictionary containing all types of date ranges
        """
        from_date = from_date or self.from_date
        to_date = to_date or self.to_date
        
        if not from_date or not to_date:
            frappe.throw(_("Date range is required. Use set_date_range() or provide parameters."))
        
        return {
            'monthly': self.get_monthly_ranges(from_date, to_date),
            'fiscal_quarters': self.get_fiscal_quarters(from_date, to_date),
            'weekly': self.get_weekly_ranges(from_date, to_date),
            'daily': self.get_daywise_dates(from_date, to_date)
        }


# Backward compatibility functions (deprecated - use DateRangeGenerator class instead)
def validate_filters(from_date, to_date , time_period):
    """Validate the input filters (deprecated - use DateRangeGenerator class)"""
    generator = DateRangeGenerator()
    return generator.validate_filters(from_date, to_date , time_period)


def get_monthly_ranges(from_date, to_date):
    """Generate month-wise date ranges (deprecated - use DateRangeGenerator class)"""
    generator = DateRangeGenerator(from_date, to_date)
    return generator.get_monthly_ranges()


def get_fiscal_quarters(from_date, to_date):
    """Generate fiscal quarter-wise date ranges (deprecated - use DateRangeGenerator class)"""
    generator = DateRangeGenerator(from_date, to_date)
    return generator.get_fiscal_quarters()


def get_weekly_ranges(from_date, to_date):
    """Generate week-wise date ranges (deprecated - use DateRangeGenerator class)"""
    generator = DateRangeGenerator(from_date, to_date)
    return generator.get_weekly_ranges()


def get_daywise_dates(from_date, to_date):
    """Generate day-wise date ranges (deprecated - use DateRangeGenerator class)"""
    generator = DateRangeGenerator(from_date, to_date)
    return generator.get_daywise_dates()
