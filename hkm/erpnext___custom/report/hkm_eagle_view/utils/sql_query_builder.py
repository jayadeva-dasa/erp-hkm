# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

"""
SQL Query Builder Utilities for Eagle View Report

Centralizes duplicate SQL query building logic to eliminate code redundancy
and make maintenance easier.
"""

import frappe
from hkm.erpnext___custom.report.hkm_eagle_view.utils.constants import (
    INCOME,
    EXPENSE_LIST,
    ONLY_INCOME,
    ONLY_EXPENSE,
    NET_PROFIT,
    SUMMARY
)


class SQLSelectBuilder:
    """
    Centralized SQL SELECT section builder.
    
    Eliminates 90% code duplication between account_wise and dimension_wise reports.
    """
    
    @staticmethod
    def get_income_expense_select(report_type: str) -> str:
        """
        Get SELECT section for income/expense reports.
        
        Args:
            report_type: One of ONLY_INCOME, ONLY_EXPENSE, NET_PROFIT, SUMMARY
            
        Returns:
            SQL SELECT section string
            
        Example:
            >>> SQLSelectBuilder.get_income_expense_select(ONLY_INCOME)
            "CAST(COALESCE(SUM(CASE WHEN tac.root_type = 'Income' 
                THEN gl.credit - gl.debit ELSE 0 END), 0) AS INTEGER) AS total_inc,
             0 AS total_exp,"
        """
        if report_type == ONLY_INCOME:
            return f""" 
                CAST(COALESCE(SUM(CASE WHEN tac.root_type = '{INCOME}' 
                    THEN gl.credit - gl.debit ELSE 0 END), 0) AS INTEGER) AS total_inc,
                0 AS total_exp,
            """
        
        elif report_type == ONLY_EXPENSE:
            return f""" 
                0 AS total_inc,
                CAST(COALESCE(SUM(CASE WHEN tac.root_type = '{EXPENSE_LIST[0]}' 
                    THEN gl.debit - gl.credit ELSE 0 END), 0) AS INTEGER) AS total_exp,
            """
        
        elif report_type == NET_PROFIT:
            return f""" 
                CAST((
                    COALESCE(SUM(CASE WHEN tac.root_type = '{INCOME}' 
                        THEN gl.credit - gl.debit ELSE 0 END), 0)
                    -
                    COALESCE(SUM(CASE WHEN tac.root_type = '{EXPENSE_LIST[0]}' 
                        THEN gl.debit - gl.credit ELSE 0 END), 0)
                ) AS INTEGER) AS net_profit,
            """
        
        else:  # SUMMARY
            return f""" 
                CAST(COALESCE(SUM(CASE WHEN tac.root_type = '{INCOME}' 
                    THEN gl.credit - gl.debit ELSE 0 END), 0) AS INTEGER) AS total_inc,
                CAST(COALESCE(SUM(CASE WHEN tac.root_type = '{EXPENSE_LIST[0]}' 
                    THEN gl.debit - gl.credit ELSE 0 END), 0) AS INTEGER) AS total_exp,
            """
    
    @staticmethod
    def get_adjustment_select(report_type: str) -> str:
        """
        Get SELECT section for adjustment (Internal Adjustment) queries.
        
        Args:
            report_type: One of ONLY_INCOME, ONLY_EXPENSE, NET_PROFIT, SUMMARY
            
        Returns:
            SQL SELECT section string for adjustment queries
        """
        if report_type == NET_PROFIT:
            return f"""
                CAST((
                    COALESCE(SUM(CASE WHEN ia.adjustment_for = '{INCOME}' 
                        THEN iai.credit - iai.debit ELSE 0 END), 0)
                    -
                    COALESCE(SUM(CASE WHEN ia.adjustment_for = '{EXPENSE_LIST[0]}' 
                        THEN iai.debit - iai.credit ELSE 0 END), 0)
                ) AS INTEGER) AS net_profit
            """
        else:
            return f"""
                CAST(COALESCE(SUM(CASE WHEN ia.adjustment_for = '{INCOME}' 
                    THEN iai.credit - iai.debit ELSE 0 END), 0) AS INTEGER) AS total_inc,
                CAST(COALESCE(SUM(CASE WHEN ia.adjustment_for = '{EXPENSE_LIST[0]}' 
                    THEN iai.debit - iai.credit ELSE 0 END), 0) AS INTEGER) AS total_exp
            """
    
    @staticmethod
    def get_stock_asset_select(report_type: str) -> str:
        """
        Get SELECT section for stock/asset liability queries.
        
        Args:
            report_type: One of ONLY_EXPENSE, NET_PROFIT, SUMMARY
            
        Returns:
            SQL SELECT section string for stock/asset queries
        """
        if report_type == NET_PROFIT:
            return """
                CAST(0 - COALESCE(SUM(gl.debit - gl.credit), 0) AS INTEGER) AS net_profit
            """
        else:
            return """
                0 AS total_inc,
                CAST(COALESCE(SUM(gl.debit - gl.credit), 0) AS INTEGER) AS total_exp
            """
    
    @staticmethod
    def get_voucher_detail_select(report_type: str) -> str:
        """
        Get SELECT section for detailed voucher-wise reports.
        
        Args:
            report_type: DETAILED_INCOME or DETAILED_EXPENSE
            
        Returns:
            SQL CASE statement for amount calculation
        """
        from hkm.erpnext___custom.report.hkm_eagle_view.utils.constants import (
            DETAILED_INCOME,
            DETAILED_EXPENSE
        )
        
        if report_type == DETAILED_INCOME:
            return f"CASE WHEN tac.root_type = '{INCOME}' THEN gl.credit - gl.debit ELSE 0 END as amount"
        
        elif report_type == DETAILED_EXPENSE:
            return f"CASE WHEN tac.root_type = '{EXPENSE_LIST[0]}' THEN gl.debit - gl.credit ELSE 0 END as amount"
        
        else:
            return f"CASE WHEN tac.root_type = '{INCOME}' THEN gl.credit - gl.debit ELSE gl.debit - gl.credit END as amount"


class SQLConditionBuilder:
    """
    Build common SQL WHERE conditions with proper parameterization.
    """
    
    @staticmethod
    def get_root_type_condition(report_type: str, table_alias: str = "tac") -> str:
        """
        Get root type filter condition.
        
        Args:
            report_type: Report type (ONLY_INCOME, ONLY_EXPENSE, etc.)
            table_alias: Table alias for account table
            
        Returns:
            SQL WHERE condition for root type
        """
        if report_type == ONLY_INCOME:
            return f"AND {table_alias}.root_type = 'Income'"
        elif report_type == ONLY_EXPENSE:
            return f"AND {table_alias}.root_type = 'Expense'"
        else:
            return ""
    
    @staticmethod
    def get_adjustment_root_type_condition(report_type: str) -> str:
        """
        Get adjustment root type condition.
        
        Args:
            report_type: Report type
            
        Returns:
            SQL WHERE condition for adjustment_for field
        """
        if report_type == ONLY_INCOME:
            return "AND ia.adjustment_for = 'Income'"
        elif report_type == ONLY_EXPENSE:
            return "AND ia.adjustment_for = 'Expense'"
        else:
            return ""
    
    @staticmethod
    def get_group_by_clause(include_adjustment: bool, report_type: str) -> str:
        """
        Get appropriate GROUP BY clause.
        
        Args:
            include_adjustment: Whether adjustments are included
            report_type: Report type
            
        Returns:
            SQL GROUP BY clause
        """
        base_group_by = "GROUP BY head, tac.root_type"
        
        if include_adjustment and report_type in [ONLY_EXPENSE, ONLY_INCOME]:
            return base_group_by + ", adjustment_type"
        
        return base_group_by


class CombinedQueryBuilder:
    """
    Build combined queries using UNION ALL for better performance.
    
    Combines GL Entry and Internal Adjustment queries into single execution.
    """
    
    @staticmethod
    def build_combined_gl_adjustment_query(
        dimension: str,
        gl_select: str,
        gl_conditions: str,
        adjustment_select: str,
        adjustment_conditions: str,
        include_adjustment: bool,
        group_by: str
    ) -> str:
        """
        Build combined GL + Adjustment query using UNION ALL.
        
        Args:
            dimension: Dimension field name
            gl_select: SELECT section for GL query
            gl_conditions: WHERE conditions for GL query
            adjustment_select: SELECT section for adjustment query
            adjustment_conditions: WHERE conditions for adjustment query
            include_adjustment: Whether to include adjustment query
            group_by: GROUP BY clause
            
        Returns:
            Combined SQL query string
        """
        gl_query = f"""
        SELECT 
            {gl_select.strip()}
            COALESCE(gl.{dimension}, 'Not Tagged') as head,
            tac.root_type,
            'gl_entry' as adjustment_type
        FROM `tabGL Entry` gl
        JOIN `tabAccount` tac ON tac.name = gl.account
        {gl_conditions}
        {group_by}
        """
        
        if not include_adjustment:
            return gl_query
        
        adjustment_query = f"""
        UNION ALL
        SELECT 
            {adjustment_select},
            COALESCE(iai.{dimension}, 'Not Tagged') as head,
            ia.adjustment_for as root_type,
            ia.type as adjustment_type
        FROM `tabInternal Adjustment` ia
        JOIN `tabInternal Adjustment Detail` iai ON iai.parent = ia.name
        {adjustment_conditions}
        {group_by.replace('tac.root_type', 'ia.adjustment_for')}
        """
        
        return gl_query + adjustment_query
