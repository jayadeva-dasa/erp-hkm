"""
Intelligent COA Reorganization
==============================

This script analyzes the Kota COA structure and intelligently moves ALL accounts
under the numbered parent structure, ensuring only numbered accounts are parents.

Based on Jaipur COA structure analysis.

Usage:
    bench --site erp.hkmkota.org console
    >>> from hkm.cursor.intelligent_coa_reorganization import reorganize_all_kota_accounts
    >>> reorganize_all_kota_accounts()

Author: Cursor AI Assistant
Date: 2026-02-07
"""

import frappe
from typing import Dict, List, Tuple


def get_intelligent_account_mapping():
    """
    Build intelligent mapping based on account names and types
    Maps account patterns to their correct numbered parents
    """
    
    # Based on Jaipur structure analysis
    mapping = {
        # ASSETS (2.x)
        # Current Assets (2.2.x)
        "Loans and Advances (Assets)": "2.2.5 - Short Term Loans and Advances",
        "Employee Advances": "2.2.5 - Short Term Loans and Advances",
        "Imprest": "2.2.5 - Short Term Loans and Advances",  # All imprest accounts
        "Securities and Deposits": "2.2.5 - Short Term Loans and Advances",
        "Earnest Money": "2.2.5 - Short Term Loans and Advances",
        "Security Deposit": "2.2.5 - Short Term Loans and Advances",
        
        "Stock Assets": "2.2.2 - Inventories",
        "Book Counter Stock": "2.2.2 - Inventories",
        "Book Main Location": "2.2.2 - Inventories",
        "Temple Counter Main": "2.2.2 - Inventories",
        
        "Tax Assets": "2.2.6 - Other Current Assets",
        "Accrued Interest": "2.2.6 - Other Current Assets",
        "Paytm Machine Security": "2.2.5 - Short Term Loans and Advances",
        "Sundry debtors": "2.2.3 - Accounts Receivable",
        "Books Marathon": "2.2.3 - Accounts Receivable",
        
        "POS Sales Fund": "2.2.4 - Cash and bank balances",
        "Sales Temporary Cash": "2.2.4 - Cash and bank balances",
        
        "Advance Tax": "2.2.6 - Other Current Assets",
        "TDS Refundable": "2.2.6 - Other Current Assets",
        
        # Fixed Assets (2.1.1.1)
        "Fixed Assets": "2.1.1 - Property, Plant and Equipment",
        "FA - Buildings": "2.1.1.1 - Property Plant and Equipment",
        "Capital Equipments": "2.1.1.1 - Property Plant and Equipment",
        "FA - Electrical": "2.1.1.1 - Property Plant and Equipment",
        "FA - Office Equipments": "2.1.1.1 - Property Plant and Equipment",
        "FA - Plants and Machineries": "2.1.1.1 - Property Plant and Equipment",
        "FA - Softwares": "2.1.1.1 - Property Plant and Equipment",
        "FA - Deity Poshak": "2.1.1.1 - Property Plant and Equipment",
        "FA - Kirtan Equipments": "2.1.1.1 - Property Plant and Equipment",
        "FA - Vehicles": "2.1.1.1 - Property Plant and Equipment",
        "FA - Furnitures": "2.1.1.1 - Property Plant and Equipment",
        "Buildings": "2.1.1.1 - Property Plant and Equipment",
        "Deity Poshak": "2.1.1.1 - Property Plant and Equipment",
        "Camera & Accessories": "2.1.1.1 - Property Plant and Equipment",
        "Computer & Softwares": "2.1.1.1 - Property Plant and Equipment",
        "Electric Equipment": "2.1.1.1 - Property Plant and Equipment",
        "Deities": "2.1.1.1 - Property Plant and Equipment",
        "Kitchen Equipment": "2.1.1.1 - Property Plant and Equipment",
        "Musical Instruments": "2.1.1.1 - Property Plant and Equipment",
        "Deity Related": "2.1.1.1 - Property Plant and Equipment",
        
        # Investments
        "Investments": "2.1.2 - Non-current investment",
        "Fixed Deposits": "2.1.2 - Non-current investment",
        "Specific FD": "2.1.2 - Non-current investment",
        "General FD": "2.1.2 - Non-current investment",
        "FD with": "2.1.2 - Non-current investment",
        
        # LIABILITIES (1.x)
        # Current Liabilities (1.3.x)
        "Loans (Liabilities)": "1.3.1 - Short-term borrowings",
        "Bank Overdraft": "1.3.1 - Short-term borrowings",
        "Secured Loans": "1.3.1 - Short-term borrowings",
        "Unsecured Loans": "1.3.1 - Short-term borrowings",
        
        "Stock Liabilities": "1.3.2 - Accounts Payable",
        "Payables": "1.3.2 - Accounts Payable",
        "Expenses Payable": "1.3.3 - Other Current Liabilities",
        "Payroll Payable": "1.3.3 - Other Current Liabilities",
        "Expense Payable": "1.3.3 - Other Current Liabilities",
        "Honorarium Payable": "1.3.3 - Other Current Liabilities",
        "Salary Payable": "1.3.3 - Other Current Liabilities",
        "Incentive payable": "1.3.3 - Other Current Liabilities",
        "Traveling & Conveyance Payable": "1.3.3 - Other Current Liabilities",
        
        "Provisions": "1.3.4 - Short-term provisions",
        "Provision for": "1.3.4 - Short-term provisions",
        "Provision": "1.3.4 - Short-term provisions",
        
        "Post Dated Cheques": "1.3.3 - Other Current Liabilities",
        "Staff Welfare Fund": "1.3.3 - Other Current Liabilities",
        "Payable": "1.3.3 - Other Current Liabilities",
        
        "Duties and Taxe": "1.3.3 - Other Current Liabilities",
        "Duties and Taxes": "1.3.3 - Other Current Liabilities",
        "PF and ESI Payable": "1.3.3 - Other Current Liabilities",
        "Statutory Liabilities": "1.3.3 - Other Current Liabilities",
        "Output Tax": "1.3.3 - Other Current Liabilities",
        "CGST": "1.3.3 - Other Current Liabilities",
        "SGST": "1.3.3 - Other Current Liabilities",
        "Income Tax Payable": "1.3.3 - Other Current Liabilities",
        "Statutory Liability": "1.3.3 - Other Current Liabilities",
        "Customs Duty Payable": "1.3.3 - Other Current Liabilities",
        "TDS on": "1.3.3 - Other Current Liabilities",
        
        # Trust Funds (1.1.x)
        "Capital Account": "1.1.1 - Unrestricted Funds",
        "Reserve & Surplus": "1.1.1 - Unrestricted Funds",
        "Corpus Fund": "1.1.1 - Unrestricted Funds",
        "Profit & Loss": "1.1.1 - Unrestricted Funds",
        "Temple Construction": "1.1.1 - Unrestricted Funds",
        "Trust Fund": "1.1.1 - Unrestricted Funds",
        
        # INCOME (3.x)
        "Direct Income": "3.2 - Revenue From Operation",
        "Sales": "3.2 - Revenue From Operation",
        "Service": "3.2 - Revenue From Operation",
        "books & paraphernalia sale": "3.2 - Revenue From Operation",
        "Books Sales": "3.2 - Revenue From Operation",
        
        "Donation (Temple": "3.1.2 - Specific Donation",
        "Donation Income": "3.1.1 - General Donation",
        "Donations Income": "3.1.1 - General Donation",
        
        "Indirect Income": "3.3 - Other Income",
        "Income Tax Refund": "3.3 - Other Income",
        "Interest Income": "3.3 - Other Income",
        
        # EXPENSES (4.x)
        "Direct Expenses": "4.1 - Charitable Expenses",
        "Stock Expenses": "4.2 - Material consumed / distributed",
        "Cost of Goods Sold": "4.2 - Material consumed / distributed",
        "Expenses Included": "4.2 - Material consumed / distributed",
        "Stock Adjustment": "4.2 - Material consumed / distributed",
        "Customs Duty Expense": "4.2 - Material consumed / distributed",
        
        "Worship & Rituals": "4.1 - Charitable Expenses",
        "Purchases (Books": "4.2 - Material consumed / distributed",
        "Vegetable Expenses": "4.1 - Charitable Expenses",
        "Grocery Expenses": "4.1 - Charitable Expenses",
        "Charitable Expenses": "4.1 - Charitable Expenses",
        "Festival Expenses": "4.1 - Charitable Expenses",
        "Raw Material Expenses": "4.2 - Material consumed / distributed",
        
        "Akshaya Yatra Expenses": "4.1 - Charitable Expenses",
        "Akshaya Yatra Trip": "4.1 - Charitable Expenses",
        "Char Dham": "4.1 - Charitable Expenses",
        "Nepal Muktinath": "4.1 - Charitable Expenses",
        "Rampath Yatra": "4.1 - Charitable Expenses",
        "Vrindavan Trip": "4.1 - Charitable Expenses",
        "YTP": "4.1 - Charitable Expenses",
        "Publicity and Promotion Exp. (Yatra)": "4.1 - Charitable Expenses",
        "Tour and Travel Expenses": "4.1 - Charitable Expenses",
        
        "Indirect Expenses": "4.7 - Other Expenses",
        "Administrative Expenses": "4.7 - Other Expenses",
        "Commission on Sales": "4.7 - Other Expenses",
        "Entertainment Expenses": "4.7 - Other Expenses",
        "Exchange Gain/Loss": "4.7 - Other Expenses",
        "Freight and Forwarding": "4.7 - Other Expenses",
        "Gain/Loss on Asset": "4.7 - Other Expenses",
        "Impairment": "4.7 - Other Expenses",
        "Legal Expenses": "4.7 - Other Expenses",
        "Marketing Expenses": "4.7 - Other Expenses",
        "Miscellaneous Expenses": "4.7 - Other Expenses",
        "Office Maintenance": "4.7 - Other Expenses",
        "Office Rent": "4.7 - Other Expenses",
        "Postal Expenses": "4.7 - Other Expenses",
        "Print and Stationery": "4.7 - Other Expenses",
        "Round Off": "4.7 - Other Expenses",
        "Salary": "4.4 - Employee benefits expenses",
        "Sales Expenses": "4.7 - Other Expenses",
        "Telephone Expenses": "4.7 - Other Expenses",
        "Travel Expenses": "4.7 - Other Expenses",
        "Utility Expenses": "4.7 - Other Expenses",
        "Write Off": "4.7 - Other Expenses",
        "GST Expense": "4.7 - Other Expenses",
        "Gateway Expenses": "4.7 - Other Expenses",
        "Bank Charges": "4.7 - Other Expenses",
        "Ashram Expenses": "4.7 - Other Expenses",
        "Flower Expenses": "4.1 - Charitable Expenses",
        "Housekeeping Expenses": "4.7 - Other Expenses",
        "Fuel Expenses": "4.7 - Other Expenses",
        "Interest on TDS": "4.6 - Finance Cost",
        "Cultural Trips": "4.2 - Cultural Promotion Expenses",
        "Legal & Professional": "4.7 - Other Expenses",
        "Audit Fees": "4.7 - Other Expenses",
        "Packing Expenses": "4.7 - Other Expenses",
        "Labour Expenses": "4.7 - Other Expenses",
        "TDS Return Filing": "4.7 - Other Expenses",
        "Remuneration Expenses": "4.4 - Employee benefits expenses",
        "decoration": "4.1 - Charitable Expenses",
        "Fuel Charge": "4.7 - Other Expenses",
        "Function Exp": "4.1 - Charitable Expenses",
        "HR Expenses": "4.4 - Employee benefits expenses",
        "Incentive + conveyance": "4.4 - Employee benefits expenses",
        "Janmashtami Expenses": "4.1 - Charitable Expenses",
        "staff walfare": "4.4 - Employee benefits expenses",
        "Telecommunication Expenses": "4.7 - Other Expenses",
        "Transport Expenses": "4.7 - Other Expenses",
        "Transportation Charges": "4.7 - Other Expenses",
        "Trip Expenses": "4.2 - Cultural Promotion Expenses",
        "Economy Trip": "4.2 - Cultural Promotion Expenses",
        "Folk Trip": "4.2 - Cultural Promotion Expenses",
        "Heritage Tour": "4.2 - Cultural Promotion Expenses",
        "Yurop Trip": "4.2 - Cultural Promotion Expenses",
        "Publicity & Promotion": "4.2 - Cultural Promotion Expenses",
        "Membership Fee": "4.7 - Other Expenses",
        "Youth Programs Expenses": "4.2 - Cultural Promotion Expenses",
    }
    
    return mapping


def find_best_parent(account_name: str, account_type: str, mapping: Dict) -> str:
    """
    Find the best parent for an account based on name patterns and type
    
    Args:
        account_name: Account name without company abbr
        account_type: Account type from ERPNext
        mapping: Dictionary of patterns to parent accounts
        
    Returns:
        Parent account number (e.g., "2.2.5 - Short Term Loans and Advances")
    """
    # Check for exact or partial matches
    for pattern, parent in mapping.items():
        if pattern.lower() in account_name.lower():
            return parent
    
    # Fallback based on account type if no pattern match
    type_fallbacks = {
        "Bank": "2.2.4 - Cash and bank balances",
        "Cash": "2.2.4 - Cash and bank balances",
        "Receivable": "2.2.3 - Accounts Receivable",
        "Payable": "1.3.2 - Accounts Payable",
        "Tax": "1.3.3 - Other Current Liabilities",
        "Stock": "2.2.2 - Inventories",
        "Fixed Asset": "2.1.1.1 - Property Plant and Equipment",
        "Depreciation": "4.5 - Depreciation and amortization expenses",
        "Income Account": "3.3 - Other Income",
        "Expense Account": "4.7 - Other Expenses",
    }
    
    if account_type:
        for type_key, parent in type_fallbacks.items():
            if type_key.lower() in account_type.lower():
                return parent
    
    return None


def get_all_kota_accounts():
    """
    Get all accounts from Kota that need reorganization
    Returns accounts that are NOT already under numbered parents
    """
    company = "Radha Krishna Mandir Foundation Kota"
    company_abbr = frappe.get_cached_value("Company", company, "abbr")
    
    # Get all accounts
    accounts = frappe.get_all(
        "Account",
        filters={"company": company},
        fields=["name", "account_name", "account_number", "parent_account", "is_group", "account_type", "lft"],
        order_by="lft ASC"
    )
    
    # Get list of numbered parent accounts
    numbered_parents = set()
    for acc in accounts:
        if acc['account_number'] and acc['is_group']:
            numbered_parents.add(acc['name'])
    
    # Find accounts that need to be moved
    accounts_to_move = []
    for acc in accounts:
        # Skip root accounts
        if not acc['parent_account']:
            continue
        
        # Skip if already under a numbered parent
        if acc['parent_account'] in numbered_parents:
            continue
        
        # Skip if this IS a numbered parent
        if acc['account_number'] and acc['is_group']:
            continue
        
        accounts_to_move.append(acc)
    
    return accounts_to_move, numbered_parents, company_abbr


def move_account_to_new_parent(account_name: str, new_parent_name: str, company_abbr: str):
    """
    Move an account to a new parent
    """
    full_parent_name = f"{new_parent_name} - {company_abbr}"
    
    # Check if parent exists
    if not frappe.db.exists("Account", full_parent_name):
        return False, f"Parent not found: {full_parent_name}"
    
    try:
        account = frappe.get_doc("Account", account_name)
        old_parent = account.parent_account
        
        # If already correct, skip
        if old_parent == full_parent_name:
            return True, "Already correct"
        
        # Update parent
        account.parent_account = full_parent_name
        
        # Save with flags
        frappe.flags.ignore_permissions = True
        account.flags.ignore_mandatory = True
        account.save()
        frappe.db.commit()
        
        return True, f"Moved from {old_parent}"
        
    except Exception as e:
        frappe.db.rollback()
        return False, str(e)


def reorganize_all_kota_accounts():
    """
    Main function to reorganize all Kota accounts under numbered parents
    """
    print(f"\n{'='*80}")
    print(f"INTELLIGENT COA REORGANIZATION")
    print(f"{'='*80}\n")
    
    # Get accounts that need reorganization
    accounts_to_move, numbered_parents, company_abbr = get_all_kota_accounts()
    
    print(f"Found {len(accounts_to_move)} accounts that need reorganization")
    print(f"Numbered parent accounts: {len(numbered_parents)}\n")
    
    # Get mapping
    mapping = get_intelligent_account_mapping()
    
    # Statistics
    stats = {
        "moved": 0,
        "skipped": 0,
        "errors": 0,
        "no_match": 0
    }
    
    no_match_accounts = []
    
    # Process each account
    for acc in accounts_to_move:
        account_name_only = acc['account_name']
        
        # Find best parent
        best_parent = find_best_parent(account_name_only, acc['account_type'], mapping)
        
        if not best_parent:
            stats['no_match'] += 1
            no_match_accounts.append(f"{acc['name']} (type: {acc['account_type']})")
            print(f"  ? No match found: {account_name_only}")
            continue
        
        # Move account
        success, message = move_account_to_new_parent(acc['name'], best_parent, company_abbr)
        
        if success:
            if "Already correct" in message:
                stats['skipped'] += 1
                print(f"  ✓ Already correct: {account_name_only}")
            else:
                stats['moved'] += 1
                print(f"  ✓ Moved: {account_name_only}")
                print(f"    → {best_parent}")
        else:
            stats['errors'] += 1
            print(f"  ✗ Error: {account_name_only}")
            print(f"    {message}")
    
    # Summary
    print(f"\n{'='*80}")
    print(f"REORGANIZATION SUMMARY")
    print(f"{'='*80}")
    print(f"  Moved:     {stats['moved']} accounts")
    print(f"  Skipped:   {stats['skipped']} accounts")
    print(f"  Errors:    {stats['errors']} accounts")
    print(f"  No match:  {stats['no_match']} accounts")
    print(f"{'='*80}\n")
    
    if no_match_accounts:
        print(f"\nAccounts with no match (need manual review):")
        for acc in no_match_accounts[:20]:
            print(f"  - {acc}")
        if len(no_match_accounts) > 20:
            print(f"  ... and {len(no_match_accounts) - 20} more")
    
    return stats


def show_help():
    """Display help"""
    print("\n" + "="*80)
    print("INTELLIGENT COA REORGANIZATION - COMMANDS")
    print("="*80 + "\n")
    
    print("  reorganize_all_kota_accounts()")
    print("    → Intelligently reorganize all Kota accounts\n")
    
    print("  show_help()")
    print("    → Show this help\n")
    
    print("="*80 + "\n")


# Auto-display help
if __name__ != "__main__":
    print("\n💡 Type show_help() to see available commands\n")
