# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

"""
HKM Budget Utilization Tracker

This module handles incremental budget utilization updates.
Instead of recalculating the entire budget on each transaction,
it updates the utilization field incrementally on submit/cancel.

Key Features:
- Incremental updates on document submit/cancel
- Supports Purchase Orders, Purchase Invoices, Payment Entries, GL Entries
- Handles tree and flat dimensions
- Multi-budget support (one transaction can affect multiple budgets)
"""

import frappe
from frappe.utils import flt
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
    get_accounting_dimensions,
)


def update_budget_utilization_on_submit(doc, method=None):
    """
    Update budget utilization when a document is submitted.
    
    Called from hooks on submit of:
    - Purchase Order
    - Purchase Invoice
    - Payment Entry
    - GL Entry (for Stock Entry, Journal Entry, etc.)
    
    Args:
        doc: The document being submitted
        method: Hook method (not used)
    """
    try:
        # Get expense amount from document
        expense_amount = get_expense_amount_from_doc(doc)
        
        if not expense_amount or expense_amount <= 0:
            return
        
        # Find applicable budgets
        applicable_budgets = find_applicable_budgets_for_doc(doc)
        
        if not applicable_budgets:
            return
        
        # Update each budget's utilization
        for budget_name in applicable_budgets:
            update_budget_utilization(budget_name, expense_amount, operation="add")
            
    except Exception as e:
        frappe.log_error(
            f"Error updating budget utilization on submit for {doc.doctype} {doc.name}: {str(e)}",
            "Budget Utilization Update Error"
        )


def update_budget_utilization_on_cancel(doc, method=None):
    """
    Update budget utilization when a document is cancelled.
    
    Reverses the utilization added during submit.
    
    Args:
        doc: The document being cancelled
        method: Hook method (not used)
    """
    try:
        # Get expense amount from document
        expense_amount = get_expense_amount_from_doc(doc)
        
        if not expense_amount or expense_amount <= 0:
            return
        
        # Find applicable budgets
        applicable_budgets = find_applicable_budgets_for_doc(doc)
        
        if not applicable_budgets:
            return
        
        # Update each budget's utilization (subtract)
        for budget_name in applicable_budgets:
            update_budget_utilization(budget_name, expense_amount, operation="subtract")
            
    except Exception as e:
        frappe.log_error(
            f"Error updating budget utilization on cancel for {doc.doctype} {doc.name}: {str(e)}",
            "Budget Utilization Update Error"
        )


def get_expense_amount_from_doc(doc):
    """
    Extract expense amount from different document types.
    
    Args:
        doc: Document (Purchase Order, Purchase Invoice, Payment Entry, GL Entry)
    
    Returns:
        float: Expense amount
    """
    doctype = doc.doctype
    
    if doctype == "Purchase Order":
        # For PO: Sum of item amounts + taxes
        total = flt(doc.total) + flt(doc.total_taxes_and_charges)
        return total
    
    elif doctype == "Purchase Invoice":
        # For PI: Grand total
        return flt(doc.grand_total)
    
    elif doctype == "Payment Entry":
        # For PE: Only "Pay" type (expenses)
        if doc.payment_type == "Pay":
            return flt(doc.paid_amount)
        return 0
    
    elif doctype == "GL Entry":
        # For GL Entry: Only debit on Expense accounts
        account_root_type = frappe.get_cached_value("Account", doc.account, "root_type")
        if account_root_type == "Expense":
            return flt(doc.debit)
        return 0
    
    return 0


def find_applicable_budgets_for_doc(doc):
    """
    Find all budgets that apply to this document based on dimensions.
    
    For tree dimensions: Finds parent budgets that should apply.
    For flat dimensions: Finds exact match budgets.
    
    Args:
        doc: Document with dimension fields
    
    Returns:
        list: List of budget names
    """
    # Get fiscal year from document
    fiscal_year = get_fiscal_year_from_doc(doc)
    
    if not fiscal_year:
        return []
    
    # Check if any budgets exist for this fiscal year
    if not frappe.db.exists("HKM Budget", {"fiscal_year": fiscal_year}):
        return []
    
    # Prepare dimensions from document
    doc_dimensions = prepare_doc_dimensions(doc)
    
    if not doc_dimensions:
        return []
    
    # Build SQL conditions to find matching budgets
    conditions = []
    
    for dimension in doc_dimensions:
        fieldname = dimension["fieldname"]
        dimension_value = dimension["value"]
        
        if not dimension_value:
            continue
        
        if dimension["is_tree"]:
            # For tree dimensions: Find budgets where budget dimension is parent/ancestor
            try:
                lft, rgt = frappe.get_cached_value(
                    dimension["document_type"], dimension_value, ["lft", "rgt"]
                )
                
                conditions.append(f"""
                    EXISTS(
                        SELECT 1 
                        FROM `tab{dimension["document_type"]}` dim
                        WHERE dim.name = budget.{fieldname}
                        AND dim.lft <= {lft}
                        AND dim.rgt >= {rgt}
                    )
                """)
            except:
                continue
        else:
            # For flat dimensions: Exact match
            conditions.append(f"budget.{fieldname} = {frappe.db.escape(dimension_value)}")
    
    if not conditions:
        return []
    
    # Combine conditions
    condition_sql = " AND " + " AND ".join(conditions) if conditions else ""
    
    # Query budgets
    budgets = frappe.db.sql(
        f"""
        SELECT name
        FROM `tabHKM Budget` budget
        WHERE fiscal_year = {frappe.db.escape(fiscal_year)}
        {condition_sql}
        """,
        as_dict=True
    )
    
    return [b.name for b in budgets]


def prepare_doc_dimensions(doc):
    """
    Extract dimension values from document.
    
    Args:
        doc: Document with dimension fields
    
    Returns:
        list: List of dimension dicts with fieldname, document_type, value, is_tree
    """
    # Default dimensions
    default_dimensions = [
        {"fieldname": "cost_center", "document_type": "Cost Center"},
        {"fieldname": "project", "document_type": "Project"},
    ]
    
    # Combine with custom accounting dimensions
    all_dimensions = default_dimensions + get_accounting_dimensions(as_list=False)
    
    # Get company abbreviation for default cost center check
    company = doc.get("company")
    abbr = frappe.get_cached_value("Company", company, "abbr") if company else None
    
    doc_dimensions = []
    
    for d in all_dimensions:
        fieldname = d.get("fieldname")
        dimension_value = doc.get(fieldname)
        
        # Skip if dimension not set
        if not dimension_value:
            continue
        
        # Skip default/root cost center
        if fieldname == "cost_center" and abbr and dimension_value == f"Main - {abbr}":
            continue
        
        # Check if tree-based
        is_tree = frappe.get_cached_value(
            "DocType", d.get("document_type"), "is_tree"
        ) or False
        
        doc_dimensions.append({
            "fieldname": fieldname,
            "document_type": d.get("document_type"),
            "value": dimension_value,
            "is_tree": bool(is_tree),
        })
    
    return doc_dimensions


def get_fiscal_year_from_doc(doc):
    """
    Get fiscal year from document.
    
    Args:
        doc: Document
    
    Returns:
        str: Fiscal year name or None
    """
    # Direct fiscal_year field
    if hasattr(doc, "fiscal_year") and doc.fiscal_year:
        return doc.fiscal_year
    
    # Get from posting_date or transaction_date
    date_field = None
    if hasattr(doc, "posting_date") and doc.posting_date:
        date_field = doc.posting_date
    elif hasattr(doc, "transaction_date") and doc.transaction_date:
        date_field = doc.transaction_date
    
    if date_field:
        try:
            from erpnext.accounts.utils import get_fiscal_year
            fiscal_year = get_fiscal_year(date_field, company=doc.get("company"))[0]
            return fiscal_year
        except:
            pass
    
    return None


def update_budget_utilization(budget_name, amount, operation="add"):
    """
    Update the utilization field of a budget.
    
    Args:
        budget_name: Name of the budget document
        amount: Amount to add or subtract
        operation: "add" or "subtract"
    """
    try:
        # Use SQL UPDATE for performance (avoid loading full document)
        if operation == "add":
            frappe.db.sql("""
                UPDATE `tabHKM Budget`
                SET utilization = IFNULL(utilization, 0) + %s,
                    available = amount - (IFNULL(utilization, 0) + %s)
                WHERE name = %s
            """, (amount, amount, budget_name))
        else:  # subtract
            frappe.db.sql("""
                UPDATE `tabHKM Budget`
                SET utilization = IFNULL(utilization, 0) - %s,
                    available = amount - (IFNULL(utilization, 0) - %s)
                WHERE name = %s
            """, (amount, amount, budget_name))
        
        frappe.db.commit()  # v16: REVIEW - check if needed
        
    except Exception as e:
        frappe.log_error(
            f"Error updating budget {budget_name}: {str(e)}",
            "Budget Utilization Update Error"
        )
        raise


def recalculate_budget_utilization(budget_name):
    """
    Recalculate budget utilization from scratch.
    
    Used for:
    - Initial setup (patch)
    - Manual recalculation if data gets out of sync
    
    Args:
        budget_name: Name of the budget document
    """
    budget = frappe.get_doc("HKM Budget", budget_name)
    
    # Prepare args similar to old system
    args = frappe._dict({
        "fiscal_year": budget.fiscal_year,
        "company": None,  # Will be determined from transactions
    })
    
    # Get fiscal year dates
    args.yr_start_date, args.yr_end_date = frappe.get_cached_value(
        "Fiscal Year", budget.fiscal_year, ["year_start_date", "year_end_date"]
    )
    
    # Prepare dimensions
    from hkm.erpnext___custom.doctype.hkm_budget.hkm_budget import prepare_dimensions, get_dimension_condition
    
    # Set dimensions from budget
    for dim in ["cost_center", "project"] + get_accounting_dimensions():
        if budget.get(dim):
            args[dim] = budget.get(dim)
    
    prepare_dimensions(args)
    
    if not args.accounting_dimensions:
        return 0
    
    args.dimension_condition = get_dimension_condition(args)
    
    # Calculate from all 5 sources
    from hkm.erpnext___custom.doctype.hkm_budget.hkm_budget import (
        get_payment_entries_amount,
        get_unpaid_purchase_invoices_amount,
        get_unpaid_and_uninvoiced_purchase_orders_amount,
        get_stock_expenses_amount,
        get_additional_expenses_amount
    )
    
    payment_entries_amount = get_payment_entries_amount(args)
    unpaid_invoices_amount = get_unpaid_purchase_invoices_amount(args)
    unpaid_and_uninvoiced_po_amt = get_unpaid_and_uninvoiced_purchase_orders_amount(args)
    stock_expenses_amount = get_stock_expenses_amount(args)
    additional_expenses = get_additional_expenses_amount(args)
    
    total_utilization = (
        payment_entries_amount
        + unpaid_invoices_amount
        + unpaid_and_uninvoiced_po_amt
        + stock_expenses_amount
        + additional_expenses
    )
    
    # Update budget with total and breakdown
    frappe.db.set_value("HKM Budget", budget_name, {
        "utilization": total_utilization,
        "available": budget.amount - total_utilization,
        "utilization_payment_entries": payment_entries_amount,
        "utilization_unpaid_invoices": unpaid_invoices_amount,
        "utilization_purchase_orders": unpaid_and_uninvoiced_po_amt,
        "utilization_stock_expenses": stock_expenses_amount,
        "utilization_additional_expenses": additional_expenses
    })
    
    frappe.db.commit()  # v16: REVIEW - check if needed
    
    return total_utilization
