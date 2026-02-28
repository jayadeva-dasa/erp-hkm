import frappe
from hkm.erpnext___custom.report.hkm_eagle_view.utils.base_report import BaseReport
from hkm.erpnext___custom.report.hkm_eagle_view.utils.sql_conditions import (
    get_ie_gl_sql_conditions,
    get_ie_adjustment_sql_conditions,
    get_al_gl_sql_conditions,
)
from hkm.erpnext___custom.report.hkm_eagle_view.utils.sql_query_builder import SQLSelectBuilder
from hkm.erpnext___custom.report.hkm_eagle_view.utils.query_optimizer import QueryParameterBuilder
from hkm.erpnext___custom.report.hkm_eagle_view.utils.report_formatters import ReportFormatter
from hkm.erpnext___custom.report.hkm_eagle_view.utils.constants import (
    INCOME,
    EXPENSE_LIST,
    REPORT_TYPE,
    SUMMARY,
    ONLY_INCOME,
    ONLY_EXPENSE,
    NET_PROFIT,
)

income_keys = "total_inc"
expense_keys = "total_exp"
net_keys = "total_net"


class AccountCummulative(BaseReport):
    def __init__(self, filters):
        super().__init__(filters)
        self.data = []

        self.gl_conditions, self.gl_params = get_ie_gl_sql_conditions(
            account=self.account,
            from_date=self.from_date,
            to_date=self.to_date,
            include_stock_asset=self.include_stock_asset,
            dimension_value=self.selected_dimension_value,
            dimension_meta=self.dimension_meta,
            exclude_period_closing_entries=self.exclude_period_closing_entries,
            company=self.company,
            permission_cache=self.permission_cache,
        )
        self.asset_liability_conditions, self.asset_liability_params = get_al_gl_sql_conditions(
            account=self.account,
            from_date=self.from_date,
            to_date=self.to_date,
            include_stock_asset=self.include_stock_asset,
            dimension_value=self.selected_dimension_value,
            dimension_meta=self.dimension_meta,
            exclude_period_closing_entries=self.exclude_period_closing_entries,
            company=self.company,
            permission_cache=self.permission_cache,
        )
        self.adjustment_conditions, self.adjustment_params = get_ie_adjustment_sql_conditions(
            account=self.account,
            from_date=self.from_date,
            to_date=self.to_date,
            adjustment_type=self.internal_adjustment_type,
            dimension_meta=self.dimension_meta,
            dimension_value=self.selected_dimension_value,
            permission_cache=self.permission_cache,
        )

    def get_data(self):
        self.load_data()
        self.add_empty_row()
        self.add_grand_total_row()
        return self.data

    def load_data(self):
        """Load data from database"""
        self.get_summary_entries()

    def get_sql_select_section(self):
        """Use centralized SQL builder to eliminate duplication"""
        return SQLSelectBuilder.get_income_expense_select(self.filters.get(REPORT_TYPE))

    def get_summary_entries(self):
        """Get summary GL entries"""
        data = {}

        if self.filters.get(REPORT_TYPE) == ONLY_INCOME:
            self.gl_conditions += " AND tac.root_type = 'Income'"
        elif self.filters.get(REPORT_TYPE) == ONLY_EXPENSE:
            self.gl_conditions += " AND tac.root_type = 'Expense'"

        query = f"""
            SELECT 
                {self.get_sql_select_section().strip()}
                gl.account,
                tac.root_type
            FROM `tabGL Entry` gl
            JOIN `tabAccount` tac ON tac.name = gl.account
             {self.gl_conditions}
            GROUP BY gl.account, root_type
        """

        if self.include_stock_asset and self.filters.get(REPORT_TYPE) in [
            SUMMARY,
            ONLY_EXPENSE,
        ]:
            results = self._get_stock_asset_query_summary()
            query += results
        # Merge params for parameterized query
        base_params = {"from_date": self.from_date, "to_date": self.to_date}
        all_params = QueryParameterBuilder.merge_params(
            base_params, self.gl_params, self.asset_liability_params
        )
        
        for d in frappe.db.sql(query, all_params, as_dict=True):
            head = d.get("account")
            root_type = d.get("root_type")

            total_inc = 0
            total_exp = 0
            net_profit = 0

            report_type = self.filters.get(REPORT_TYPE)

            if report_type == NET_PROFIT:
                net_profit = int(d.get("net_profit", 0) or 0)
            else:
                total_inc = int(d.get("total_inc", 0) or 0)
                total_exp = int(d.get("total_exp", 0) or 0)

            if head not in data:
                data[head] = {
                    "account": head,
                    income_keys: 0,
                    expense_keys: 0,
                    net_keys: 0,
                }

            if root_type == INCOME:
                data[head][income_keys] += total_inc

            if root_type in EXPENSE_LIST:
                data[head][expense_keys] += total_exp

            data[head][net_keys] += net_profit

        if self.include_adjustment:
            adjustment_map = self._get_adjustment_data_summary()
            for h in adjustment_map:
                if h in data:
                    data[h][income_keys] += adjustment_map[h][income_keys]
                    data[h][expense_keys] += adjustment_map[h][expense_keys]
                    data[h][net_keys] += adjustment_map[h][net_keys]

                if h not in data:
                    data[h] = {
                        "account": h,
                        income_keys: adjustment_map[h][income_keys],
                        expense_keys: adjustment_map[h][expense_keys],
                        net_keys: adjustment_map[h][net_keys],
                    }
        self.data = list(data.values())

    def _get_stock_asset_query_summary(self):
        """Get stock asset query for summary"""

        select_section = """
            0 AS total_inc,
            CAST(COALESCE(SUM(gl.debit - gl.credit), 0) AS INTEGER) AS total_exp
        """

        if self.filters.get(REPORT_TYPE) == NET_PROFIT:
            select_section = """
            CAST(0 - COALESCE(SUM(gl.debit - gl.credit), 0) AS INTEGER) AS net_profit
        """

        return f"""
        UNION ALL
        SELECT 
            {select_section},
            gl.account,
            tac.root_type
        FROM `tabGL Entry` gl
        JOIN `tabAccount` tac ON tac.name = gl.account
         {self.asset_liability_conditions}
        GROUP BY gl.account, root_type
        """

    def _get_adjustment_data_summary(self):
        """Get adjustment data for summary view"""
        

        # Create a local copy of adjustment conditions to avoid modifying the instance variable
        adjustment_conditions = self.adjustment_conditions

        if self.filters.get(REPORT_TYPE) == ONLY_INCOME:
            adjustment_conditions += " AND ia.adjustment_for = 'Income'"
        elif self.filters.get(REPORT_TYPE) == ONLY_EXPENSE:
            adjustment_conditions += " AND ia.adjustment_for = 'Expense'"

        select_section = f"""
            CAST(COALESCE(SUM(CASE WHEN ia.adjustment_for = '{INCOME}' THEN iai.credit - iai.debit ELSE 0 END), 0) AS INTEGER) AS total_inc,
            CAST(COALESCE(SUM(CASE WHEN ia.adjustment_for = '{EXPENSE_LIST[0]}' THEN iai.debit - iai.credit ELSE 0 END), 0) AS INTEGER) AS total_exp
        """

        if self.filters.get(REPORT_TYPE) == NET_PROFIT:
            select_section = f"""
                CAST((
                    COALESCE(SUM(CASE WHEN ia.adjustment_for = '{INCOME}' THEN iai.credit - iai.debit ELSE 0 END), 0)
                    -
                    COALESCE(SUM(CASE WHEN ia.adjustment_for = '{EXPENSE_LIST[0]}' THEN iai.debit - iai.credit ELSE 0 END), 0)
                ) AS INTEGER) AS total_net
            """

        group_by = "GROUP BY ia.adjustment_for , iai.account"

        query = f"""
        SELECT 
            iai.account,
            ia.adjustment_for,
            {select_section}
        FROM `tabInternal Adjustment` ia
        JOIN `tabInternal Adjustment Detail` iai ON iai.parent = ia.name
         {adjustment_conditions}
        {group_by}
        """

        # if self.filters.get("account") == "Food Distribution Expenses - HKMJ":
        #     frappe.errprint(query)
        base_params = {"from_date": self.from_date, "to_date": self.to_date}
        all_params = QueryParameterBuilder.merge_params(base_params, self.adjustment_params)
        
        results = frappe.db.sql(query, all_params, as_dict=True)
        if self.filters.get("account") == "Food Distribution Expenses - HKMJ":
            frappe.errprint(results)

        data = {}

        for row in results:
            acc = row["account"]

            if acc not in data:
                data[acc] = {
                    "account": acc,
                    income_keys: 0,
                    expense_keys: 0,
                    net_keys: 0,
                }

            # Safely add numeric values
            data[acc][income_keys] += int(row.get(income_keys, 0) or 0)
            data[acc][expense_keys] += int(row.get(expense_keys, 0) or 0)
            data[acc][net_keys] += int(row.get(net_keys, 0) or 0)
        if self.filters.get("account") == "Food Distribution Expenses - HKMJ":
            frappe.errprint(data)
        return data

    def add_empty_row(self):
        """Use centralized formatter to eliminate duplication"""
        ReportFormatter.add_empty_rows(self.data, count=4)  # Total of 4 empty rows

    def add_grand_total_row(self):
        """Use centralized formatter to eliminate duplication"""
        ReportFormatter.add_grand_total_row(
            self.data, 
            label_field="account",
            exclude_values=["Grand Total"]
        )
