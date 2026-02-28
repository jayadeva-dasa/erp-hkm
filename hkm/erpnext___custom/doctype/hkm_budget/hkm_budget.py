# Copyright (c) 2024, Narahari Dasa and contributors
# For license information, please see license.txt

"""
HKM Budget System - Dimension-based Expense Control

This module provides comprehensive budget validation across multiple accounting dimensions.
It tracks expenses from Purchase Orders (commitment), Purchase Invoices (accrual),
Payment Entries (cash), and other GL entries (adjustments).

Key Features:
- Multi-dimensional budget control (Cost Center, Project, Custom Dimensions)
- Tree hierarchy support (parent budgets apply to child dimensions)
- Real-time validation on GL Entry creation
- Comprehensive expense tracking across procurement lifecycle
"""

from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
    get_accounting_dimensions,
)
import frappe
from frappe.model.document import Document
from frappe.utils import flt, fmt_money, get_link_to_form


class HKMBudget(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        amount: DF.Currency
        cost_center: DF.Link | None
        fiscal_year: DF.Link
        project: DF.Link | None
    # end: auto-generated types

    def validate(self):
        """Validate that at least one dimension is set for the budget."""
        dim_set = 0
        for dim in ["cost_center", "project"] + get_accounting_dimensions():
            if self.get(dim):
                dim_set += 1
        
        # Optional: Enforce exactly one dimension per budget
        # Uncomment below to restrict budgets to single dimension only
        # if dim_set != 1:
        #     frappe.throw("Please select exactly one dimension for the budget.")
        
        if dim_set == 0:
            frappe.throw("Please select at least one dimension (Cost Center, Project, or Accounting Dimension) for the budget.")


def validate_expense_against_budget(args):
    """
    Main entry point for budget validation on GL Entry creation.
    
    Args:
        args: GL Entry data as dict containing account, debit, dimensions, etc.
    
    Returns:
        None - throws exception if budget exceeded
    
    Flow:
        1. Check if any budgets exist in system
        2. Verify fiscal year has budgets configured
        3. Only validate debit entries (expenses) on Expense accounts
        4. Prepare dimension metadata (tree vs flat)
        5. Find applicable budget records matching dimensions
        6. Calculate total usage and validate against budget
    """
    args = frappe._dict(args)
    
    # Early exit: No budgets configured in system
    if not frappe.db.exists("HKM Budget"):
        return
    
    # Early exit: No budgets for this fiscal year
    if not frappe.db.exists("HKM Budget", {"fiscal_year": args.fiscal_year}):
        return
    
    # Early exit: Only validate debit entries (expenses)
    if not args.get("debit") or flt(args.get("debit")) <= 0:
        return
    
    # Early exit: Skip cancelled entries
    if args.get("is_cancelled"):
        return
    
    # Early exit: Only validate Expense accounts
    account_root_type = frappe.get_cached_value("Account", args.get("account"), "root_type")
    if account_root_type != "Expense":
        return
    
    # Prepare dimension metadata (identifies tree vs flat dimensions)
    prepare_dimensions(args)
    
    # Only proceed if GL entry has dimensions set
    if not args.accounting_dimensions:
        return
    
    # Find budget records matching the dimensions
    budget_records = get_applicable_budget_records(args)
    
    # Validate against found budgets
    if budget_records:
        validate_budget_records(args, budget_records)


def get_applicable_budget_records(args):
    """
    Find budget records that apply to the given GL entry dimensions.
    
    For TREE dimensions: Finds parent/ancestor budgets that should apply to child dimensions.
                        Example: If GL entry has Cost Center "Delhi - Main", 
                        it will match budgets for "Delhi - Main" or its parents like "India" or "All Cost Centers"
    
    For FLAT dimensions: Exact match only.
    
    Args:
        args: GL Entry data with accounting_dimensions list
    
    Returns:
        List of budget records (name, amount, utilization, available, fiscal_year)
    """
    conditions = []
    
    for dimension in args.accounting_dimensions:
        fieldname = dimension.fieldname
        dimension_value = args.get(fieldname)
        
        if not dimension_value:
            continue
        
        if dimension.is_tree:
            # For tree dimensions: Find budgets where budget dimension is parent/ancestor of GL entry dimension
            # Logic: Budget's dimension lft <= GL dimension lft AND Budget's dimension rgt >= GL dimension rgt
            # This means budget dimension contains/encompasses the GL entry dimension
            try:
                lft, rgt = frappe.get_cached_value(
                    dimension.document_type, dimension_value, ["lft", "rgt"]
                )
                
                # Find budgets where the budget's dimension is an ancestor (parent/grandparent) of the GL entry's dimension
                conditions.append(f"""
                    EXISTS(
                        SELECT 1 
                        FROM `tab{dimension.document_type}` dim
                        WHERE dim.name = budget.{fieldname}
                        AND dim.lft <= {lft}
                        AND dim.rgt >= {rgt}
                    )
                """)
            except Exception as e:
                frappe.log_error(
                    f"Error getting tree values for {dimension.document_type}: {dimension_value}",
                    "Budget Tree Dimension Error"
                )
                continue
        else:
            # For flat dimensions: Exact match
            conditions.append(f"budget.{fieldname} = {frappe.db.escape(dimension_value)}")
    
    if not conditions:
        return []
    
    # Combine all dimension conditions with AND (budget must match ALL dimensions)
    condition_sql = " AND " + " AND ".join(conditions) if conditions else ""
    
    return frappe.db.sql(
        f"""
        SELECT
            name, amount, IFNULL(utilization, 0) as utilization,   # v16: TODO - Use pypika Field objects for ifnull
            IFNULL(available, amount) as available, fiscal_year  # v16: TODO - Use pypika Field objects for ifnull
        FROM
            `tabHKM Budget` budget
        WHERE
            fiscal_year = {frappe.db.escape(args.fiscal_year)}
            {condition_sql}
    """,
        as_dict=True,
    )


def prepare_dimensions(args):
    """
    Prepare dimension metadata for the GL entry.
    
    Identifies which dimensions are set in the GL entry and determines
    whether each dimension is tree-based (hierarchical) or flat.
    
    Args:
        args: GL Entry data (modified in-place to add accounting_dimensions list)
    
    Sets:
        args.accounting_dimensions: List of dicts with fieldname, document_type, is_tree
    """
    # Default ERPNext dimensions
    default_dimensions = [
        {
            "fieldname": "cost_center",
            "document_type": "Cost Center",
        },
        {
            "fieldname": "project",
            "document_type": "Project",
        },
    ]
    
    # Combine with custom accounting dimensions
    accounting_dimensions = default_dimensions + get_accounting_dimensions(as_list=False)
    
    # Get company abbreviation for default cost center check
    abbr = frappe.get_cached_value("Company", args.company, "abbr") if args.get("company") else None
    
    args.accounting_dimensions = []
    
    for d in accounting_dimensions:
        fieldname = d.get("fieldname")
        dimension_value = args.get(fieldname)
        
        # Skip if dimension not set in GL entry
        if not dimension_value:
            continue
        
        # Skip default/root cost center (usually not budgeted)
        if fieldname == "cost_center" and abbr and dimension_value == f"Main - {abbr}":
            continue
        
        # Check if dimension DocType is tree-based
        is_tree = frappe.get_cached_value(
            "DocType", 
            d.get("document_type"), 
            "is_tree"
        ) or False
        
        dimension = frappe._dict({
            "fieldname": fieldname,
            "document_type": d.get("document_type"),
            "is_tree": bool(is_tree),
        })
        
        args.accounting_dimensions.append(dimension)


def get_dimension_condition(args):
    """
    Build SQL WHERE conditions for filtering transactions by dimensions.
    
    This is used in expense calculation queries (Payment Entry, Purchase Invoice, etc.)
    to filter transactions that match the budget dimensions.
    
    For TREE dimensions: Includes the dimension value AND all its descendants.
                        Example: If budget is for "India", include transactions for
                        "India", "Delhi", "Mumbai", etc. (all children)
    
    For FLAT dimensions: Exact match only.
    
    Args:
        args: GL Entry data with accounting_dimensions list
    
    Returns:
        SQL WHERE condition string (starts with AND)
    
    Note: Uses 'tmi' as table alias (table main item/transaction)
    """
    conditions = []
    
    for dimension in args.accounting_dimensions:
        fieldname = dimension.fieldname
        dimension_value = args.get(fieldname)
        
        if not dimension_value:
            continue
        
        if dimension.is_tree:
            # For tree dimensions: Include the dimension AND all its children
            # Logic: Transaction's dimension lft >= Budget dimension lft AND Transaction's dimension rgt <= Budget dimension rgt
            # This means transaction dimension is contained within the budget dimension
            try:
                lft, rgt = frappe.db.get_value(
                    dimension.document_type, dimension_value, ["lft", "rgt"]
                )
                
                conditions.append(f"""
                    EXISTS(
                        SELECT 1
                        FROM `tab{dimension.document_type}` dim
                        WHERE dim.name = tmi.{fieldname}
                        AND dim.lft >= {lft}
                        AND dim.rgt <= {rgt}
                    )
                """)
            except Exception as e:
                frappe.log_error(
                    f"Error getting tree values for {dimension.document_type}: {dimension_value}",
                    "Budget Dimension Condition Error"
                )
                continue
        else:
            # For flat dimensions: Exact match
            conditions.append(f"tmi.{fieldname} = {frappe.db.escape(dimension_value)}")
    
    # Return combined conditions with AND prefix
    if conditions:
        return " AND " + " AND ".join(conditions)
    return ""


def validate_budget_records(args, budget_records):
    """
    Validate expense against budget limits using pre-calculated utilization.
    
    NEW APPROACH (Performance Optimized):
    - Uses the 'utilization' field which is incrementally updated on each transaction
    - No need to recalculate from Purchase Orders, Invoices, Payments, etc.
    - Much faster and reduces server load
    
    Args:
        args: GL Entry data
        budget_records: List of applicable budget records (with utilization field)
    
    Raises:
        frappe.ValidationError: If budget limit exceeded
    """
    for budget in budget_records:
        # Skip zero-amount budgets
        if not flt(budget.amount):
            continue
        
        # Get current utilization from budget record (pre-calculated)
        current_utilization = flt(budget.utilization)
        
        # Current transaction amount
        requested_value = flt(args.get("debit"))
        
        # Calculate what utilization would be after this transaction
        projected_utilization = current_utilization + requested_value
        
        # Check if budget would be exceeded
        if projected_utilization > budget.amount:
            link = get_link_to_form("HKM Budget", budget.name)
            available = budget.amount - current_utilization
            
            frappe.throw(
                msg=f"""
                    Budget : {link}<br>
                    Allowed : {frappe.bold(fmt_money(budget.amount, currency='₹'))}<br>
                    Current Utilization : {frappe.bold(fmt_money(current_utilization, currency='₹'))}<br>
                    Requested : {frappe.bold(fmt_money(requested_value, currency='₹'))}<br>
                    Available : {frappe.bold(fmt_money(available, currency='₹'))}<br>
                    ------------------------<br>
                    Projected Utilization : {frappe.bold(fmt_money(projected_utilization, currency='₹'))}<br>
                    Excess : {frappe.bold(fmt_money(projected_utilization - budget.amount, currency='₹'))}
                """,
                title="Budget Limit Exceeded",
            )


def get_payment_entries_amount(args):
    """
    Calculate total amount from Payment Entries matching budget dimensions.
    
    Only includes:
    - Submitted payment entries (docstatus = 1)
    - Pay type payments (expenses, not receipts)
    - Payments within fiscal year date range
    - Payments matching dimension conditions
    
    Args:
        args: Contains dimension_condition, yr_start_date, yr_end_date, company
    
    Returns:
        float: Total payment amount
    """
    company_condition = ""
    if args.get("company"):
        company_condition = f"AND tmi.company = {frappe.db.escape(args.company)}"
    
    result = frappe.db.sql(
        f"""
        SELECT IFNULL(SUM(tmi.paid_amount), 0)  # v16: TODO - Use pypika Field objects for ifnull
        FROM `tabPayment Entry` tmi
        WHERE tmi.docstatus = 1
        AND tmi.payment_type = 'Pay'
        AND tmi.posting_date BETWEEN {frappe.db.escape(args.yr_start_date)} AND {frappe.db.escape(args.yr_end_date)}
        {company_condition}
        {args.dimension_condition}
    """
    )
    
    return flt(result[0][0]) if result else 0.0


def get_unpaid_purchase_invoices_amount(args):
    """
    Calculate unpaid amount from Purchase Invoices.
    
    Uses outstanding_amount field which is automatically maintained by ERPNext.
    This is more reliable than calculating from payment allocations.
    
    Only includes:
    - Submitted invoices (docstatus = 1)
    - With outstanding amount > 0 (actually unpaid)
    - Within fiscal year date range
    - Matching dimension conditions
    
    Args:
        args: Contains dimension_condition, yr_start_date, yr_end_date, voucher_no, company
    
    Returns:
        float: Total unpaid invoice amount
    """
    company_condition = ""
    if args.get("company"):
        company_condition = f"AND tmi.company = {frappe.db.escape(args.company)}"
    
    voucher_no = args.get("voucher_no", "")
    
    result = frappe.db.sql(
        f"""
        SELECT IFNULL(SUM(tmi.outstanding_amount), 0)  # v16: TODO - Use pypika Field objects for ifnull
        FROM `tabPurchase Invoice` tmi 
        WHERE tmi.docstatus = 1
            AND tmi.outstanding_amount > 0
            AND tmi.name != {frappe.db.escape(voucher_no)}
            AND tmi.posting_date BETWEEN {frappe.db.escape(args.yr_start_date)} AND {frappe.db.escape(args.yr_end_date)}
            {company_condition}
            {args.dimension_condition}
    """
    )
    
    return flt(result[0][0]) if result else 0.0


def get_unpaid_and_uninvoiced_purchase_orders_amount(args):
    """
    Calculate unpaid and uninvoiced amount from Purchase Orders.
    
    Formula: (PO Item Amount + Taxes) - (Payments + Journal Entries + Invoiced Amount)
    
    Only includes:
    - Submitted POs (docstatus = 1)
    - Only submitted payments, journal entries, and invoices
    - Within fiscal year date range
    - Matching dimension conditions
    
    Args:
        args: Contains dimension_condition, yr_start_date, yr_end_date, company
    
    Returns:
        float: Total unpaid/uninvoiced PO amount
    """
    company_condition = ""
    if args.get("company"):
        company_condition = f"AND tmi.company = {frappe.db.escape(args.company)}"
    
    result = frappe.db.sql(
        f"""
        SELECT IFNULL(SUM(unpaid_amount), 0)  # v16: TODO - Use pypika Field objects for ifnull
        FROM (
            SELECT tmi.name, 
                (   
                    (
                        IFNULL(SUM(tmii.amount), 0)  # v16: TODO - Use pypika Field objects for ifnull
                        + IFNULL(SUM(tmii.igst_amount), 0)  # v16: TODO - Use pypika Field objects for ifnull
                        + IFNULL(SUM(tmii.cgst_amount), 0)  # v16: TODO - Use pypika Field objects for ifnull
                        + IFNULL(SUM(tmii.sgst_amount), 0)      # v16: TODO - Use pypika Field objects for ifnull
                    ) 
                    - (
                        IFNULL(SUM(tper.allocated_amount), 0)  # v16: TODO - Use pypika Field objects for ifnull
                        + IFNULL(SUM(tjea.debit), 0)  # v16: TODO - Use pypika Field objects for ifnull
                    )
                    - (
                        IFNULL(SUM(tpii.amount), 0)  # v16: TODO - Use pypika Field objects for ifnull
                        + IFNULL(SUM(tpii.igst_amount), 0)  # v16: TODO - Use pypika Field objects for ifnull
                        + IFNULL(SUM(tpii.cgst_amount), 0)  # v16: TODO - Use pypika Field objects for ifnull
                        + IFNULL(SUM(tpii.sgst_amount), 0)   # v16: TODO - Use pypika Field objects for ifnull
                    )
                ) as unpaid_amount
            FROM `tabPurchase Order` tmi
            JOIN `tabPurchase Order Item` tmii
                ON tmii.parent = tmi.name
            LEFT JOIN `tabPayment Entry Reference` tper
                ON tper.reference_doctype = 'Purchase Order' 
                AND tper.reference_name = tmi.name
            LEFT JOIN `tabPayment Entry` tpe
                ON tpe.name = tper.parent
                AND tpe.docstatus = 1
            LEFT JOIN `tabJournal Entry Account` tjea
                ON tjea.reference_type = 'Purchase Order' 
                AND tjea.reference_name = tmi.name
            LEFT JOIN `tabJournal Entry` tje
                ON tje.name = tjea.parent
                AND tje.docstatus = 1
            LEFT JOIN `tabPurchase Invoice Item` tpii 
                ON tpii.purchase_order = tmi.name
            LEFT JOIN `tabPurchase Invoice` tpi 
                ON tpi.name = tpii.parent 
                AND tpi.docstatus = 1
            WHERE tmi.docstatus = 1
                AND tmi.transaction_date BETWEEN {frappe.db.escape(args.yr_start_date)} AND {frappe.db.escape(args.yr_end_date)}
                {company_condition}
                {args.dimension_condition}
            GROUP BY tmi.name
        ) up
    """
    )
    
    return flt(result[0][0]) if result else 0.0


def get_additional_expenses_amount(args):
    """
    Calculate additional expenses from GL Entries.
    
    Includes:
    - Stock Entry expenses
    - Journal Entry expenses
    - Other expense GL entries
    
    Excludes:
    - Purchase Invoices (already counted in unpaid invoices)
    - Period Closing Vouchers (year-end accounting adjustments, not actual expenses)
    - Cancelled entries
    
    Args:
        args: Contains dimension_condition, fiscal_year, company
    
    Returns:
        float: Total additional expenses (debit - credit)
    """
    company_condition = ""
    if args.get("company"):
        company_condition = f"AND tmi.company = {frappe.db.escape(args.company)}"
    
    exclude_voucher_types = ["Purchase Invoice", "Period Closing Voucher", "Stock Entry"]
    exclude_voucher_types_str = ", ".join([f"'{vt}'" for vt in exclude_voucher_types])
    
    result = frappe.db.sql(
        f"""
        SELECT IFNULL(SUM(tmi.debit) - SUM(tmi.credit), 0)  # v16: TODO - Use pypika Field objects for ifnull
        FROM `tabGL Entry` tmi
        JOIN `tabAccount` ta
            ON tmi.account = ta.name
        WHERE tmi.is_cancelled = 0
        AND ta.root_type = 'Expense'
        AND tmi.voucher_type NOT IN ({exclude_voucher_types_str})
        AND tmi.fiscal_year = {frappe.db.escape(args.fiscal_year)}
        {company_condition}
        {args.dimension_condition}
    """
    )
    
    return flt(result[0][0]) if result else 0.0


def get_stock_expenses_amount(args):
    """
    Calculate stock-related expenses from Stock Entry.
    
    Includes:
    - Stock Entry expenses (Material Issue, Material Consumption, etc.)
    - Only expense accounts (root_type = 'Expense')
    
    Excludes:
    - Cancelled entries
    - Asset accounts (Stock In Hand, Stock Received But Not Billed, etc.)
    
    Args:
        args: Contains dimension_condition, fiscal_year, company
    
    Returns:
        float: Total stock expenses (debit - credit)
    """
    company_condition = ""
    if args.get("company"):
        company_condition = f"AND tmi.company = {frappe.db.escape(args.company)}"
    
    result = frappe.db.sql(
        f"""
        SELECT IFNULL(SUM(tmi.debit) - SUM(tmi.credit), 0)  # v16: TODO - Use pypika Field objects for ifnull
        FROM `tabGL Entry` tmi
        JOIN `tabAccount` ta
            ON tmi.account = ta.name
        WHERE tmi.is_cancelled = 0
        AND ta.root_type = 'Expense'
        AND tmi.voucher_type = 'Stock Entry'
        AND tmi.fiscal_year = {frappe.db.escape(args.fiscal_year)}
        {company_condition}
        {args.dimension_condition}
    """
    )
    
    return flt(result[0][0]) if result else 0.0
