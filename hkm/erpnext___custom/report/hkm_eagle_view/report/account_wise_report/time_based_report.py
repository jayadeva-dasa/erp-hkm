# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe
from hkm.erpnext___custom.report.hkm_eagle_view.utils.base_report import BaseReport
from hkm.erpnext___custom.report.hkm_eagle_view.utils.sql_conditions import (
    get_ie_gl_sql_conditions,
    get_ie_adjustment_sql_conditions,
    get_al_gl_sql_conditions,
)
from hkm.erpnext___custom.report.hkm_eagle_view.utils.query_optimizer import QueryParameterBuilder
from hkm.erpnext___custom.report.hkm_eagle_view.utils.constants import (
    ONLY_INCOME,
    ONLY_EXPENSE,
    SUMMARY,
    NET_PROFIT,
)
from hkm.erpnext___custom.report.hkm_eagle_view.utils.account_data_processor import (
    AccountWiseReportDataProcessor,
)
from hkm.erpnext___custom.report.hkm_eagle_view.utils.account_wise_total_handler import (
    AccountWiseTotalHandler,
)
from hkm.erpnext___custom.report.hkm_eagle_view.utils.account_wise_empty_row_handler import (
    AccountWiseEmptyRowHandler,
)


class TimeBasedReport(BaseReport):
    """Base class for time-based reports (day, week, month, quarter)"""

    def __init__(self, filters, time_periods):
        super().__init__(filters)
        self.data = {}
        self.not_tagged_entry = []
        self.time_periods = time_periods
        self._initialize_conditions()

    def _initialize_conditions(self):
        """Initialize SQL conditions (with parameterized queries)"""
        self.gl_conditions, self.gl_params = get_ie_gl_sql_conditions(
            account=self.account,
            include_stock_asset=self.include_stock_asset,
            dimension_value=self.selected_dimension_value,
            dimension_meta=self.dimension_meta,
            exclude_period_closing_entries=self.exclude_period_closing_entries,
            company=self.company,
            permission_cache=self.permission_cache,
        )
        self.asset_liability_conditions, self.asset_liability_params = get_al_gl_sql_conditions(
            account=self.account,
            include_stock_asset=self.include_stock_asset,
            dimension_value=self.selected_dimension_value,
            dimension_meta=self.dimension_meta,
            exclude_period_closing_entries=self.exclude_period_closing_entries,
            company=self.company,
            permission_cache=self.permission_cache,
        )
        self.adjustment_conditions, self.adjustment_params = get_ie_adjustment_sql_conditions(
            account=self.account,
            adjustment_type=self.internal_adjustment_type,
            dimension_meta=self.dimension_meta,
            dimension_value=self.selected_dimension_value,
            permission_cache=self.permission_cache,
        )

    def get_data(self):
        """Get data for the report"""
        self.load_data()
        self.data = list(self.data.values())

        # Initialize utility handlers
        total_handler = AccountWiseTotalHandler(
            report_type=self.report_type,
            inc_keys=self.inc_keys,
            exp_keys=self.exp_keys,
            net_keys=self.net_keys,
            adj_inc_keys=self.adj_inc_keys,
            adj_exp_keys=self.adj_exp_keys,
        )

        empty_row_handler = AccountWiseEmptyRowHandler(
            report_type=self.report_type, time_periods=self.time_periods
        )

        # Add horizontal totals
        total_handler.add_horizontal_total(self.data)

        # Add empty rows
        self.data = empty_row_handler.add_empty_rows(self.data, self.not_tagged_entry)

        self.inc_keys = set(self.inc_keys)
        self.exp_keys = set(self.exp_keys)
        self.net_keys = set(self.net_keys)
        self.adj_inc_keys = set(self.adj_inc_keys)
        self.adj_exp_keys = set(self.adj_exp_keys)

        # Add final total row
        total_handler.add_final_total_row(self.data)

        return self.data

    def build_base_gl_query(self, gl_conditions, period):
        """Build base GL query with common logic"""
        conditions = gl_conditions

        if self.report_type == ONLY_INCOME:
            conditions += " AND tac.root_type = 'Income'"
        elif self.report_type == ONLY_EXPENSE:
            conditions += " AND tac.root_type = 'Expense'"

        group_by = " GROUP BY gl.account, tac.root_type "
        if self.include_adjustment and self.report_type in [ONLY_EXPENSE, ONLY_INCOME]:
            group_by = " GROUP BY gl.account, tac.root_type , adjustment_type "

        date_condition = self._get_date_condition(period)

        return f"""
        SELECT gl.account, tac.root_type, {self.dimension} as head ,
        SUM(gl.debit) as sum_debit, SUM(gl.credit) as sum_credit ,
        'gl_entry' as adjustment_type
        FROM `tabGL Entry` gl   
        JOIN `tabAccount` tac ON tac.name = gl.account
        {conditions}
        {date_condition}
        {group_by}
        """

    def build_stock_asset_query(self, asset_liability_conditions, period):
        """Build stock/asset query"""
        group_by = " GROUP BY gl.account, tac.root_type "
        if self.include_adjustment and self.report_type in [ONLY_EXPENSE, ONLY_INCOME]:
            group_by = " GROUP BY gl.account, tac.root_type , adjustment_type "

        date_condition = self._get_date_condition(period)

        return f"""
        UNION ALL
        SELECT gl.account as account, tac.root_type, {self.dimension} as head ,
        SUM(gl.debit) as sum_debit, SUM(gl.credit) as sum_credit ,
        'gl_entry' as adjustment_type 
        FROM `tabGL Entry` gl
        JOIN `tabAccount` tac ON tac.name = gl.account
        {asset_liability_conditions}
        {date_condition}
        {group_by}
        """

    def build_adjustment_query(self, adjustment_conditions, period):
        """Build adjustment query"""
        conditions = adjustment_conditions

        if self.report_type == ONLY_INCOME:
            conditions += " AND ia.adjustment_for = 'Income'"
        elif self.report_type == ONLY_EXPENSE:
            conditions += " AND ia.adjustment_for = 'Expense'"

        group_by = " GROUP BY iai.account, ia.adjustment_for "
        if self.include_adjustment and self.report_type in [ONLY_EXPENSE, ONLY_INCOME]:
            group_by = " GROUP BY iai.account, ia.adjustment_for , adjustment_type "

        date_condition = self._get_date_condition(period, adjustment=True)

        return f"""
        UNION ALL
        SELECT 
        iai.account as account,
        ia.adjustment_for as root_type,
        {self.dimension} as head,
        SUM(iai.debit) as sum_debit,
        SUM(iai.credit) as sum_credit,
        ia.type as adjustment_type
        FROM `tabInternal Adjustment` ia
        JOIN `tabInternal Adjustment Detail` iai ON iai.parent = ia.name
        {conditions}
        {date_condition}
        {group_by}
        """

    def _get_date_condition(self, period, adjustment=False):
        """Get date condition based on period type - to be overridden by subclasses"""
        raise NotImplementedError("Subclasses must implement _get_date_condition")
    
    def _get_period_param_prefix(self):
        """Get parameter prefix based on report type - to be overridden by subclasses"""
        return "period"

    def load_data(self):
        """Load data from database (with parameterized queries)"""
        for period in self.time_periods:
            query = self.build_base_gl_query(self.gl_conditions, period)

            if self.include_stock_asset:
                result = self.build_stock_asset_query(
                    self.asset_liability_conditions, period
                )
                query += result

            if self.include_adjustment:
                query += self.build_adjustment_query(self.adjustment_conditions, period)

            # Merge all parameter dictionaries and add period dates
            all_params = QueryParameterBuilder.merge_params(
                self.gl_params, 
                self.asset_liability_params, 
                self.adjustment_params
            )
            
            # Add date parameters for this period
            prefix = self._get_period_param_prefix()
            all_params[f"{prefix}_{period.key}_start"] = period.start_date
            all_params[f"{prefix}_{period.key}_end"] = period.end_date

            results = frappe.db.sql(query, all_params, as_dict=True)
            results = self.add_not_tagged_entry(results)

            for entry in results:
                (
                    self.data,
                    self.inc_keys,
                    self.exp_keys,
                    self.net_keys,
                    self.adj_inc_keys,
                    self.adj_exp_keys,
                ) = AccountWiseReportDataProcessor(
                    filters=self.filters,
                    data=self.data,
                    inc_keys=self.inc_keys,
                    exp_keys=self.exp_keys,
                    net_keys=self.net_keys,
                    adj_inc_keys=self.adj_inc_keys,
                    adj_exp_keys=self.adj_exp_keys,
                    entry=entry,
                    main_key=period.key,
                ).get_data()

    def add_not_tagged_entry(self, results):
        """Add not tagged entries to results"""
        special_entry = []
        for entry in results:
            if entry.get("head"):
                continue
            else:
                account = "Not Tagged"
                root_type = entry.get("root_type")
                head = "Not Tagged"
                sum_debit = entry.get("sum_debit")
                sum_credit = entry.get("sum_credit")
                adjustment_type = entry.get("adjustment_type")
                special_entry.append(
                    frappe._dict(
                        account=account,
                        root_type=root_type,
                        head=head,
                        sum_debit=sum_debit,
                        sum_credit=sum_credit,
                        adjustment_type=adjustment_type,
                    )
                )
        results.extend(special_entry)
        self.not_tagged_entry = special_entry
        return results
