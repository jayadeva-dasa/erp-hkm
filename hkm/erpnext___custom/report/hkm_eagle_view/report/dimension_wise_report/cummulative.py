import frappe

from hkm.erpnext___custom.report.hkm_eagle_view.utils.date_utils import (
    DateRangeGenerator,
)
from hkm.erpnext___custom.report.hkm_eagle_view.utils.base_report import BaseReport
from hkm.erpnext___custom.report.hkm_eagle_view.utils.sql_conditions import (
    get_ie_gl_sql_conditions,
    get_ie_adjustment_sql_conditions,
    get_al_gl_sql_conditions,
)
from hkm.erpnext___custom.report.hkm_eagle_view.utils.sql_query_builder import SQLSelectBuilder
from hkm.erpnext___custom.report.hkm_eagle_view.utils.query_optimizer import QueryParameterBuilder
from hkm.erpnext___custom.report.hkm_eagle_view.utils.constants import (
    INCOME,
    EXPENSE_LIST,
    REPORT_TYPE,
    SUMMARY,
    ONLY_INCOME,
    ONLY_EXPENSE,
    NET_PROFIT,
)
from frappe.utils import cstr


class DimensionCummulative(BaseReport):
    """
    Dimension Cumulative Report Class

    Handles the generation of cumulative reports based on dimensions.
    Supports different report types: summary, income only, expense only, and net profit.
    """

    def __init__(self, filters):
        """Initialize the report with filters and setup conditions"""
        super().__init__(filters)
        self.data = []
        self._setup_conditions()
        self._setup_keys()

    def _setup_conditions(self):
        """Setup SQL conditions for different query types (with parameterized queries)"""
        self.gl_conditions, self.gl_params = get_ie_gl_sql_conditions(
            account=self.account,
            from_date=self.from_date,
            to_date=self.to_date,
            include_stock_asset=self.include_stock_asset,
            dimension_value=self.selected_dimension_value,
            dimension_meta=self.dimension_meta,
            include_disabled_dimension=self.include_disabled_dimension,
            exclude_period_closing_entries=self.exclude_period_closing_entries,
            company=self.company,
            permission_cache=self.permission_cache,  # Use cached permissions
        )

        self.asset_liability_conditions, self.asset_liability_params = get_al_gl_sql_conditions(
            account=self.account,
            from_date=self.from_date,
            to_date=self.to_date,
            include_stock_asset=self.include_stock_asset,
            dimension_value=self.selected_dimension_value,
            dimension_meta=self.dimension_meta,
            include_disabled_dimension=self.include_disabled_dimension,
            exclude_period_closing_entries=self.exclude_period_closing_entries,
            company=self.company,
            permission_cache=self.permission_cache,  # Use cached permissions
        )

        self.adjustment_conditions, self.adjustment_params = get_ie_adjustment_sql_conditions(
            account=self.account,
            from_date=self.from_date,
            to_date=self.to_date,
            adjustment_type=self.internal_adjustment_type,
            dimension_meta=self.dimension_meta,
            dimension_value=self.selected_dimension_value,
            include_disabled_dimension=self.include_disabled_dimension,
            permission_cache=self.permission_cache,  # Use cached permissions
        )

    def _setup_keys(self):
        """Setup key names for different report types"""
        self.income_keys = "total_inc"
        self.expense_keys = "total_exp"
        self.net_keys = "total_net"
        self.adjustment_keys = []

    def get_data(self):
        """Get the processed report data"""
        self.load_data()
        if self.report_type in [ONLY_INCOME, ONLY_EXPENSE] and self.include_adjustment:
            self._add_horizontal_total(self.data)

        return self.data

    def _test_adjustment_data(self):
        """Test method to verify adjustment data processing"""
        if not self.include_adjustment:
            return

        # This method is kept for potential future debugging but with no logging
        pass

    def _add_horizontal_total(self, data):
        inc_keys = "total_inc"
        exp_keys = "total_exp"

        for d in data:

            if self.report_type == ONLY_INCOME:
                total_sum = d.get(self.income_keys, 0) or 0
                # Add adjustment values
                for adj_key in self.adjustment_keys:
                    total_sum += d.get(adj_key, 0) or 0
                d[inc_keys] = total_sum or 0
            else:
                total_sum = d.get(self.expense_keys, 0) or 0
                # Add adjustment values
                for adj_key in self.adjustment_keys:
                    total_sum += d.get(adj_key, 0) or 0
                d[exp_keys] = total_sum or 0

    def load_data(self):
        """Load and process data from database"""
        self._setup_not_tagged_head()
        self.get_summary_entries()
        self.accumulate_values_into_parents()
        self.data = list(self.heads.values())

    def _setup_not_tagged_head(self):
        """Setup the 'Not Tagged' head for untagged entries"""
        self.heads["Not Tagged"] = {
            "name": "Not Tagged",
            "parent_cost_head": None,
            "lft": 3,
            "rgt": 4,
            "is_group": 0,
            "indent": 0,
        }

    def log_sql_query(self, query, params):
        formatted = query
        for k, v in params.items():
            formatted = formatted.replace(f"%({k})s", f"'{cstr(v)}'")
        print(formatted, "Final SQL Query")
        # frappe.log_error(formatted, "Final SQL Query")

    def get_sql_select_section(self):
        """Generate SQL SELECT section based on report type (using centralized builder)"""
        return SQLSelectBuilder.get_income_expense_select(self.filters.get(REPORT_TYPE))

    def _get_stock_asset_query_summary(self):
        """Get stock asset query for summary"""
        report_type = self.filters.get(REPORT_TYPE)

        if report_type == NET_PROFIT:
            select_section = """
                CAST(0 - COALESCE(SUM(gl.debit - gl.credit), 0) AS INTEGER) AS net_profit
            """
        else:
            select_section = """
                0 AS total_inc,
                CAST(COALESCE(SUM(gl.debit - gl.credit), 0) AS INTEGER) AS total_exp
            """

        group_by = " GROUP BY head, root_type "
        if self.include_adjustment and self.report_type in [ONLY_EXPENSE, ONLY_INCOME]:
            group_by = " GROUP BY head, root_type , adjustment_type "

        return f"""
        UNION ALL
        SELECT 
            {select_section},
            COALESCE({self.dimension}, 'Not Tagged') as head,
            tac.root_type ,
            'gl_entry' as adjustment_type
        FROM `tabGL Entry` gl
        JOIN `tabAccount` tac ON tac.name = gl.account
         {self.asset_liability_conditions}
        {group_by}
        """

    def get_summary_entries(self):
        """Get summary entries from database"""
        data = {}
        self._setup_report_type_conditions()
        self._setup_group_by_clause()
        self._initialize_not_tagged_data(data)

        query = self._build_main_query()
        self._process_query_results(query, data)
        self._process_adjustments(data)
        self._update_heads_with_data(data)

    def _setup_report_type_conditions(self):
        """Setup conditions based on report type"""
        report_type = self.filters.get(REPORT_TYPE)
        if report_type == ONLY_INCOME:
            self.gl_conditions += " AND tac.root_type = 'Income'"
            if self.include_adjustment:
                self.income_keys = "total_main"
            else:
                self.income_keys = "total_inc"
        elif report_type == ONLY_EXPENSE:
            self.gl_conditions += " AND tac.root_type = 'Expense'"
            if self.include_adjustment:
                self.expense_keys = "total_main"
            else:
                self.expense_keys = "total_exp"

    def _setup_group_by_clause(self):
        """Setup GROUP BY clause based on conditions"""
        self.group_by = " GROUP BY head, tac.root_type "
        if self.include_adjustment and self.report_type in [ONLY_EXPENSE, ONLY_INCOME]:
            self.group_by = " GROUP BY head, tac.root_type , adjustment_type "

    def _initialize_not_tagged_data(self, data):
        """Initialize data for 'Not Tagged' entries"""
        data["Not Tagged"] = {
            self.dimension: "Not Tagged",
            self.income_keys: 0,
            self.expense_keys: 0,
            self.net_keys: 0,
        }

    def _build_main_query(self):
        """Build the main SQL query"""
        query = f"""
            SELECT 
                {self.get_sql_select_section().strip()}
                COALESCE({self.dimension}, 'Not Tagged') as head,
                tac.root_type,
                'gl_entry' as adjustment_type
            FROM `tabGL Entry` gl
            JOIN `tabAccount` tac ON tac.name = gl.account
             {self.gl_conditions}
            {self.group_by}
        """

        if self.include_stock_asset and self.filters.get(REPORT_TYPE) in [
            SUMMARY,
            ONLY_EXPENSE,
        ]:
            query += self._get_stock_asset_query_summary()

        return query

    def _process_query_results(self, query, data):
        """Process the results from the main query (with merged params)"""
        # Merge all parameter dictionaries
        base_params = {"from_date": self.from_date, "to_date": self.to_date}
        all_params = QueryParameterBuilder.merge_params(
            base_params, self.gl_params, self.asset_liability_params
        )


        # self.log_sql_query(query, all_params)
        
        for d in frappe.db.sql(query, all_params, as_dict=True):
            self._process_single_result(d, data)

    def _process_single_result(self, d, data):
        """Process a single result from the query"""
        head = d["head"]
        root_type = d["root_type"]
        adj_type = d["adjustment_type"]
        report_type = self.filters.get(REPORT_TYPE)

        # Initialize data structure for head if not exists
        if head not in data:
            data[head] = {
                self.income_keys: 0,
                self.expense_keys: 0,
                self.net_keys: 0,
                "adjustment_type": adj_type,
            }

        # Process values based on report type
        if report_type == NET_PROFIT:
            net_profit = int(d.get("net_profit", 0) or 0)
            data[head][self.net_keys] += net_profit
        else:
            total_inc = int(d.get("total_inc", 0) or 0)
            total_exp = int(d.get("total_exp", 0) or 0)

            if root_type == INCOME:
                data[head][self.income_keys] += total_inc
            if root_type in EXPENSE_LIST:
                data[head][self.expense_keys] += total_exp

    def _process_adjustments(self, data):
        """Process adjustment data if enabled"""
        if not self.include_adjustment:
            return

        adjustment_map = self._get_adjustment_data_summary()

        if self.report_type in [ONLY_EXPENSE, ONLY_INCOME] and self.include_adjustment:
            self._process_specific_adjustments(data, adjustment_map)
        else:
            self._process_general_adjustments(data, adjustment_map)

    def _process_general_adjustments(self, data, adjustment_map):
        """Process adjustments for general report types"""

        print(adjustment_map, "adjustment_map")
        print(data, "data")
        for h in adjustment_map:

            if h in data:
            
                data[h][self.income_keys] += adjustment_map[h]["total_inc"]
                data[h][self.expense_keys] += adjustment_map[h]["total_exp"]
                data[h][self.net_keys] += adjustment_map[h]["total_net"]
            else:
                data[h] = {
                    self.income_keys: adjustment_map[h]["total_inc"],
                    self.expense_keys: adjustment_map[h]["total_exp"],
                    self.net_keys: adjustment_map[h]["total_net"],
                }

    def _process_specific_adjustments(self, data, adjustment_map):
        """Process adjustments for specific report types (income/expense only)"""

        for key, adjustment_data in adjustment_map.items():
            head, adj_type = key.split("_", 1)

            adjustment_value = 0
            key_suffix = f"total_{adj_type}_adj"

            if key_suffix not in self.adjustment_keys:
                self.adjustment_keys.append(key_suffix)
            if head not in data:
                data[head] = {
                    self.income_keys: 0,
                    self.expense_keys: 0,
                    self.net_keys: 0,
                }

            if key_suffix not in data[head]:
                data[head][key_suffix] = 0

            if self.report_type == ONLY_INCOME:
                adjustment_value = adjustment_map[key].get("total_inc", 0) or 0
            else:
                adjustment_value = adjustment_map[key].get("total_exp", 0) or 0

            data[head][key_suffix] += adjustment_value

    def _update_heads_with_data(self, data):
        """Update heads with processed data"""
        for h in self.heads:
            if h in data and not self.has_children(h):
                self.heads[h].update(data[h])
                # if h == "BrajRas Rasoi" :
                # frappe.errprint(self.heads[h])

    def _get_adjustment_data_summary(self):
        """Get adjustment data for summary view"""

        adjustment_map = {}
        adjustment_conditions = self.adjustment_conditions
        report_type = self.filters.get(REPORT_TYPE)

        # Add report type specific conditions
        if report_type == ONLY_INCOME:
            adjustment_conditions += " AND ia.adjustment_for = 'Income'"
        elif report_type == ONLY_EXPENSE:
            adjustment_conditions += " AND ia.adjustment_for = 'Expense'"

        group_by = " GROUP BY head"
        if self.include_adjustment and self.report_type in [ONLY_EXPENSE, ONLY_INCOME]:
            group_by = " GROUP BY head, ia.adjustment_for , adjustment_type "

        select_section = self._get_adjustment_select_section()

        query = f"""
        SELECT 
            iai.{self.dimension} as head,
            ia.adjustment_for,
            ia.type as adjustment_type,
            {select_section}
        FROM `tabInternal Adjustment` ia
        JOIN `tabInternal Adjustment Detail` iai ON iai.parent = ia.name
         {adjustment_conditions}
        {group_by}
        """

        # Merge base params with adjustment params
        base_params = {"from_date": self.from_date, "to_date": self.to_date}
        all_params = QueryParameterBuilder.merge_params(base_params, self.adjustment_params)
        
        
        # self.log_sql_query(query, all_params)
        results = frappe.db.sql(query, all_params, as_dict=True)

        # print(results, "results")
        if self.include_adjustment and self.report_type in [ONLY_EXPENSE, ONLY_INCOME]:
            for row in results:
                # Handle None values for head and adjustment_type
                head = row.get("head") or "Not Tagged"
                adjustment_type = row.get("adjustment_type")
                
                if not adjustment_type:
                    continue  # Skip rows without adjustment type
                
                row["adjustment_type"] = frappe.scrub(adjustment_type)
                key = head + "_" + row["adjustment_type"]

                if key not in adjustment_map:
                    adjustment_map[key] = {
                        "adjustment_type": row["adjustment_type"],
                        "total_inc": 0,
                        "total_exp": 0,
                        "total_net": 0,
                    }

                adjustment_map[key]["total_inc"] += int(row.get("total_inc", 0) or 0)
                adjustment_map[key]["total_exp"] += int(row.get("total_exp", 0) or 0)
                adjustment_map[key]["total_net"] += int(row.get("net_profit", 0) or 0)
        else:
            adjustment_map = {
                row["head"]: {
                    "adjustment_type": "gl_entry",
                    "total_inc": int(row.get("total_inc", 0) or 0),
                    "total_exp": int(row.get("total_exp", 0) or 0),
                    "total_net": int(row.get("net_profit", 0) or 0),
                }
                for row in results
            }

        return adjustment_map

    def _get_adjustment_select_section(self):
        """Get the SELECT section for adjustment queries"""
        report_type = self.filters.get(REPORT_TYPE)

        if report_type == NET_PROFIT:
            return f"""
                CAST((
                    COALESCE(SUM(CASE WHEN ia.adjustment_for = '{INCOME}' THEN iai.credit - iai.debit ELSE 0 END), 0)
                    -
                    COALESCE(SUM(CASE WHEN ia.adjustment_for = '{EXPENSE_LIST[0]}' THEN iai.debit - iai.credit ELSE 0 END), 0)
                ) AS INTEGER) AS net_profit
            """
        else:
            return f"""
                CAST(COALESCE(SUM(CASE WHEN ia.adjustment_for = '{INCOME}' THEN iai.credit - iai.debit ELSE 0 END), 0) AS INTEGER) AS total_inc,
                CAST(COALESCE(SUM(CASE WHEN ia.adjustment_for = '{EXPENSE_LIST[0]}' THEN iai.debit - iai.credit ELSE 0 END), 0) AS INTEGER) AS total_exp
            """

    def accumulate_values_into_parents(self):
        """Accumulate values from children to parent heads"""
        # Parent fields use scrubbed doctype name, not fieldname
        parent_field = "parent_" + frappe.scrub(self.dimension_meta.name)
        current_report_type = self.filters.get("report_type")

        for head, data in reversed(list(self.heads.items())):
            parent_name = data.get(parent_field)
            # Parent fields are already normalized to None in BaseReport
            if parent_name and parent_name in self.heads:
                parent = self.heads[parent_name]

                if current_report_type == NET_PROFIT:
                    self._accumulate_net_profit_values(parent, data)
                elif current_report_type == SUMMARY:
                    self._accumulate_income_expense_values(parent, data)
                elif current_report_type == ONLY_INCOME:
                    self._accumulate_income_values(parent, data)
                elif current_report_type == ONLY_EXPENSE:
                    self._accumulate_expense_values(parent, data)

    def _accumulate_net_profit_values(self, parent, data):
        """Accumulate net profit values"""
        if self.net_keys not in parent:
            parent[self.net_keys] = 0
        parent[self.net_keys] += data.get(self.net_keys, 0)

    def _accumulate_income_expense_values(self, parent, data):
        """Accumulate income and expense values"""
        if self.income_keys not in parent:
            parent[self.income_keys] = 0
        parent[self.income_keys] += data.get(self.income_keys, 0)

        if self.expense_keys not in parent:
            parent[self.expense_keys] = 0
        parent[self.expense_keys] += data.get(self.expense_keys, 0)

    def _accumulate_income_values(self, parent, data):
        """Accumulate income values"""
        # Accumulate adjustment values
        if self.include_adjustment:
            for adj_key in self.adjustment_keys:
                if adj_key not in parent:
                    parent[adj_key] = 0
                parent[adj_key] += data.get(adj_key, 0)

        # Accumulate main income values
        if self.income_keys not in parent:
            parent[self.income_keys] = 0
        parent[self.income_keys] += data.get(self.income_keys, 0)

    def _accumulate_expense_values(self, parent, data):
        """Accumulate expense values"""
        # Accumulate adjustment values
        if self.include_adjustment:
            for adj_key in self.adjustment_keys:
                if adj_key not in parent:
                    parent[adj_key] = 0
                parent[adj_key] += data.get(adj_key, 0)

        # Accumulate main expense values
        if self.expense_keys not in parent:
            parent[self.expense_keys] = 0
        parent[self.expense_keys] += data.get(self.expense_keys, 0)
