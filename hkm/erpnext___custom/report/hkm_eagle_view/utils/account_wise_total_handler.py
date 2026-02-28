# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

from hkm.erpnext___custom.report.hkm_eagle_view.utils.constants import (
    ONLY_INCOME,
    ONLY_EXPENSE,
    SUMMARY,
    NET_PROFIT,
)


class AccountWiseTotalHandler:
    """Handles all total calculations for reports"""

    def __init__(self, report_type, inc_keys, exp_keys, net_keys, adj_inc_keys, adj_exp_keys):
        self.report_type = report_type
        self.inc_keys = inc_keys
        self.exp_keys = exp_keys
        self.net_keys = net_keys
        self.adj_inc_keys = adj_inc_keys
        self.adj_exp_keys = adj_exp_keys

    def add_horizontal_total(self, data):
        """Add horizontal total row to the data"""
        if self.report_type == SUMMARY:
            self._get_horizontal_IAE_total(data)
        elif self.report_type == ONLY_INCOME:
            self._get_horizontal_income_total(data)
        elif self.report_type == ONLY_EXPENSE:
            self._get_horizontal_expense_total(data)
        elif self.report_type == NET_PROFIT:
            self._get_horizontal_net_profit_total(data)

    def _get_horizontal_IAE_total(self, data):
        """Calculate horizontal totals for Income and Expense"""
        for row in data:
            income_total = sum(
                row[k]
                for k in row
                if k.endswith("_inc") and isinstance(row[k], (int, float))
            )
            expense_total = sum(
                row[k]
                for k in row
                if k.endswith("_exp") and isinstance(row[k], (int, float))
            )
            row["total_inc"] = income_total
            row["total_exp"] = expense_total

    def _get_horizontal_income_total(self, data):
        """Calculate horizontal totals for Income only"""
        for row in data:
            if any(key.endswith("_inc") or key.endswith("_inc_adj") for key in row):
                row["total_inc"] = sum(
                    row[key]
                    for key in row
                    if key.endswith("_inc") or key.endswith("_inc_adj")
                )

    def _get_horizontal_expense_total(self, data):
        """Calculate horizontal totals for Expense only"""
        for row in data:
            if any(key.endswith("_exp") or key.endswith("_exp_adj") for key in row):
                row["total_exp"] = sum(
                    row[key]
                    for key in row
                    if key.endswith("_exp") or key.endswith("_exp_adj")
                )

    def _get_horizontal_net_profit_total(self, data):
        """Calculate horizontal totals for Net Profit"""
        for row in data:
            if any(key.endswith("_net") for key in row):
                row["total_net"] = sum(row[key] for key in row if key.endswith("_net"))

    def add_final_total_row(self, data):
        """Add final total row to the data"""
        if self.report_type == SUMMARY:
            grand_total = self._get_grand_total_IAE(data)
        elif self.report_type == ONLY_INCOME:
            grand_total = self._get_grand_total_income(data)
        elif self.report_type == ONLY_EXPENSE:
            grand_total = self._get_grand_total_expense(data)
        elif self.report_type == NET_PROFIT:
            grand_total = self._get_grand_total_net_profit(data)
        
        data.append(grand_total)

    def _get_grand_total_IAE(self, data):
        """Calculate grand total for Income and Expense"""
        grand_total = {}
        
        # Calculate income totals
        for inc_key in self.inc_keys:
            grand_total[inc_key] = 0
            for d in data:
                if d.get("account") == "Not Tagged":
                    continue
                grand_total[inc_key] += d.get(inc_key, 0) or 0

        # Calculate expense totals
        for exp_key in self.exp_keys:
            grand_total[exp_key] = 0
            for d in data:
                if d.get("account") == "Not Tagged":
                    continue
                grand_total[exp_key] += d.get(exp_key, 0) or 0
                
        # Calculate row totals
        row_total_inc = 0
        row_total_exp = 0
        for d in data:
            if d.get("account") == "Not Tagged":
                continue
            if d.get("total_inc"):
                row_total_inc += d.get("total_inc", 0)
            if d.get("total_exp"):
                row_total_exp += d.get("total_exp", 0)

        grand_total["total_inc"] = row_total_inc 
        grand_total["total_exp"] = row_total_exp
        
        return grand_total
    
    def _get_grand_total_income(self, data):
        """Calculate grand total for Income only"""
        grand_total = {}
        
        # Calculate income totals
        for inc_key in self.inc_keys:
            grand_total[inc_key] = 0
            for d in data:
                if d.get("account") == "Not Tagged":
                    continue
                grand_total[inc_key] += d.get(inc_key, 0) or 0
                
        # Calculate adjustment income totals
        if self.adj_inc_keys:
            for adj_inc_key in self.adj_inc_keys:
                grand_total[adj_inc_key] = 0
                for d in data:
                    if d.get("account") == "Not Tagged":
                        continue
                    grand_total[adj_inc_key] += d.get(adj_inc_key, 0) or 0
                    
        # Calculate row total
        row_total_inc = 0
        for d in data:
            if d.get("account") == "Not Tagged":
                continue
            if d.get("total_inc"):
                row_total_inc += d.get("total_inc", 0)
        grand_total["total_inc"] = row_total_inc
        
        return grand_total
    
    def _get_grand_total_expense(self, data):
        """Calculate grand total for Expense only"""
        grand_total = {}
        
        # Calculate expense totals
        for exp_key in self.exp_keys:
            grand_total[exp_key] = 0
            for d in data:
                if d.get("account") == "Not Tagged":
                    continue
                grand_total[exp_key] += d.get(exp_key, 0) or 0
                
        # Calculate adjustment expense totals
        if self.adj_exp_keys:
            for adj_exp_key in self.adj_exp_keys:
                grand_total[adj_exp_key] = 0
                for d in data:
                    if d.get("account") == "Not Tagged":
                        continue
                    grand_total[adj_exp_key] += d.get(adj_exp_key, 0) or 0
                    
        # Calculate row total
        row_total_exp = 0
        for d in data:
            if d.get("account") == "Not Tagged":
                continue
            if d.get("total_exp"):
                row_total_exp += d.get("total_exp", 0)
        grand_total["total_exp"] = row_total_exp
        
        return grand_total
    
    def _get_grand_total_net_profit(self, data):
        """Calculate grand total for Net Profit"""
        grand_total = {}
        
        # Calculate net profit totals
        for net_key in self.net_keys:
            grand_total[net_key] = 0
            for d in data:
                if d.get("account") == "Not Tagged":
                    continue
                grand_total[net_key] += d.get(net_key, 0) or 0
                
        # Calculate row total
        row_total_net = 0
        for d in data:
            if d.get("account") == "Not Tagged":
                continue
            if d.get("total_net"):
                row_total_net += d.get("total_net", 0)
        grand_total["total_net"] = row_total_net
        
        return grand_total 