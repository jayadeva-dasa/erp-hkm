# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

"""
Patch: Calculate Initial Budget Utilization

This patch calculates and populates the 'utilization' and 'available' fields
for all existing HKM Budget records.

Run this patch after adding the new fields to migrate from the old system
(which recalculated on every transaction) to the new system (which maintains
incremental utilization).
"""

import frappe
from frappe.utils import flt


def execute():
    """
    Calculate initial utilization for all existing budgets.
    """
    frappe.log("Starting budget utilization calculation patch...")
    
    # Get all budgets
    budgets = frappe.get_all("HKM Budget", fields=["name"])
    
    total = len(budgets)
    frappe.log(f"Found {total} budgets to process")
    
    success_count = 0
    error_count = 0
    
    for idx, budget_dict in enumerate(budgets, 1):
        try:
            budget_name = budget_dict.name
            
            # Calculate utilization using the recalculation function
            from hkm.erpnext___custom.doctype.hkm_budget.budget_utilization import recalculate_budget_utilization
            
            utilization = recalculate_budget_utilization(budget_name)
            
            success_count += 1
            
            if idx % 10 == 0:
                frappe.log(f"Processed {idx}/{total} budgets...")
                frappe.db.commit()  # v16: OK - patch script
            
        except Exception as e:
            error_count += 1
            frappe.log_error(
                f"Error calculating utilization for budget {budget_name}: {str(e)}",
                "Budget Utilization Patch Error"
            )
            continue
    
    # Final commit
    frappe.db.commit()  # v16: OK - patch script
    
    frappe.log(f"""
    Budget Utilization Calculation Patch Completed
    ================================================
    Total Budgets: {total}
    Successfully Processed: {success_count}
    Errors: {error_count}
    """)
    
    if error_count > 0:
        frappe.log(f"WARNING: {error_count} budgets had errors. Check Error Log for details.")
