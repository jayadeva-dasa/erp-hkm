import select
import frappe
from frappe import _

from hkm.erpnext___custom.report.hkm_eagle_view.utils.base_report import BaseReport
from hkm.erpnext___custom.report.hkm_eagle_view.utils.sql_conditions import (
    get_ie_gl_sql_conditions,
    get_ie_adjustment_sql_conditions,
    get_al_gl_sql_conditions,
)
from hkm.erpnext___custom.report.hkm_eagle_view.utils.query_optimizer import QueryParameterBuilder
from hkm.erpnext___custom.report.hkm_eagle_view.utils.report_formatters import ReportFormatter
from hkm.erpnext___custom.report.hkm_eagle_view.utils.constants import (
    INCOME,
    EXPENSE_LIST,
    REPORT_TYPE,
    DETAILED_INCOME,
    DETAILED_EXPENSE,
)
from hkm.erpnext___custom.report.hkm_eagle_view.utils.file_processors import (
    FileProcessor,
)


class VoucherWise(BaseReport):
    def __init__(self, filters):
        super().__init__(filters)
        self.data = []
        self.adjustment_data = []
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

        return self.data

    def load_data(self):
        """Load data from database"""
        self._get_detailed_gl_entries()
        self.data = self._get_detailed_data()

    def _get_accounting_dimension(self, prefix):
        """Get accounting dimension"""

        dimesnion_selected = ""
        for i in self.accounting_dimension:
            dimesnion_selected += f"COALESCE({prefix}{i}, '') AS {i},"

        return dimesnion_selected

    def _get_detailed_gl_entries(self):
        """Get detailed GL entries"""
        conditions = self.gl_conditions

        if self.report_type == DETAILED_INCOME:
            conditions += f"AND tac.root_type = '{INCOME}'"
        elif self.report_type == DETAILED_EXPENSE:
            conditions += f"AND tac.root_type = '{EXPENSE_LIST[0]}'"

        if self.hide_not_tagged_entries:
            conditions += f"AND gl.{self.dimension} IS NOT NULL AND TRIM(gl.{self.dimension}) != ''"

        query = f"""
            SELECT 
                gl.posting_date,
                gl.voucher_type,
                gl.voucher_no,
                gl.company,
                gl.account,
                gl.remarks,
                gl.{self.dimension} as head,
                {self._get_select_logic_for_detailed()},
                {self._get_accounting_dimension("gl.")}
                JSON_ARRAYAGG(
                    JSON_OBJECT(
                        'file_name', f.file_name,
                        'url', f.file_url
                    )
                ) AS files
            FROM `tabGL Entry` gl
            JOIN `tabAccount` tac ON tac.name = gl.account
             LEFT JOIN `tabFile` f 
                ON f.attached_to_name = gl.voucher_no 
                AND f.attached_to_doctype = gl.voucher_type
             {conditions}
            GROUP BY gl.name
        """

        if self.include_stock_asset and self.report_type == DETAILED_EXPENSE:
            query += self._get_stock_asset_results_detailed()

        # Merge params for parameterized query
        base_params = {"from_date": self.from_date, "to_date": self.to_date}
        all_params = QueryParameterBuilder.merge_params(
            base_params, self.gl_params, self.asset_liability_params
        )
        
        self.data = frappe.db.sql(query, all_params, as_dict=True)

        # Fetch adjustment data separately if needed
        if self.include_adjustment:
            self.adjustment_data = self._get_adjustment_data_detailed()
        else:
            self.adjustment_data = []

    def _get_stock_asset_results_detailed(self):
        """Get stock asset results for detailed view"""
        conditions = self.asset_liability_conditions

        if self.hide_not_tagged_entries:
            conditions += f"AND gl.{self.dimension} IS NOT NULL AND TRIM(gl.{self.dimension}) != ''"

        return f"""
        UNION ALL
        SELECT 
           gl.posting_date,
            gl.voucher_type,
            gl.voucher_no,
            gl.company,
            CASE
                WHEN gl.account LIKE '%%Asset Received But Not Billed%%' THEN "Asset Purchased" 
                WHEN gl.account LIKE '%%Stock Received But Not Billed%%' THEN "Stock Purchased"
                ELSE gl.account
            END as account,
            gl.remarks,
            gl.{self.dimension} as head,
            gl.debit - gl.credit as amount,
            {self._get_accounting_dimension("gl.")}
            JSON_ARRAYAGG(
                JSON_OBJECT(
                    'file_name', f.file_name,
                    'url', f.file_url
                )
            ) AS files
        FROM `tabGL Entry` gl
        JOIN `tabAccount` tac ON tac.name = gl.account
        LEFT JOIN `tabFile` f 
            ON f.attached_to_name = gl.voucher_no 
            AND f.attached_to_doctype = gl.voucher_type
        {conditions}
        GROUP BY gl.name
        """

    def _get_select_logic_for_detailed(self):
        """Get select logic for detailed view"""
        if self.report_type == DETAILED_INCOME:
            return f"CASE WHEN tac.root_type = '{INCOME}' THEN gl.credit - gl.debit ELSE 0 END as amount"
        elif self.report_type == DETAILED_EXPENSE:
            return f"CASE WHEN tac.root_type = '{EXPENSE_LIST[0]}' THEN gl.debit - gl.credit ELSE 0 END as amount"
        else:
            return f"CASE WHEN tac.root_type = '{INCOME}' THEN gl.credit - gl.debit ELSE gl.debit - gl.credit END as amount"

    def _get_adjustment_data_detailed(self):
        """Get adjustment data for detailed view"""

        select_logic = self._get_adjustment_select_logic()

        conditions = self.adjustment_conditions

        if self.report_type == DETAILED_INCOME:
            conditions += f"AND ia.adjustment_for = '{INCOME}'"
        elif self.report_type == DETAILED_EXPENSE:
            conditions += f"AND ia.adjustment_for = '{EXPENSE_LIST[0]}'"

        if self.hide_not_tagged_entries:
            conditions += f"AND iai.{self.dimension} IS NOT NULL AND TRIM(iai.{self.dimension}) != ''"

        query = f"""
        SELECT 
            ia.adjustment_for,
            COALESCE(iai.{self.dimension}, "Not Tagged") as head,
            ia.posting_date,
            ia.name,
            ia.remarks,
            iai.account AS account,
            {self._get_accounting_dimension("iai.")}
            {select_logic}
        FROM `tabInternal Adjustment` ia
        JOIN `tabInternal Adjustment Detail` iai ON iai.parent = ia.name
         {conditions}
        GROUP BY iai.name
        """

        base_params = {"from_date": self.from_date, "to_date": self.to_date}
        all_params = QueryParameterBuilder.merge_params(base_params, self.adjustment_params)
        
        return frappe.db.sql(query, all_params, as_dict=True)

    def _get_adjustment_select_logic(self):
        """Get select logic for adjustment queries"""
        if self.filters.get("report_type") == DETAILED_INCOME:
            return """
            SUM(
                  iai.credit - iai.debit 
                ) AS amount
            """
        elif self.filters.get("report_type") == DETAILED_EXPENSE:
            return """
            SUM(
                   iai.debit - iai.credit 
                ) AS amount
            """
        return "0 AS amount"

    def _get_detailed_data(self):
        """Get data for detailed reports"""
        final_data = []

        # Process GL entries
        for row in self.data:
            files_html = FileProcessor.process_files(row.get("files") or "[]")
            voucher_no_link = FileProcessor.create_voucher_link(
                row.get("voucher_type"), row.get("voucher_no")
            )
            dict = {
                "posting_date": row.get("posting_date"),
                "voucher_type": row.get("voucher_type"),
                "voucher_no": voucher_no_link,
                "company": row.get("company"),
                self.dimension: row.get("head") or "Not Tagged",
                "account_head": row.get("account"),
                "amount": row.get("amount", 0),
                "files_html": files_html,
                "remarks": row.get("remarks"),
            }
            for i in self.accounting_dimension:
                dict[i] = row.get(i)

            final_data.append(dict)

        # Process adjustment entries if included
        if self.include_adjustment and self.adjustment_data:
            for d in self.adjustment_data:
                voucher_no_link = FileProcessor.create_voucher_link(
                    "Internal Adjustment", d.get("name")
                )
                dict = {
                    "posting_date": d.get("posting_date"),
                    "voucher_type": "Internal Adjustment",
                    "voucher_no": voucher_no_link,
                    "company": "Expense Load",
                    self.dimension: d.get("head") or "Not Tagged",
                    "account_head": d.get("account"),
                    "amount": d.get("amount", 0),
                    "files_html": "No File",
                    "remarks": "IAEC :- " + (d.get("remarks") or ""),
                }
                for i in self.accounting_dimension:
                    dict[i] = d.get(i)

                final_data.append(dict)

        # Add empty rows and total
        self._add_empty_rows_and_total(final_data)

        return final_data

    def _add_empty_rows_and_total(self, final_data):
        """Add empty rows and total to detailed data (using centralized formatter)"""
        # Add empty rows
        ReportFormatter.add_empty_rows(final_data, count=2)

        # Add total row
        total = sum([d.get("amount", 0) for d in final_data if d.get("amount")])
        total_row = {
            "posting_date": "Total",
            "voucher_type": "",
            "voucher_no": "",
            "company": "",
            self.dimension: "",
            "account_head": "",
            "amount": total,
            "files_html": "",
            "remarks": "",
        }
        for i in self.accounting_dimension:
            total_row[i] = ""

        final_data.append(total_row)
