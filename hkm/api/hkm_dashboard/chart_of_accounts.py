"""
Chart of Accounts API
Provides endpoints for managing and viewing chart of accounts with drag-and-drop support
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate


@frappe.whitelist()
def get_chart_of_accounts(company, max_depth=None):
    """
    Get chart of accounts for a company
    
    Args:
        company: Company name
        max_depth: Maximum depth to fetch (optional)
    
    Returns:
        List of accounts with hierarchy information
    """
    try:
        filters = {"company": company}
        fields = [
            "name",
            "account_name",
            "account_number",
            "parent_account",
            "is_group",
            "root_type",
            "account_type",
            "company",
            "disabled",
            "report_type",
        ]
        
        # Get all accounts for the company
        accounts = frappe.get_all(
            "Account",
            filters=filters,
            fields=fields,
            order_by="lft"
        )
        
        # Calculate level for each account
        for account in accounts:
            level = 0
            parent = account.get("parent_account")
            while parent:
                level += 1
                parent_doc = frappe.db.get_value(
                    "Account",
                    parent,
                    ["parent_account"],
                    as_dict=True
                )
                parent = parent_doc.get("parent_account") if parent_doc else None
            
            account["level"] = level
        
        return accounts
        
    except Exception as e:
        frappe.log_error(f"Error in get_chart_of_accounts: {str(e)}")
        frappe.throw(_("Failed to fetch chart of accounts: {0}").format(str(e)))


@frappe.whitelist()
def update_account_parent(account_name, new_parent, company):
    """
    Update account parent (for drag and drop)
    
    Args:
        account_name: Account to move
        new_parent: New parent account
        company: Company name
    
    Returns:
        Success message
    """
    try:
        # Get account document
        account = frappe.get_doc("Account", account_name)
        
        # Validate company
        if account.company != company:
            frappe.throw(_("Account does not belong to company {0}").format(company))
        
        # Get new parent document
        new_parent_doc = frappe.get_doc("Account", new_parent)
        
        # Validate new parent is a group account
        if not new_parent_doc.is_group:
            frappe.throw(_("Cannot move account under a ledger account. Parent must be a group account."))
        
        # Validate account types match
        if account.root_type != new_parent_doc.root_type:
            frappe.throw(
                _("Cannot move {0} account under {1} account").format(
                    account.root_type, new_parent_doc.root_type
                )
            )
        
        # Validate not moving to self or descendant
        if account_name == new_parent:
            frappe.throw(_("Cannot move account to itself"))
        
        # Check if new_parent is a descendant of account
        if is_descendant(account_name, new_parent):
            frappe.throw(_("Cannot move account to its own descendant"))
        
        # Update parent
        old_parent = account.parent_account
        account.parent_account = new_parent
        account.save()
        
        return {
            "success": True,
            "message": _("Account {0} moved from {1} to {2}").format(
                account.account_name,
                old_parent or "Root",
                new_parent_doc.account_name
            )
        }
        
    except Exception as e:
        frappe.log_error(f"Error in update_account_parent: {str(e)}")
        frappe.throw(_("Failed to update account parent: {0}").format(str(e)))


@frappe.whitelist()
def validate_account_move(account_name, new_parent):
    """
    Validate if account can be moved to new parent
    
    Args:
        account_name: Account to move
        new_parent: New parent account
    
    Returns:
        Validation result with message
    """
    try:
        # Get account document
        account = frappe.get_doc("Account", account_name)
        
        # Get new parent document
        new_parent_doc = frappe.get_doc("Account", new_parent)
        
        # Validate new parent is a group account
        if not new_parent_doc.is_group:
            return {
                "valid": False,
                "message": _("Cannot move account under a ledger account. Parent must be a group account.")
            }
        
        # Validate account types match
        if account.root_type != new_parent_doc.root_type:
            return {
                "valid": False,
                "message": _("Cannot move {0} account under {1} account").format(
                    account.root_type, new_parent_doc.root_type
                )
            }
        
        # Validate not moving to self
        if account_name == new_parent:
            return {
                "valid": False,
                "message": _("Cannot move account to itself")
            }
        
        # Check if new_parent is a descendant of account
        if is_descendant(account_name, new_parent):
            return {
                "valid": False,
                "message": _("Cannot move account to its own descendant")
            }
        
        return {
            "valid": True,
            "message": _("Move is valid")
        }
        
    except Exception as e:
        frappe.log_error(f"Error in validate_account_move: {str(e)}")
        return {
            "valid": False,
            "message": str(e)
        }


@frappe.whitelist()
def get_account_details(account_name, company, from_date, to_date):
    """
    Get account details including balance
    
    Args:
        account_name: Account name
        company: Company name
        from_date: From date for balance calculation
        to_date: To date for balance calculation
    
    Returns:
        Account details with balance information
    """
    try:
        # Get account document
        account = frappe.get_doc("Account", account_name)
        
        # Get account balance
        from erpnext.accounts.utils import get_balance_on
        
        opening_balance = get_balance_on(
            account_name,
            date=getdate(from_date),
            company=company,
            in_account_currency=False
        )
        
        closing_balance = get_balance_on(
            account_name,
            date=getdate(to_date),
            company=company,
            in_account_currency=False
        )
        
        # Get debit and credit for the period
        gl_entries = frappe.db.sql("""
            SELECT
                SUM(debit) as debit,
                SUM(credit) as credit
            FROM `tabGL Entry`
            WHERE account = %(account)s
                AND company = %(company)s
                AND posting_date BETWEEN %(from_date)s AND %(to_date)s
                AND is_cancelled = 0
        """, {
            "account": account_name,
            "company": company,
            "from_date": from_date,
            "to_date": to_date
        }, as_dict=True)
        
        debit = flt(gl_entries[0].get("debit")) if gl_entries else 0
        credit = flt(gl_entries[0].get("credit")) if gl_entries else 0
        
        # Get currency
        company_doc = frappe.get_doc("Company", company)
        
        return {
            "account_name": account.account_name,
            "account_number": account.account_number,
            "account_type": account.account_type,
            "root_type": account.root_type,
            "is_group": account.is_group,
            "parent_account": account.parent_account,
            "company": account.company,
            "report_type": account.report_type,
            "opening_balance": opening_balance,
            "debit": debit,
            "credit": credit,
            "closing_balance": closing_balance,
            "currency": company_doc.default_currency,
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_account_details: {str(e)}")
        frappe.throw(_("Failed to fetch account details: {0}").format(str(e)))


@frappe.whitelist()
def get_account_balances(account_names, company, from_date, to_date):
    """
    Get account balances for multiple accounts
    
    Args:
        account_names: List of account names (JSON string)
        company: Company name
        from_date: From date
        to_date: To date
    
    Returns:
        Dictionary of account balances
    """
    try:
        import json
        
        # Parse account names if string
        if isinstance(account_names, str):
            account_names = json.loads(account_names)
        
        # Get balances
        from erpnext.accounts.utils import get_balance_on
        
        balances = {}
        for account_name in account_names:
            try:
                balance = get_balance_on(
                    account_name,
                    date=getdate(to_date),
                    company=company,
                    in_account_currency=False
                )
                balances[account_name] = flt(balance)
            except Exception as e:
                frappe.log_error(f"Error getting balance for {account_name}: {str(e)}")
                balances[account_name] = 0
        
        return balances
        
    except Exception as e:
        frappe.log_error(f"Error in get_account_balances: {str(e)}")
        frappe.throw(_("Failed to fetch account balances: {0}").format(str(e)))


def is_descendant(parent_account, child_account):
    """
    Check if child_account is a descendant of parent_account
    
    Args:
        parent_account: Parent account name
        child_account: Child account name
    
    Returns:
        Boolean indicating if child is descendant of parent
    """
    try:
        current = child_account
        while current:
            parent = frappe.db.get_value("Account", current, "parent_account")
            if parent == parent_account:
                return True
            current = parent
        return False
    except Exception:
        return False
