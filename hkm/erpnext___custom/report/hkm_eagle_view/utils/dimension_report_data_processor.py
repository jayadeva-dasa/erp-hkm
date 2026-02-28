# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe
from hkm.erpnext___custom.report.hkm_eagle_view.utils.constants import (
    ONLY_INCOME,
    ONLY_EXPENSE,
    SUMMARY,
    NET_PROFIT,
    INCOME,
    EXPENSE_LIST,
)


class DimensionWiseReportDataProcessor:
    """Class to handle GL entry processing and accumulation logic"""

    def __init__(self, report_type, include_adjustment, internal_adjustment_type):
        self.report_type = report_type
        self.include_adjustment = include_adjustment
        self.internal_adjustment_type = internal_adjustment_type

        # Initialize key lists for tracking different types of keys
        self.inc_keys = []
        self.exp_keys = []
        self.net_keys = []
        self.adj_inc_keys = []
        self.adj_exp_keys = []

    def process_gl_entry(self, entry, period, data):
        head = entry.get("head")
        """Process a single GL entry"""
        if self.report_type == SUMMARY:
            self._process_income_expense_entry(entry, period, head, data)
        elif self.report_type == ONLY_INCOME:
            self._process_income_entry(entry, period, head, data)
        elif self.report_type == ONLY_EXPENSE:
            self._process_expense_entry(entry, period, head, data)
        elif self.report_type == NET_PROFIT:
            self._process_net_profit_entry(entry, period, head, data)

    def _process_income_expense_entry(self, entry, period, head, data):
        """Process entry for income and expense report type"""
        month_key_inc = period.key + "_inc"
        month_key_exp = period.key + "_exp"

        # Add keys only once to prevent duplicates
        if month_key_inc not in self.inc_keys:
            self.inc_keys.append(month_key_inc)
        if month_key_exp not in self.exp_keys:
            self.exp_keys.append(month_key_exp)

        # Initialize head data if not exists
        if head not in data:
            data.setdefault(head, {})

        if month_key_inc not in data[head]:
            data[head].setdefault(month_key_inc, 0)
        if month_key_exp not in data[head]:
            data[head].setdefault(month_key_exp, 0)

        # Process income
        if entry.root_type == INCOME:
            amount = (entry.sum_credit or 0) - (entry.sum_debit or 0)
            data[head][month_key_inc] += amount

        # Process expense
        if entry.root_type in EXPENSE_LIST:
            amount = (entry.sum_debit or 0) - (entry.sum_credit or 0)
            data[head][month_key_exp] += amount

    def _process_income_entry(self, entry, period, head, data):
        """Process entry for income report type"""
        month_key_inc = period.key + "_inc"
        adj_month_key_inc = (
            period.key + "_" + frappe.scrub(entry.adjustment_type) + "_inc_adj"
        )

        # Add key only once to prevent duplicates
        if month_key_inc not in self.inc_keys:
            self.inc_keys.append(month_key_inc)

        if adj_month_key_inc not in self.adj_inc_keys:
            self.adj_inc_keys.append(adj_month_key_inc)

        # Initialize head data if not exists
        if head not in data:
            data.setdefault(head, {})
        if month_key_inc not in data[head]:
            data[head][month_key_inc] = 0

        if adj_month_key_inc not in data[head]:
            data[head][adj_month_key_inc] = 0

        amount = (entry.sum_credit or 0) - (entry.sum_debit or 0)
        if entry.adjustment_type == "gl_entry":
            data[head][month_key_inc] += amount
        else:
            data[head][adj_month_key_inc] += amount

    def _process_expense_entry(self, entry, period, head, data):
        """Process entry for expense report type"""
        month_key_exp = period.key + "_exp"
        adj_month_key_exp = (
            period.key + "_" + frappe.scrub(entry.adjustment_type) + "_exp_adj"
        )

        # Add key only once to prevent duplicates
        if month_key_exp not in self.exp_keys:
            self.exp_keys.append(month_key_exp)

        if adj_month_key_exp not in self.adj_exp_keys:
            self.adj_exp_keys.append(adj_month_key_exp)

        # Initialize head data if not exists
        if head not in data:
            data.setdefault(head, {})
        if month_key_exp not in data[head]:
            data[head].setdefault(month_key_exp, 0)

        if adj_month_key_exp not in data[head]:
            data[head][adj_month_key_exp] = 0

        amount = (entry.sum_debit or 0) - (entry.sum_credit or 0)
        if entry.adjustment_type == "gl_entry":
            data[head][month_key_exp] += amount
        else:
            data[head][adj_month_key_exp] += amount

    def _process_net_profit_entry(self, entry, period, head, data):
        """Process entry for net profit report type"""
        month_key = period.key + "_net"

        # Add key only once to prevent duplicates
        if month_key not in self.net_keys:
            self.net_keys.append(month_key)

        # Initialize head data if not exists
        if head not in data:
            data.setdefault(head, {})
        if month_key not in data[head]:
            data[head].setdefault(month_key, 0)

        # Process income
        if entry.root_type == INCOME:
            amount = (entry.sum_credit or 0) - (entry.sum_debit or 0)
            data[head][month_key] += amount

        # Process expense
        if entry.root_type in EXPENSE_LIST:
            amount = (entry.sum_debit or 0) - (entry.sum_credit or 0)
            data[head][month_key] -= amount

    def accumulate_values_into_parents(self, heads, time_periods, dimension_meta):
        """Accumulate children's values in parent heads"""
        # Parent fields use scrubbed doctype name, not fieldname
        parent_key = "parent_" + frappe.scrub(dimension_meta.name)

        for head, data in reversed(list(heads.items())):
            parent_name = data.get(parent_key)
            # Parent fields are already normalized to None in dimension_utils
            if parent_name:
                self._accumulate_parent_values(
                    head, data, parent_key, heads, time_periods
                )

    def _accumulate_parent_values(self, head, data, parent_key, heads, time_periods):
        """Accumulate values for a specific parent"""
        parent_name = data[parent_key]

        # Check if parent exists in heads before accessing
        if parent_name not in heads:
            # Skip this accumulation if parent doesn't exist
            return

        parent = heads[parent_name]

        for period in time_periods:
            if self.report_type == NET_PROFIT:
                self._accumulate_net_profit_values(parent, data, period)
            elif self.report_type == SUMMARY:
                self._accumulate_income_expense_values(parent, data, period)
            elif self.report_type == ONLY_INCOME:
                self._accumulate_income_values(parent, data, period)
            elif self.report_type == ONLY_EXPENSE:
                self._accumulate_expense_values(parent, data, period)

    def _accumulate_net_profit_values(self, parent, data, period):
        """Accumulate net profit values"""
        period_key = period.key + "_net"

        if period_key not in parent:
            parent[period_key] = 0

        parent[period_key] += data.get(period_key, 0)

    def _accumulate_income_expense_values(self, parent, data, period):
        """Accumulate income and expense values"""
        period_key_inc = period.key + "_inc"
        period_key_exp = period.key + "_exp"

        if period_key_inc not in parent:
            parent[period_key_inc] = 0
        parent[period_key_inc] += data.get(period_key_inc, 0)

        if period_key_exp not in parent:
            parent[period_key_exp] = 0
        parent[period_key_exp] += data.get(period_key_exp, 0)

    def _accumulate_income_values(self, parent, data, period):
        """Accumulate income values"""
        period_key_inc = period.key + "_inc"

        if period_key_inc not in parent:
            parent[period_key_inc] = 0

        if data.get(period_key_inc):
            parent[period_key_inc] += data.get(period_key_inc, 0)

        # Accumulate adjustment values only for ONLY_INCOME report type
        if self.report_type == ONLY_INCOME and self.include_adjustment:
            if not self.internal_adjustment_type:
                adj_types = frappe.get_all("Internal Adjustment Type", pluck="name")
                adj_types.append("Unknown")
            else:
                adj_types = self.internal_adjustment_type

            for adj_type in adj_types:
                adj_period_key_inc = (
                    period.key + "_" + frappe.scrub(adj_type) + "_inc_adj"
                )
                if adj_period_key_inc not in parent:
                    parent[adj_period_key_inc] = 0
                if data.get(adj_period_key_inc):
                    parent[adj_period_key_inc] += data.get(adj_period_key_inc, 0)

    def _accumulate_expense_values(self, parent, data, period):
        """Accumulate expense values"""
        period_key_exp = period.key + "_exp"

        if period_key_exp not in parent:
            parent[period_key_exp] = 0

        if data.get(period_key_exp):
            parent[period_key_exp] += data.get(period_key_exp, 0)

        # Accumulate adjustment values only for ONLY_EXPENSE report type
        if self.report_type == ONLY_EXPENSE and self.include_adjustment:
            if not self.internal_adjustment_type:
                adj_types = frappe.get_all("Internal Adjustment Type", pluck="name")
                adj_types.append("Unknown")
            else:
                adj_types = self.internal_adjustment_type

            for adj_type in adj_types:
                adj_period_key_exp = (
                    period.key + "_" + frappe.scrub(adj_type) + "_exp_adj"
                )
                if adj_period_key_exp not in parent:
                    parent[adj_period_key_exp] = 0
                if data.get(adj_period_key_exp):
                    parent[adj_period_key_exp] += data.get(adj_period_key_exp, 0)

    def get_key_lists(self):
        """Return all key lists for column building"""
        return {
            "inc_keys": self.inc_keys,
            "exp_keys": self.exp_keys,
            "net_keys": self.net_keys,
            "adj_inc_keys": self.adj_inc_keys,
            "adj_exp_keys": self.adj_exp_keys,
        }
