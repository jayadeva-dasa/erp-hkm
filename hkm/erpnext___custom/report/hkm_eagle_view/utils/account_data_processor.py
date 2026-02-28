from hkm.erpnext___custom.report.hkm_eagle_view.utils.constants import (
    SUMMARY,
    ONLY_INCOME,
    ONLY_EXPENSE,
    NET_PROFIT,
)

import frappe


class AccountWiseReportDataProcessor:
    def __init__(
        self,
        filters,
        data,
        inc_keys,
        exp_keys,
        net_keys,
        adj_inc_keys,
        adj_exp_keys,
        entry,
        main_key,
    ):
        self.filters = frappe._dict(filters or {})
        self.data = data
        self.inc_keys = inc_keys
        self.exp_keys = exp_keys
        self.net_keys = net_keys
        self.adj_inc_keys = adj_inc_keys
        self.adj_exp_keys = adj_exp_keys
        self.entry = entry
        self.main_key = main_key
        self.include_adjustment = self.filters.get("include_adjustment")

    def get_data(self):
        self.process_gl_entry(entry=self.entry, main_key=self.main_key)
        return (
            self.data,
            self.inc_keys,
            self.exp_keys,
            self.net_keys,
            self.adj_inc_keys,
            self.adj_exp_keys,
        )

    def process_gl_entry(self, entry, main_key, key_field="account"):
        """Process a single GL entry with common logic"""
        key = entry.get(key_field)
        report_type = self.filters.get("report_type")

        if report_type == SUMMARY:
            self._process_summary_entry(entry, main_key, key)
        elif report_type == ONLY_INCOME:
            self._process_income_entry(entry, main_key, key)
        elif report_type == ONLY_EXPENSE:
            self._process_expense_entry(entry, main_key, key)
        elif report_type == NET_PROFIT:
            self._process_net_profit_entry(entry, main_key, key)

    def _process_summary_entry(self, entry, main_key, key):
        """Process entry for summary report type"""
        main_key_inc = main_key + "_inc"
        main_key_exp = main_key + "_exp"

        # Add keys only once to prevent duplicates

        self.inc_keys.append(main_key_inc)
        self.exp_keys.append(main_key_exp)

        # Initialize data structures
        self._initialize_data_structure(key, main_key_inc, main_key_exp)

        # Process income
        if entry.root_type == "Income":
            amount = (entry.sum_credit or 0) - (entry.sum_debit or 0)
            self._update_amounts(key, main_key_inc, amount)

        # Process expense/asset/liability
        if entry.root_type in ["Expense", "Asset", "Liability"]:
            amount = (entry.sum_debit or 0) - (entry.sum_credit or 0)
            self._update_amounts(key, main_key_exp, amount)

    def _process_income_entry(self, entry, main_key, key):
        """Process entry for income report type"""
        main_key_inc = main_key + "_inc"

        # Add key only once to prevent duplicates
        self.inc_keys.append(main_key_inc)

        # Initialize data structures
        self._initialize_data_structure(key, main_key_inc)

        if self.include_adjustment and entry.adjustment_type != "gl_entry":
            adj_key_inc = (
                main_key + "_" + frappe.scrub(entry.adjustment_type) + "_inc_adj"
            )
            self.adj_inc_keys.append(adj_key_inc)
            if adj_key_inc not in self.data[key]:
                self.data[key][adj_key_inc] = 0

        if entry.root_type == "Income":
            amount = (entry.sum_credit or 0) - (entry.sum_debit or 0)

            inc_key = main_key_inc
            if self.include_adjustment and entry.adjustment_type != "gl_entry":
                # amount = (
                #     entry.sum_debit if entry.sum_debit == entry.sum_credit else amount
                # )
                inc_key = (
                    main_key_inc if entry.adjustment_type == "gl_entry" else adj_key_inc
                )

            self._update_amounts(key, inc_key, amount, entry)

    def _process_expense_entry(self, entry, main_key, key):
        """Process entry for expense report type"""
        main_key_exp = main_key + "_exp"

        # Add key only once to prevent duplicates
        self.exp_keys.append(main_key_exp)

        # Initialize data structures
        self._initialize_data_structure(key, main_key_exp)

        if self.include_adjustment and entry.adjustment_type != "gl_entry":
            adj_key_exp = (
                main_key + "_" + frappe.scrub(entry.adjustment_type) + "_exp_adj"
            )
            self.adj_exp_keys.append(adj_key_exp)
            if adj_key_exp not in self.data[key]:
                self.data[key][adj_key_exp] = 0

        if entry.root_type in ["Expense", "Asset", "Liability"]:
            amount = (entry.sum_debit or 0) - (entry.sum_credit or 0)

            exp_key = main_key_exp

            if self.include_adjustment and entry.adjustment_type != "gl_entry":
                # amount = (
                #     entry.sum_debit if entry.sum_debit == entry.sum_credit else amount
                # )
                exp_key = (
                    main_key_exp if entry.adjustment_type == "gl_entry" else adj_key_exp
                )

            self._update_amounts(key, exp_key, amount, entry)

    def _process_net_profit_entry(self, entry, main_key, key):
        """Process entry for net profit report type"""
        main_key_net = main_key + "_net"

        # Add key only once to prevent duplicates
        self.net_keys.append(main_key_net)

        # Initialize data structures
        self._initialize_data_structure(key, main_key_net)

        # Process income
        if entry.root_type == "Income":
            amount = (entry.sum_credit or 0) - (entry.sum_debit or 0)
            self._update_amounts(key, main_key_net, amount)

        # Process expense/asset/liability
        if entry.root_type in ["Expense", "Asset", "Liability"]:
            amount = (entry.sum_debit or 0) - (entry.sum_credit or 0)
            self._update_amounts(key, main_key_net, -amount)

    def _initialize_data_structure(self, key, main_key_inc=None, main_key_exp=None):
        """Initialize data structure for a key"""
        if key not in self.data:
            self.data[key] = {"account": key}

        if main_key_inc and main_key_inc not in self.data[key]:
            self.data[key][main_key_inc] = 0
        if main_key_exp and main_key_exp not in self.data[key]:
            self.data[key][main_key_exp] = 0

    def _update_amounts(self, key, main_key, amount, entry=None):
        """Update amounts in data structures"""
        self.data[key][main_key] += amount
