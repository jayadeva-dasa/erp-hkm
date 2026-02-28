# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from .constants import (
    SUMMARY,
    ONLY_INCOME,
    ONLY_EXPENSE,
    NET_PROFIT,
    Add_Income_Expense_total,
    Add_Income_total,
    Add_Expense_total,
    Add_Net_Profit_total,
)


class ReportDataProcessor:
    """Base class for processing report data with common functionality"""

    def __init__(self, filters):
        self.filters = frappe._dict(filters or {})
        self.data = {}
        self.additional_data = {}


    def initialize_common_data(self):
        """Initialize common data structures"""
        self.from_date = self.filters.get("from_date")
        self.to_date = self.filters.get("to_date")
        self.report_type = self.filters.get("report_type")
        self.include_adjustment = self.filters.get("include_adjustment")
        self.include_stock_asset = self.filters.get("include_stock_asset")
        self.exclude_consumption_and_depreciation = self.filters.get(
            "exclude_consumption_and_depreciation"
        )
        self.account = self.filters.get("account")
        self.dimension_meta = frappe.get_meta(self.filters.get("dimension"))
        self.dimension = frappe.scrub(self.filters.get("dimension"))
        self.total_type = self.get_total_type()
        self.inc_keys = []
        self.exp_keys = []
        self.net_keys = []
        self.adj_inc_keys = []
        self.adj_exp_keys = []
        self.adj_net_keys = []

    def get_total_type(self):
        total_type = Add_Income_Expense_total
        if self.report_type == ONLY_INCOME:
            total_type = Add_Income_total
        elif self.report_type == ONLY_EXPENSE:
            total_type = Add_Expense_total
        elif self.report_type == NET_PROFIT:
            total_type = Add_Net_Profit_total
        else:
            total_type = Add_Income_Expense_total
        return total_type

    def process_gl_entry(self, entry, month, key_field="account"):
        """Process a single GL entry with common logic"""
        key = entry.get(key_field)
        report_type = self.filters.get("report_type")
       
        if report_type == SUMMARY:
            self._process_summary_entry(entry, month, key)
        elif report_type == ONLY_INCOME:
            self._process_income_entry(entry, month, key)
        elif report_type == ONLY_EXPENSE:
            self._process_expense_entry(entry, month, key)
        elif report_type == NET_PROFIT:
            self._process_net_profit_entry(entry, month, key)

    def _process_summary_entry(self, entry, month, key):
     
        """Process entry for summary report type"""
        month_key_inc = month.key + "_inc"
        month_key_exp = month.key + "_exp"
        
        # Add keys only once to prevent duplicates
        if month_key_inc not in self.inc_keys:
            self.inc_keys.append(month_key_inc)
        if month_key_exp not in self.exp_keys:
            self.exp_keys.append(month_key_exp)

        # Initialize data structures
        self._initialize_data_structure(key, month_key_inc, month_key_exp)

        # Process income
        if entry.root_type == "Income":
            amount = (entry.sum_credit or 0) - (entry.sum_debit or 0)
            self._update_amounts(key, month_key_inc, amount)

        # Process expense/asset/liability
        if entry.root_type in ["Expense", "Asset", "Liability"]:
            amount = (entry.sum_debit or 0) - (entry.sum_credit or 0)
            self._update_amounts(key, month_key_exp, amount)

    def _process_income_entry(self, entry, month, key):
        """Process entry for income report type"""
        month_key_inc = month.key + "_inc"
        
        # Add key only once to prevent duplicates
        if month_key_inc not in self.inc_keys:
            self.inc_keys.append(month_key_inc)
            
        # Initialize data structures
        self._initialize_data_structure(key, month_key_inc)

        if entry.root_type == "Income":
            amount = (entry.sum_credit or 0) - (entry.sum_debit or 0)
            self._update_amounts(key, month_key_inc, amount)

    def _process_expense_entry(self, entry, month, key):
        """Process entry for expense report type"""
        month_key_exp = month.key + "_exp"
        
        # Add key only once to prevent duplicates
        if month_key_exp not in self.exp_keys:
            self.exp_keys.append(month_key_exp)

        # Initialize data structures
        self._initialize_data_structure(key, month_key_exp)

        if entry.root_type in ["Expense", "Asset", "Liability"]:
            amount = (entry.sum_debit or 0) - (entry.sum_credit or 0)
            self._update_amounts(key, month_key_exp, amount)

    def _process_net_profit_entry(self, entry, month, key):
        """Process entry for net profit report type"""
        month_key = month.key + "_net"
        
        # Add key only once to prevent duplicates
        if month_key not in self.net_keys:
            self.net_keys.append(month_key)
            
        # Initialize data structures
        self._initialize_data_structure(key, month_key)

        # Process income
        if entry.root_type == "Income":
            amount = (entry.sum_credit or 0) - (entry.sum_debit or 0)
            self._update_amounts(key, month_key, amount)

        # Process expense/asset/liability
        if entry.root_type in ["Expense", "Asset", "Liability"]:
            amount = (entry.sum_debit or 0) - (entry.sum_credit or 0)
            self._update_amounts(key, month_key, -amount)

    def _initialize_data_structure(self, key, month_key_inc=None, month_key_exp=None):
        """Initialize data structure for a key"""
        if key not in self.data:
            self.data[key] = {"name": key}

        if month_key_inc and month_key_inc not in self.data[key]:
            self.data[key][month_key_inc] = 0
        if month_key_exp and month_key_exp not in self.data[key]:
            self.data[key][month_key_exp] = 0

        # Initialize additional data
        if month_key_inc and month_key_inc not in self.additional_data:
            self.additional_data[month_key_inc] = 0
        if month_key_exp and month_key_exp not in self.additional_data:
            self.additional_data[month_key_exp] = 0

    def _update_amounts(self, key, month_key, amount):
        """Update amounts in data structures"""
        self.data[key][month_key] += amount
