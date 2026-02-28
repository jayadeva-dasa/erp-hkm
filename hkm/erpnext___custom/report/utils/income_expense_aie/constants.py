# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

# Report Type Constants
SUMMARY = "Both Income and Expenses"
ONLY_INCOME = "Only Incomes"
ONLY_EXPENSE = "Only Expense"
NET_PROFIT = "Net Profit"

# A03 Report Type Constants
A03_SUMMARY = "Summary"
A03_DETAILED_INCOME = "Detailed Income"
A03_DETAILED_EXPENSE = "Detailed Expense"

# Filter Constants
DEP_AND_CONSUMPTION = "exclude_consumption_and_depreciation"
ADJUSTMENT = "include_adjustment"
STOCK_ASSET = "include_stock_asset" 

# Additional Total Constants
Add_Income_Expense_total = "_inc _exp"
Add_Income_total = "_inc"
Add_Expense_total = "_exp"
Add_Net_Profit_total = "_net"

# Root Type Constants
INCOME = "Income"
EXPENSE_LIST = ["Expense", "Asset", "Liability"]

# # =============================================================================
# # SQL CONDITION CONSTANTS
# # =============================================================================

# # Root Type Conditions for SQL Queries
# ROOT_TYPE_CONDITIONS = {
#     SUMMARY: "AND (root_type = 'Income' OR root_type = 'Expense')",
#     ONLY_INCOME: "AND root_type = 'Income'",
#     ONLY_EXPENSE: "AND root_type = 'Expense'"
# }

# # Adjustment Root Type Conditions
# ADJUSTMENT_ROOT_TYPE_CONDITIONS = {
#     SUMMARY: "AND (ia.adjustment_for = 'Income' OR ia.adjustment_for = 'Expense')",
#     ONLY_INCOME: "AND ia.adjustment_for = 'Income'",
#     ONLY_EXPENSE: "AND ia.adjustment_for = 'Expense'"
# }

# # SQL Exclusion Conditions
# EXCLUDE_CONSUMPTION_DEPRECIATION_CONDITION = """
# AND NOT (
#     (tac.root_type = 'Expense' AND gl.against LIKE '%Stock In Hand%')
#     OR
#     (tac.root_type = 'Expense' AND tac.account_type = 'Depreciation' AND tac.name LIKE '%Depreciation%')
# )
# """

# # Stock Asset Conditions
# STOCK_ASSET_CONDITIONS = """
# AND (
#     (tac.root_type = 'Asset' AND gl.against LIKE '%%Asset Received But Not Billed%%')
#     OR
#     (tac.root_type = 'Liability' 
#     AND gl.voucher_type = 'Purchase Invoice' 
#     AND gl.account LIKE '%%Stock Received But Not Billed%%')
# )
# """

# Report Type Mapping Constants
REPORT_TYPES = {
    "SUMMARY": SUMMARY,
    "INCOME": ONLY_INCOME, 
    "EXPENSE": ONLY_EXPENSE,
    "NET_PROFIT": NET_PROFIT
}