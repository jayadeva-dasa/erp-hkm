# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe


def demo():
    filters = frappe._dict({"cost_head": ["Akshaya Yatra Parent"]})
    return HKMReportA02(filters).load_data()


def execute(filters=None):
    return HKMReportA02(filters).load_data()


class HKMReportA02:
    def __init__(self, filters):
        self.filters = frappe._dict(filters)
        self.validate_filters()
        self.set_columns()
        self.get_data()

    def load_data(self):
        # print(self.data)
        return self.columns, list(self.data.values())

    def validate_filters(self):
        if not self.filters.get("cost_head"):
            frappe.throw("Please select Cost Head")

    def get_data(self):
        
        cost_heads = (
            self.filters.get("cost_head")
            + frappe.db.get_descendants("Cost Head", self.filters.get("cost_head"))
            or []
        )
        cost_head_str = ",".join([f"'{c}'" for c in cost_heads])
        # print(cost_head_str)
        self.data = {}
        for r in frappe.db.sql(
            f"""
				SELECT cost_head,tac.root_type, SUM(debit) as sum_debit, SUM(credit) as sum_credit  
				FROM `tabGL Entry`
				JOIN `tabAccount` tac
					ON tac.name = `tabGL Entry`.account
				WHERE tac.report_type = 'Profit and Loss'
				AND is_cancelled = 0
				AND (tac.root_type = 'Income' OR tac.root_type = 'Expense')
				AND cost_head IN ( {cost_head_str} )
				GROUP BY cost_head, tac.root_type
				""",
            as_dict=True,
        ):
            if r["cost_head"] not in self.data:
                self.data[r["cost_head"]] = {
                    "cost_head": r["cost_head"],
                    "income": 0,
                    "expense": 0,
                }
            if r["root_type"] == "Income":
                self.data[r["cost_head"]]["income"] += r["sum_credit"] - r["sum_debit"]
            else:
                self.data[r["cost_head"]]["expense"] += r["sum_debit"] - r["sum_credit"]

    def set_columns(self):
        self.columns = [
            {"label": "Cost Head", "fieldname": "cost_head", "fieldtype": "Data"},
            {"label": "Income", "fieldname": "income", "fieldtype": "Currency"},
            {"label": "Expense", "fieldname": "expense", "fieldtype": "Currency"},
        ]
