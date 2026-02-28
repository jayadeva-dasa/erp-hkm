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
    INCOME,
    EXPENSE_LIST,
)
from hkm.erpnext___custom.report.hkm_eagle_view.utils.dimension_report_data_processor import (
    DimensionWiseReportDataProcessor,
)
from hkm.erpnext___custom.report.hkm_eagle_view.utils.dimension_wise_total_handler import (
    DimensionWiseTotalHandler,
)
from hkm.erpnext___custom.report.hkm_eagle_view.utils.dimension_wise_empty_row_handler import (
    DimensionWiseEmptyRowHandler,
)


class TimeBasedReport(BaseReport):
    """Base class for time-based reports (day, week, month, quarter)"""

    def __init__(self, filters, time_periods):
        super().__init__(filters)
        self.data = {}
        self.time_periods = time_periods
        self._initialize_conditions()
        self._initialize_gl_processor()

    def _initialize_conditions(self):
        """Initialize SQL conditions (with parameterized queries)"""
        self.gl_conditions, self.gl_params = get_ie_gl_sql_conditions(
            account=self.account,
            include_stock_asset=self.include_stock_asset,
            dimension_value=self.selected_dimension_value,
            dimension_meta=self.dimension_meta,
            include_disabled_dimension=self.include_disabled_dimension,
            exclude_period_closing_entries=self.exclude_period_closing_entries,
            company=self.company,
            permission_cache=self.permission_cache,
        )
        self.asset_liability_conditions, self.asset_liability_params = get_al_gl_sql_conditions(
            account=self.account,
            include_stock_asset=self.include_stock_asset,
            dimension_value=self.selected_dimension_value,
            dimension_meta=self.dimension_meta,
            include_disabled_dimension=self.include_disabled_dimension,
            exclude_period_closing_entries=self.exclude_period_closing_entries,
            company=self.company,
            permission_cache=self.permission_cache,
        )
        self.adjustment_conditions, self.adjustment_params = get_ie_adjustment_sql_conditions(
            account=self.account,
            adjustment_type=self.internal_adjustment_type,
            dimension_meta=self.dimension_meta,
            dimension_value=self.selected_dimension_value,
            include_disabled_dimension=self.include_disabled_dimension,
            permission_cache=self.permission_cache,
        )

    def _initialize_gl_processor(self):
        """Initialize GL entry processor"""
        self.gl_processor = DimensionWiseReportDataProcessor(
            report_type=self.report_type,
            include_adjustment=self.include_adjustment,
            internal_adjustment_type=self.internal_adjustment_type,
        )

    def get_data(self):
        """Get data for the report"""
        self.load_data()
        self.data = list(self.heads.values())

        # Get key lists from GL processor
        key_lists = self.gl_processor.get_key_lists()
        self.inc_keys = key_lists["inc_keys"]
        self.exp_keys = key_lists["exp_keys"]
        self.net_keys = key_lists["net_keys"]
        self.adj_inc_keys = key_lists["adj_inc_keys"]
        self.adj_exp_keys = key_lists["adj_exp_keys"]

        total_handler = DimensionWiseTotalHandler(
            report_type=self.report_type,
            inc_keys=self.inc_keys,
            exp_keys=self.exp_keys,
            net_keys=self.net_keys,
            adj_inc_keys=self.adj_inc_keys,
            adj_exp_keys=self.adj_exp_keys,
            dimension=self.dimension,
            dimension_value=self.selected_dimension_value,
            dimension_meta=self.dimension_meta,
            include_disabled_dimension=self.include_disabled_dimension,
        )

        empty_row_handler = DimensionWiseEmptyRowHandler(
            report_type=self.report_type, time_periods=self.time_periods
        )
        total_handler.add_horizontal_total(self.data)
        not_tagged = 0

        if any(row["name"] == "Not Tagged" for row in self.data):
            not_tagged = 1

        self.data = empty_row_handler.add_empty_rows(self.data, not_tagged)

        total_handler.add_final_total_row(self.data, self.tree)
        return self.data

    def build_base_gl_query(self, gl_conditions, period):
        """Build base GL query with common logic"""
        conditions = gl_conditions

        if self.report_type == ONLY_INCOME:
            conditions += " AND tac.root_type = 'Income'"
        elif self.report_type == ONLY_EXPENSE:
            conditions += " AND tac.root_type = 'Expense'"

        group_by = " GROUP BY head, tac.root_type "
        if self.include_adjustment and self.report_type in [ONLY_EXPENSE, ONLY_INCOME]:
            group_by = " GROUP BY head, tac.root_type , adjustment_type "

        date_condition = self._get_date_condition(period)

        return f"""
        SELECT tac.root_type, COALESCE({self.dimension}, 'Not Tagged') as head ,
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
        group_by = " GROUP BY head, tac.root_type "
        if self.include_adjustment and self.report_type in [ONLY_EXPENSE, ONLY_INCOME]:
            group_by = " GROUP BY head, tac.root_type , adjustment_type "

        date_condition = self._get_date_condition(period)

        return f"""
        UNION ALL
        SELECT tac.root_type, COALESCE({self.dimension}, 'Not Tagged') as head ,
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

        group_by = " GROUP BY head, ia.adjustment_for "
        if self.include_adjustment and self.report_type in [ONLY_EXPENSE, ONLY_INCOME]:
            group_by = " GROUP BY head, ia.adjustment_for , adjustment_type "

        date_condition = self._get_date_condition(period, adjustment=True)

        return f"""
        UNION ALL
        SELECT 
        ia.adjustment_for as root_type,
        COALESCE({self.dimension}, 'Not Tagged') as head,
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

    def load_data(self):
        self.get_monthwise_gl_entries()
        self.accumulate_values_into_parents()

    def get_monthwise_gl_entries(self):
        """Get GL entries grouped by months"""
        """Load data from database"""

        data = {}
        # Get the correct fieldname from Accounting Dimension doctype
        dimension_doctype = self.filters.get("dimension")
        dimension = frappe.db.get_value("Accounting Dimension", {"document_type": dimension_doctype}, "fieldname")
        if not dimension:
            # Fallback to scrubbed name if not found in Accounting Dimension
            dimension = frappe.scrub(dimension_doctype)

        for period in self.time_periods:
            self.process_time_period_data(period, data)

        for h in self.heads:
            if h in data and not self.has_children(h):
                self.heads[h].update(data[h])

    def process_time_period_data(self, period, data):
        """Process time period data (with parameterized queries)"""
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

        for entry in results:
            self.gl_processor.process_gl_entry(entry, period, data)
    
    def _get_period_param_prefix(self):
        """Get parameter prefix based on report type"""
        # This should be overridden by subclasses (qtr, month, week, day)
        return "period"

    def accumulate_values_into_parents(self):
        """Accumulate children's values in parent heads"""
        self.gl_processor.accumulate_values_into_parents(
            self.heads, self.time_periods, self.dimension_meta
        )
