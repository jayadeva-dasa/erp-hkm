# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

"""
HKM Reports Utilities - Main Module
This module provides a unified interface to all utility functions and classes
organized into separate focused modules.
"""

# Import constants
from hkm.erpnext___custom.report.utils.income_expense_aie.constants import (
    SUMMARY,
    ONLY_INCOME,
    ONLY_EXPENSE,
    NET_PROFIT,
    A03_SUMMARY,
    A03_DETAILED_INCOME,
    A03_DETAILED_EXPENSE,
    DEP_AND_CONSUMPTION,
    ADJUSTMENT,
    STOCK_ASSET,
    Add_Income_Expense_total,
    Add_Income_total,
    Add_Expense_total,
    Add_Net_Profit_total,
    INCOME,
    EXPENSE_LIST,
    REPORT_TYPES,
)

# Import SQL conditions
from hkm.erpnext___custom.report.utils.income_expense_aie.sql_conditions import (
    get_common_condition,
    get_ie_gl_sql_conditions,
    get_al_gl_sql_conditions,
    get_ie_adjustment_sql_conditions,
    get_cost_head_condition,
    get_root_type_condition,
)

from hkm.erpnext___custom.report.utils.income_expense_aie.dimension_utils import (
    get_heads,get_child_nodes ,get_proper_heads
)

# Import data processors
from hkm.erpnext___custom.report.utils.income_expense_aie.data_processors import ReportDataProcessor

# Import column builders
from hkm.erpnext___custom.report.utils.income_expense_aie.column_builders import ColumnBuilder

# Import file processors
from hkm.erpnext___custom.report.utils.income_expense_aie.file_processors import FileProcessor

# Import date utilities
from hkm.erpnext___custom.report.utils.income_expense_aie.date_utils import (
    validate_filters,
    get_dates_range,
)

# Import data utilities
from hkm.erpnext___custom.report.utils.income_expense_aie.data_utils import (
    add_empty_rows,
)

# # Re-export all for backward compatibility
# __all__ = [
#     # Constants
#     'SUMMARY',
#     'INCOME', 
#     'EXPENSE',
#     'NET_PROFIT',
#     'A03_SUMMARY',
#     'A03_DETAILED_INCOME',
#     'A03_DETAILED_EXPENSE',
#     'DEP_AND_CONSUMPTION',
#     'ADJUSTMENT',
#     'STOCK_ASSET',
    
#     # SQL Conditions
#     'get_common_condition',
#     'get_ie_gl_sql_conditions',
#     'get_al_gl_sql_conditions', 
#     'get_ie_adjustment_sql_conditions',
#     'get_cost_head_condition',
#     'get_root_type_condition',
    
#     # Query Builders
#     'build_base_gl_query',
#     'build_stock_asset_query',
#     'build_adjustment_query',
    
#     # Data Processors
#     'ReportDataProcessor',
    
#     # Column Builders
#     'ColumnBuilder',
    
#     # File Processors
#     'FileProcessor',
    
#     # Date Utilities
#     'validate_filters',
#     'get_dates_range',
    
#     # Data Utilities
#     'add_empty_rows',
# ]
