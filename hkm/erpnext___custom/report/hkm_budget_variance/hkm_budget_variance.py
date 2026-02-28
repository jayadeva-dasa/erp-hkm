# Copyright (c) 2024, Narahari Dasa and contributors
# For license information, please see license.txt

"""
HKM Budget Variance Report

Shows budget vs utilization analysis using the pre-calculated utilization field.
Much faster than the old approach which recalculated everything.
"""

import frappe
from frappe.utils import flt


def execute(filters=None):
    """
    Generate budget variance report.
    
    NEW APPROACH (Performance Optimized):
    - Uses pre-calculated 'utilization' field from HKM Budget
    - No complex SQL queries needed
    - Much faster execution
    
    Args:
        filters: Report filters (fiscal_year)
    
    Returns:
        columns, data
    """
    data = []
    
    # Get all accounting dimensions from HKM Budget DocType
    budget_meta = frappe.get_meta("HKM Budget")
    
    # Get all dimension fields (cost_center, project, and custom dimensions)
    all_dimensions = ["cost_center", "project"]
    
    # Add custom accounting dimensions
    from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_accounting_dimensions
    try:
        custom_dims = get_accounting_dimensions()
        for dim in custom_dims:
            if budget_meta.has_field(dim):
                all_dimensions.append(dim)
    except Exception:
        pass
    
    # Build fields list dynamically
    fields = ["name", "fiscal_year", "amount", "utilization", "available", 
              "utilization_payment_entries", "utilization_unpaid_invoices",
              "utilization_stock_expenses", "utilization_purchase_orders", 
              "utilization_additional_expenses"]
    
    # Add all dimension fields
    fields.extend(all_dimensions)
    
    # Fetch all budgets for the fiscal year with utilization field and breakdown
    budgets = frappe.get_all(
        "HKM Budget",
        filters={"fiscal_year": filters.get("fiscal_year")},
        fields=fields,
    )
    
    for budget in budgets:
        # Build dimension display with all dimensions used
        dimension_parts = []
        for dim in all_dimensions:
            if budget.get(dim):
                dimension_parts.append(budget.get(dim))
        
        dimension_value = ", ".join(dimension_parts) if dimension_parts else "N/A"
        
        # Calculate variance
        utilization = flt(budget.utilization)
        variance = flt(budget.amount) - utilization
        utilization_percent = (utilization / flt(budget.amount) * 100) if budget.amount else 0
        
        # Build row data
        row = frappe._dict(
            budget=budget.name,
            dimension=dimension_value,
            allowed=budget.amount,
            payment_entries=flt(budget.utilization_payment_entries),
            unpaid_invoices=flt(budget.utilization_unpaid_invoices),
            stock_expenses=flt(budget.utilization_stock_expenses),
            purchase_orders=flt(budget.utilization_purchase_orders),
            additional_expenses=flt(budget.utilization_additional_expenses),
            utilization=utilization,
            available=flt(budget.available),
            variance=variance,
            utilization_percent=utilization_percent,
        )
        
        # Add all accounting dimension values
        for dim in all_dimensions:
            row[dim] = budget.get(dim) or ""
        
        data.append(row)
    
    columns = get_columns(filters, all_dimensions)
    return columns, data


def get_columns(filters, all_dimensions=None):
    """Define report columns with utilization breakdown and accounting dimensions."""
    if all_dimensions is None:
        all_dimensions = []
    
    columns = [
        {
            "label": "Budget",
            "fieldname": "budget",
            "fieldtype": "Link",
            "options": "HKM Budget",
            "width": 200,
        },
        {
            "label": "Dimension",
            "fieldname": "dimension",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": "Allowed",
            "fieldname": "allowed",
            "fieldtype": "Currency",
            "width": 120,
        },
        {
            "label": "Payment Entries",
            "fieldname": "payment_entries",
            "fieldtype": "Currency",
            "width": 120,
        },
        {
            "label": "Unpaid Invoices",
            "fieldname": "unpaid_invoices",
            "fieldtype": "Currency",
            "width": 120,
        },
        {
            "label": "Stock Expenses",
            "fieldname": "stock_expenses",
            "fieldtype": "Currency",
            "width": 120,
        },
        {
            "label": "Purchase Orders",
            "fieldname": "purchase_orders",
            "fieldtype": "Currency",
            "width": 120,
        },
        {
            "label": "Additional GL",
            "fieldname": "additional_expenses",
            "fieldtype": "Currency",
            "width": 120,
        },
        {
            "label": "Utilization",
            "fieldname": "utilization",
            "fieldtype": "Currency",
            "width": 120,
        },
        {
            "label": "Available",
            "fieldname": "available",
            "fieldtype": "Currency",
            "width": 120,
        },
        {
            "label": "Variance",
            "fieldname": "variance",
            "fieldtype": "Currency",
            "width": 120,
        },
        {
            "label": "Utilization %",
            "fieldname": "utilization_percent",
            "fieldtype": "Percent",
            "width": 100,
        },
    ]
    
    # Add all accounting dimension columns at the end
    dimension_map = {
        "cost_center": {"label": "Cost Center", "options": "Cost Center"},
        "project": {"label": "Project", "options": "Project"},
    }
    
    for dim in all_dimensions:
        try:
            # Check if it's a standard dimension
            if dim in dimension_map:
                columns.append({
                    "label": dimension_map[dim]["label"],
                    "fieldname": dim,
                    "fieldtype": "Link",
                    "options": dimension_map[dim]["options"],
                    "width": 150,
                })
            # Check if Accounting Dimension record exists
            elif frappe.db.exists("Accounting Dimension", dim):
                dim_doc = frappe.get_cached_doc("Accounting Dimension", dim)
                columns.append({
                    "label": dim_doc.label or dim.replace("_", " ").title(),
                    "fieldname": dim,
                    "fieldtype": "Link",
                    "options": dim_doc.document_type,
                    "width": 150,
                })
            else:
                # Show as Data field if no Accounting Dimension record
                columns.append({
                    "label": dim.replace("_", " ").title(),
                    "fieldname": dim,
                    "fieldtype": "Data",
                    "width": 150,
                })
        except Exception as e:
            # Show as Data field if any error
            columns.append({
                "label": dim.replace("_", " ").title(),
                "fieldname": dim,
                "fieldtype": "Data",
                "width": 150,
            })
    
    return columns
