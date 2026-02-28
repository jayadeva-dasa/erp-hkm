from calendar import month
from .constants import (
    Add_Income_Expense_total,
    Add_Income_total,
    Add_Expense_total,
    Add_Net_Profit_total,
)
import frappe

from .dimension_utils import get_heads , get_child_nodes


class AdditionalTotal:
    def __init__(
        self,
        data,
        months,
        total_type,
        inc_keys,
        exp_keys,
        net_keys,
        tree=False,
        dimension=None,
        dimension_value=None,
        dimension_meta=None,
        adj_inc_keys=None,
        adj_exp_keys=None,
    ):
        self.data = data
        self.months = months
        self.total_type = total_type
        self.inc_keys = inc_keys
        self.exp_keys = exp_keys
        self.net_keys = net_keys
        self.tree = tree
        self.grand_total = {}
        self.dimension = dimension
        self.dimension_value = dimension_value
        self.dimension_meta = dimension_meta
        self.adj_inc_keys = adj_inc_keys
        self.adj_exp_keys = adj_exp_keys

    def get_horizontal_total(self):

        self.data = GrandTotalHorizontal(
            self.data, self.total_type
        ).get_horizontal_total()

        return self.data

    def get_grand_total(self):
        ## get grand totoal that shows at the bottom of the table

        ## total of total income and expense in report

        if self.tree:
            self.grand_total = TSGrandTotal(
                self.data,
                self.total_type,
                self.grand_total,
                dimension=self.dimension,
                dimension_value=self.dimension_value,
                dimension_meta=self.dimension_meta,
            ).get_grand_total()

            ## grand total of tree structure data
            self.grand_total = TSGrandTotalMonthwise(
                self.data,
                self.inc_keys,
                self.exp_keys,
                self.net_keys,
                self.total_type,
                self.grand_total,
                dimension=self.dimension,
                dimension_value=self.dimension_value,
                dimension_meta=self.dimension_meta,
                adj_inc_keys=self.adj_inc_keys,
                adj_exp_keys=self.adj_exp_keys,
            ).get_tree_grand_total()
        else:
            self.grand_total = GeneralGrandTotal(
                self.data,
                self.total_type,
                self.grand_total,
            ).get_grand_total()
            self.data = GeneralGrandTotalMonthwise(
                self.data,
                self.inc_keys,
                self.exp_keys,
                self.net_keys,
                self.total_type,
                self.grand_total,
                adj_inc_keys=self.adj_inc_keys,
                adj_exp_keys=self.adj_exp_keys,
            ).get_monthwise_grand_total()

        return self.data


class TSGrandTotal:
    def __init__(
        self,
        data,
        total_type,
        grand_total,
        dimension=None,
        dimension_value=None,
        dimension_meta=None,
    ):
        self.data = data
        self.total_type = total_type
        self.grand_total = grand_total
        self.dimension = dimension
        self.dimension_value = dimension_value
        self.dimension_meta = dimension_meta
        self.heads = get_child_nodes(self.dimension_meta, self.dimension_value)

    def get_grand_total(self):

        if self.total_type == Add_Income_Expense_total:
            self.get_grand_total_IAE()

        elif self.total_type == Add_Income_total:
            self.get_grand_total_income()

        elif self.total_type == Add_Expense_total:
            self.get_grand_total_expense()
        elif self.total_type == Add_Net_Profit_total:
            self.get_grand_total_net_profit()
        return self.grand_total

    def get_grand_total_IAE(self):
        row_total_inc = 0
        row_total_exp = 0
        for d in self.data:
            if d.get("name") in self.heads:
                row_total_inc += d.get("horizontal_total_inc", 0)
                row_total_exp += d.get("horizontal_total_exp", 0)

        self.grand_total["horizontal_total_inc"] = row_total_inc
        self.grand_total["horizontal_total_exp"] = row_total_exp

    def get_grand_total_income(self):
        row_total_inc = 0
        for d in self.data:
            if d.get("name") in self.heads:
                row_total_inc += d.get("horizontal_total_inc", 0)
        self.grand_total["horizontal_total_inc"] = row_total_inc

    def get_grand_total_expense(self):
        row_total_exp = 0
        for d in self.data:
            if d.get("name") in self.heads:
                row_total_exp += d.get("horizontal_total_exp", 0)
        self.grand_total["horizontal_total_exp"] = row_total_exp

    def get_grand_total_net_profit(self):
        row_total_net = 0
        for d in self.data:
            if d.get("name") in self.heads:
                row_total_net += d.get("horizontal_total_net", 0)
        self.grand_total["horizontal_total_net"] = row_total_net

    
        


       

class TSGrandTotalMonthwise:
    def __init__(
        self,
        data,
        inc_keys,
        exp_keys,
        net_keys,
        total_type,
        grand_total,
        dimension=None,
        dimension_value=None,
        dimension_meta=None,
        adj_inc_keys=None,
        adj_exp_keys=None,
    ):
        self.data = data
        self.inc_keys = list(set(inc_keys))
        self.exp_keys = list(set(exp_keys))
        self.net_keys = list(set(net_keys))
        self.total_type = total_type
        self.grand_total = grand_total
        self.dimension = dimension
        self.dimension_value = dimension_value
        self.dimension_meta = dimension_meta
        self.heads = get_child_nodes(self.dimension_meta, self.dimension_value)
        self.adj_inc_keys = adj_inc_keys
        self.adj_exp_keys = adj_exp_keys

    def get_tree_grand_total(self):
        if self.total_type == Add_Income_Expense_total:
            self.get_monthwise_grand_total_IAE()
        elif self.total_type == Add_Income_total:
            self.get_monthwise_grand_total_income()
        elif self.total_type == Add_Expense_total:
            self.get_monthwise_grand_total_expense()
        elif self.total_type == Add_Net_Profit_total:
            self.get_monthwise_grand_total_net_profit()
        
        self.data.append(self.grand_total)
        return self.data

    def get_monthwise_grand_total_IAE(self):

        for inc_key in self.inc_keys:
            self.grand_total[inc_key] = 0

            for d in self.data:

                if d.get("name") in self.heads:
                    self.grand_total[inc_key] += d.get(inc_key, 0) or 0

        for exp_key in self.exp_keys:
            self.grand_total[exp_key] = 0
            for d in self.data:
                if d.get("name") in self.heads:
                    self.grand_total[exp_key] += d.get(exp_key, 0) or 0

    def get_monthwise_grand_total_income(self):
        for inc_key in self.inc_keys:
            self.grand_total[inc_key] = 0
            for d in self.data:
                if d.get("name") in self.heads:
                    self.grand_total[inc_key] += d.get(inc_key, 0) or 0
        if self.adj_inc_keys:
            for adj_inc_key in self.adj_inc_keys:
                self.grand_total[adj_inc_key] = 0
                for d in self.data:
                    if d.get("name") in self.heads:
                        self.grand_total[adj_inc_key] += d.get(adj_inc_key, 0) or 0

    def get_monthwise_grand_total_expense(self):
        for exp_key in self.exp_keys:
            self.grand_total[exp_key] = 0
            for d in self.data:
                if d.get("name") in self.heads:
                    self.grand_total[exp_key] += d.get(exp_key, 0) or 0
        if self.adj_exp_keys:
            for adj_exp_key in self.adj_exp_keys:
                self.grand_total[adj_exp_key] = 0
                for d in self.data:
                    if d.get("name") in self.heads:
                        self.grand_total[adj_exp_key] += d.get(adj_exp_key, 0) or 0

    def get_monthwise_grand_total_net_profit(self):
        for net_key in self.net_keys:
            self.grand_total[net_key] = 0
            for d in self.data:
                if d.get("name") in self.heads:
                    self.grand_total[net_key] += d.get(net_key, 0) or 0

    

class GeneralGrandTotal:
    def __init__(self, data, total_type, grand_total):
        self.data = data
        self.total_type = total_type
        self.grand_total = grand_total

    def get_grand_total(self):
        if self.total_type == Add_Income_Expense_total:
            self.get_grand_total_IAE()

        elif self.total_type == Add_Income_total:
            self.get_grand_total_income()

        elif self.total_type == Add_Expense_total:
            self.get_grand_total_expense()
        elif self.total_type == Add_Net_Profit_total:
            self.get_grand_total_net_profit()
        return self.grand_total

    def get_grand_total_IAE(self):
        row_total_inc = 0
        row_total_exp = 0
        for d in self.data:
            row_total_inc += d.get("horizontal_total_inc", 0)
            row_total_exp += d.get("horizontal_total_exp", 0)

        self.grand_total["horizontal_total_inc"] = row_total_inc
        self.grand_total["horizontal_total_exp"] = row_total_exp

    def get_grand_total_income(self):
        row_total_inc = 0
        for d in self.data:
            row_total_inc += d.get("horizontal_total_inc", 0)
        self.grand_total["horizontal_total_inc"] = row_total_inc

    def get_grand_total_expense(self):
        row_total_exp = 0
        for d in self.data:
            row_total_exp += d.get("horizontal_total_exp", 0)
        self.grand_total["horizontal_total_exp"] = row_total_exp

    def get_grand_total_net_profit(self):
        row_total_net = 0
        for d in self.data:
            row_total_net += d.get("horizontal_total_net", 0)
        self.grand_total["horizontal_total_net"] = row_total_net


class GrandTotalHorizontal:
    def __init__(self, data, total_type ):
        self.data = data
        self.total_type = total_type

    def get_horizontal_total(self):
        if self.total_type == Add_Income_Expense_total:
            ## get total_for_income_expense horizontal
            self.get_horizontal_IAE_total()
        elif self.total_type == Add_Income_total:
            self.get_horizontal_income_total()
        elif self.total_type == Add_Expense_total:
            self.get_horizontal_expense_total()
        elif self.total_type == Add_Net_Profit_total:
            self.get_horizontal_net_profit_total()
        return self.data

    def get_horizontal_IAE_total(self):
        for row in self.data:
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
            row["horizontal_total_inc"] = income_total
            row["horizontal_total_exp"] = expense_total

    def get_horizontal_income_total(self):
        for row in self.data:
            if any(key.endswith("_inc") or key.endswith("_inc_adj") for key in row):
                row["horizontal_total_inc"] = sum(
                    row[key] for key in row if key.endswith("_inc") or key.endswith("_inc_adj")
                )

    def get_horizontal_expense_total(self):
        for row in self.data:
            if any(key.endswith("_exp") or key.endswith("_exp_adj") for key in row):
                row["horizontal_total_exp"] = sum(
                    row[key] for key in row if key.endswith("_exp") or key.endswith("_exp_adj")
                )

    def get_horizontal_net_profit_total(self):
        for row in self.data:
            if any(key.endswith("_net") for key in row):
                row["horizontal_total_net"] = sum(
                    row[key] for key in row if key.endswith("_net")
                )


class GeneralGrandTotalMonthwise:
    def __init__(self, data, inc_keys, exp_keys, net_keys, total_type, grand_total, adj_inc_keys = None, adj_exp_keys = None):
        self.data = data
        self.inc_keys = list(set(inc_keys))
        self.exp_keys = list(set(exp_keys))
        self.net_keys = list(set(net_keys))
        self.total_type = total_type
        self.grand_total = grand_total
        self.adj_inc_keys = adj_inc_keys
        self.adj_exp_keys = adj_exp_keys

    def get_monthwise_grand_total(self):
        if self.total_type == Add_Income_Expense_total:
            self.get_monthwise_grand_total_IAE()
        elif self.total_type == Add_Income_total:
            self.get_monthwise_grand_total_income()
        elif self.total_type == Add_Expense_total:
            self.get_monthwise_grand_total_expense()
        elif self.total_type == Add_Net_Profit_total:
            self.get_monthwise_grand_total_net_profit()
        self.data.append(self.grand_total)
        return self.data

    def get_monthwise_grand_total_IAE(self):
        for inc_key in self.inc_keys:
            self.grand_total[inc_key] = 0
            for d in self.data:
                self.grand_total[inc_key] += d.get(inc_key, 0) or 0

        for exp_key in self.exp_keys:
            self.grand_total[exp_key] = 0
            for d in self.data:
                self.grand_total[exp_key] += d.get(exp_key, 0) or 0

    def get_monthwise_grand_total_income(self):
        for inc_key in self.inc_keys:
            self.grand_total[inc_key] = 0
            for d in self.data:
                self.grand_total[inc_key] += d.get(inc_key, 0) or 0
        if self.adj_inc_keys:
            for adj_inc_key in self.adj_inc_keys:
                self.grand_total[adj_inc_key] = 0
                for d in self.data:
                    self.grand_total[adj_inc_key] += d.get(adj_inc_key, 0) or 0

    def get_monthwise_grand_total_expense(self):
        for exp_key in self.exp_keys:
            self.grand_total[exp_key] = 0
            for d in self.data:
                self.grand_total[exp_key] += d.get(exp_key, 0) or 0
        if self.adj_exp_keys:
            for adj_exp_key in self.adj_exp_keys:
                self.grand_total[adj_exp_key] = 0
                for d in self.data:
                    self.grand_total[adj_exp_key] += d.get(adj_exp_key, 0) or 0

    def get_monthwise_grand_total_net_profit(self):
        for net_key in self.net_keys:
            self.grand_total[net_key] = 0
            for d in self.data:
                self.grand_total[net_key] += d.get(net_key, 0) or 0
