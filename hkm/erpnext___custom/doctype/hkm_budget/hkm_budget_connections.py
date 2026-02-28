"""
HKM Budget Connections
Shows all related transactions for a budget based on matching dimensions
"""

import frappe
from frappe import _



def test_query():
    get_budget_connections("Voluteer Medical Expense")


@frappe.whitelist()
def get_budget_connections(budget_name):
    """
    Get all transactions connected to this budget based on matching dimensions.
    
    Returns:
        dict: Grouped connections by document type with counts and links
    """
    budget = frappe.get_doc("HKM Budget", budget_name)
    print(budget.name)
    # Get fiscal year dates
    yr_start, yr_end = frappe.get_cached_value(
        "Fiscal Year", 
        budget.fiscal_year, 
        ["year_start_date", "year_end_date"]
    )
    
    # Build dimension conditions
    dimension_conditions = []
    dimensions_used = []
    
    # Check cost_center
    if budget.cost_center:
        dimension_conditions.append(f"cost_center = {frappe.db.escape(budget.cost_center)}")
        dimensions_used.append(("Cost Center", budget.cost_center))
    
    # Check project
    if budget.project:
        print(f"Project: {budget.project}")
        dimension_conditions.append(f"project = {frappe.db.escape(budget.project)}")
        dimensions_used.append(("Project", budget.project))
    
    # Check custom accounting dimensions
    from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_accounting_dimensions
    custom_dims = get_accounting_dimensions()
    
    for dim in custom_dims:
        if budget.get(dim):
            dimension_conditions.append(f"{dim} = {frappe.db.escape(budget.get(dim))}")
            dimensions_used.append((dim.replace("_", " ").title(), budget.get(dim)))
    
    if not dimension_conditions:
        print("No dimensions set for this budget")
        return {
            "dimensions": [],
            "connections": {},
            "message": "No dimensions set for this budget"
        }
    
    dimension_where = " AND ".join(dimension_conditions)
    
    # Get connections for each document type
    connections = {}
    
    # 1. Payment Entries
    print(f"Payment Entries: {dimension_where}")
    connections["Payment Entry"] = get_payment_entries(dimension_where, yr_start, yr_end)
    
    # 2. Purchase Invoices
    connections["Purchase Invoice"] = get_purchase_invoices(dimension_where, yr_start, yr_end)
    
    # 3. Purchase Orders
    connections["Purchase Order"] = get_purchase_orders(dimension_where, yr_start, yr_end)
    
    # 4. Journal Entries
    connections["Journal Entry"] = get_journal_entries(dimension_where, yr_start, yr_end)
    
    # 5. Stock Entries
    connections["Stock Entry"] = get_stock_entries(dimension_where, yr_start, yr_end)
    
    return {
        "dimensions": dimensions_used,
        "connections": connections,
        "fiscal_year": budget.fiscal_year,
        "date_range": f"{yr_start} to {yr_end}"
    }


def get_payment_entries(dimension_where, yr_start, yr_end):
    """Get Payment Entries matching dimensions"""
    try:
        entries = frappe.db.sql(f"""
            SELECT 
                name,
                posting_date,
                paid_amount,
                party,
                payment_type
            FROM `tabPayment Entry`
            WHERE docstatus = 1
            AND payment_type = 'Pay'
            AND posting_date BETWEEN {frappe.db.escape(yr_start)} AND {frappe.db.escape(yr_end)}
            AND ({dimension_where})
            ORDER BY posting_date DESC
            LIMIT 100
        """, as_dict=True)
        
        return {
            "count": len(entries),
            "items": entries[:10],  # Show only first 10
            "total_count": len(entries)
        }
    except Exception as e:
        frappe.log_error(f"Error fetching Payment Entries: {str(e)}")
        return {"count": 0, "items": [], "total_count": 0}


def get_purchase_invoices(dimension_where, yr_start, yr_end):
    """Get Purchase Invoices matching dimensions"""
    try:
        query = f"""
            SELECT 
                name,
                posting_date,
                grand_total,
                supplier,
                outstanding_amount
            FROM `tabPurchase Invoice`
            WHERE docstatus = 1
            AND posting_date BETWEEN {frappe.db.escape(yr_start)} AND {frappe.db.escape(yr_end)}
            AND ({dimension_where})
            ORDER BY posting_date DESC
            LIMIT 100
        """
        print(f"Purchase Invoices: {query}")
        entries = frappe.db.sql(query, as_dict=True)
        
        return {
            "count": len(entries),
            "items": entries[:10],
            "total_count": len(entries)
        }
    except Exception as e:
        frappe.log_error(f"Error fetching Purchase Invoices: {str(e)}")
        return {"count": 0, "items": [], "total_count": 0}


def get_purchase_orders(dimension_where, yr_start, yr_end):
    """Get Purchase Orders matching dimensions"""
    try:
        entries = frappe.db.sql(f"""
            SELECT 
                name,
                transaction_date,
                grand_total,
                supplier,
                status
            FROM `tabPurchase Order`
            WHERE docstatus = 1
            AND transaction_date BETWEEN {frappe.db.escape(yr_start)} AND {frappe.db.escape(yr_end)}
            AND ({dimension_where})
            ORDER BY transaction_date DESC
            LIMIT 100
        """, as_dict=True)
        
        return {
            "count": len(entries),
            "items": entries[:10],
            "total_count": len(entries)
        }
    except Exception as e:
        frappe.log_error(f"Error fetching Purchase Orders: {str(e)}")
        return {"count": 0, "items": [], "total_count": 0}


def get_journal_entries(dimension_where, yr_start, yr_end):
    """Get Journal Entries matching dimensions"""
    try:
        entries = frappe.db.sql(f"""
            SELECT DISTINCT
                je.name,
                je.posting_date,
                je.total_debit,
                je.voucher_type
            FROM `tabJournal Entry` je
            JOIN `tabJournal Entry Account` jea ON jea.parent = je.name
            WHERE je.docstatus = 1
            AND je.posting_date BETWEEN {frappe.db.escape(yr_start)} AND {frappe.db.escape(yr_end)}
            AND ({dimension_where.replace('cost_center', 'jea.cost_center').replace('project', 'jea.project')})
            ORDER BY je.posting_date DESC
            LIMIT 100
        """, as_dict=True)
        
        return {
            "count": len(entries),
            "items": entries[:10],
            "total_count": len(entries)
        }
    except Exception as e:
        frappe.log_error(f"Error fetching Journal Entries: {str(e)}")
        return {"count": 0, "items": [], "total_count": 0}


def get_stock_entries(dimension_where, yr_start, yr_end):
    """Get Stock Entries matching dimensions"""
    try:
        entries = frappe.db.sql(f"""
            SELECT 
                name,
                posting_date,
                total_outgoing_value,
                stock_entry_type,
                purpose
            FROM `tabStock Entry`
            WHERE docstatus = 1
            AND posting_date BETWEEN {frappe.db.escape(yr_start)} AND {frappe.db.escape(yr_end)}
            AND ({dimension_where})
            ORDER BY posting_date DESC
            LIMIT 100
        """, as_dict=True)
        
        return {
            "count": len(entries),
            "items": entries[:10],
            "total_count": len(entries)
        }
    except Exception as e:
        frappe.log_error(f"Error fetching Stock Entries: {str(e)}")
        return {"count": 0, "items": [], "total_count": 0}
