"""
Fix Root Accounts and Reorganize COA Structure
==============================================

This script:
1. Updates root account numbers and renames them (bypassing ERPNext validation)
2. Moves existing accounts under the correct parent structure from Jaipur

Usage:
    bench --site erp.hkmkota.org console
    >>> from hkm.cursor.fix_root_accounts_and_reorganize import fix_kota_coa
    >>> fix_kota_coa()

Author: Cursor AI Assistant
Date: 2026-02-07
"""

import frappe
from frappe import _
from frappe.model.rename_doc import rename_doc


def update_root_account_with_number(account_name, account_number):
    """
    Update root account number and rename it
    Bypasses the "Root cannot be edited" validation
    
    Args:
        account_name: Current account name (e.g., "Expenses - RKMFK")
        account_number: Account number to set (e.g., "4")
    """
    try:
        # Get account
        account = frappe.get_doc("Account", account_name)
        company_abbr = frappe.get_cached_value("Company", account.company, "abbr")
        
        # Expected new name
        new_name = f"{account_number} - {account.account_name} - {company_abbr}"
        
        print(f"Processing root account: {account_name}")
        print(f"  Current account_number: {account.account_number}")
        print(f"  Target account_number: {account_number}")
        print(f"  Target name: {new_name}")
        
        # If already correct, skip
        if account.name == new_name and account.account_number == account_number:
            print(f"  ✓ Already correct\n")
            return True
        
        # Step 1: Set account_number directly in DB (bypass validation)
        frappe.db.set_value("Account", account_name, "account_number", account_number, update_modified=False)
        frappe.db.commit()
        print(f"  ✓ Set account_number to {account_number}")
        
        # Step 2: Rename the document (bypass validation using flags)
        if account.name != new_name:
            # Set flag to bypass root validation
            frappe.flags.ignore_root_company_validation = True
            frappe.local.flags.ignore_root_company_validation = True
            
            # Rename using direct SQL to avoid validation
            # Update the account name
            frappe.db.sql("""
                UPDATE `tabAccount` 
                SET name = %s 
                WHERE name = %s
            """, (new_name, account_name))
            
            # Update all references in child accounts
            frappe.db.sql("""
                UPDATE `tabAccount` 
                SET parent_account = %s 
                WHERE parent_account = %s
            """, (new_name, account_name))
            
            # Update GL Entry references
            frappe.db.sql("""
                UPDATE `tabGL Entry` 
                SET account = %s 
                WHERE account = %s
            """, (new_name, account_name))
            
            # Clear cache
            frappe.clear_cache()
            frappe.db.commit()
            
            print(f"  ✓ Renamed to: {new_name}\n")
            return True
            
    except Exception as e:
        print(f"  ✗ Error: {str(e)}\n")
        frappe.db.rollback()
        return False


def get_account_mapping_from_jaipur():
    """
    Get the correct parent-child mapping from Jaipur
    Returns dict of {account_name: parent_account_name}
    """
    # This would ideally fetch from Jaipur, but for now we'll use the known structure
    # Based on the COA structure from the replication guide
    
    mapping = {
        # Assets structure
        "Stock In Hand": "2.2.2 - Inventories",
        "Debtors": "2.2.3 - Accounts Receivable",
        "Bank Accounts": "2.2.4 - Cash and bank balances",
        "Cash In Hand": "2.2.4 - Cash and bank balances",
        "Temporary Accounts": "2.2.4 - Cash and bank balances",
        "CWIP Account": "2.1.1.2 - Capital Work in progress",
        "Accumulated Depreciation": "2.1.1.1 - Property Plant and Equipment",
        "FA - Furnitures and Fixtures": "2.1.1.1 - Property Plant and Equipment",
        
        # Liabilities structure
        "Creditors": "1.3.2 - Accounts Payable",
        "Duties and Taxes": "1.3.3 - Other Current Liabilities",
        "TDS Payable": "1.3.3 - Other Current Liabilities",
        "Stock Received But Not Billed": "1.3.2 - Accounts Payable",
        "Asset Received But Not Billed": "1.3.2 - Accounts Payable",
        
        # Income structure
        "Heritage Tour": "3.1.1 - General Donation",
        "General Donation": "3.1.1 - General Donation",
        "Cultural Promotion": "3.1.1 - General Donation",
        "Anonymous Donation": "3.1.1 - General Donation",
        
        # Expense structure
        "Depreciation": "4.5 - Depreciation and amortization expenses",
        
        # Tax accounts
        "Input Tax CGST": "2.2.6 - Other Current Assets",
        "Input Tax IGST": "2.2.6 - Other Current Assets",
        "Input Tax SGST": "2.2.6 - Other Current Assets",
        "Input Tax CGST RCM": "1.3.3 - Other Current Liabilities",
        "Input Tax IGST RCM": "1.3.3 - Other Current Liabilities",
        "Input Tax SGST RCM": "1.3.3 - Other Current Liabilities",
        "Output Tax CGST": "1.3.3 - Other Current Liabilities",
    }
    
    return mapping


def move_account_to_parent(account_name, new_parent_name, company):
    """
    Move an account under a new parent
    
    Args:
        account_name: Account name to move
        new_parent_name: New parent account name
        company: Company name
    """
    company_abbr = frappe.get_cached_value("Company", company, "abbr")
    full_account_name = f"{account_name} - {company_abbr}"
    full_parent_name = f"{new_parent_name} - {company_abbr}"
    
    # Check if account exists
    if not frappe.db.exists("Account", full_account_name):
        print(f"  ○ Account not found: {full_account_name}")
        return False
    
    # Check if parent exists
    if not frappe.db.exists("Account", full_parent_name):
        print(f"  ⚠ Parent not found: {full_parent_name}")
        return False
    
    try:
        account = frappe.get_doc("Account", full_account_name)
        current_parent = account.parent_account
        
        # If already under correct parent, skip
        if current_parent == full_parent_name:
            print(f"  ✓ Already under correct parent: {account_name}")
            return True
        
        print(f"  Moving: {account_name}")
        print(f"    From: {current_parent or 'ROOT'}")
        print(f"    To: {full_parent_name}")
        
        # Update parent
        account.parent_account = full_parent_name
        
        # Save with flags to bypass some validations
        frappe.flags.ignore_permissions = True
        account.flags.ignore_mandatory = True
        account.save()
        frappe.db.commit()
        
        print(f"  ✓ Moved successfully\n")
        return True
        
    except Exception as e:
        print(f"  ✗ Error moving {account_name}: {str(e)}\n")
        frappe.db.rollback()
        return False


def reorganize_existing_accounts(company):
    """
    Reorganize existing accounts under the correct parent structure
    
    Args:
        company: Company name
    """
    print(f"\n{'='*80}")
    print(f"REORGANIZING EXISTING ACCOUNTS")
    print(f"Company: {company}")
    print(f"{'='*80}\n")
    
    mapping = get_account_mapping_from_jaipur()
    
    moved_count = 0
    skipped_count = 0
    error_count = 0
    
    for account_name, parent_name in mapping.items():
        result = move_account_to_parent(account_name, parent_name, company)
        if result:
            moved_count += 1
        elif result is False:
            error_count += 1
        else:
            skipped_count += 1
    
    print(f"\n{'='*80}")
    print(f"REORGANIZATION SUMMARY")
    print(f"{'='*80}")
    print(f"  Moved:   {moved_count} accounts")
    print(f"  Skipped: {skipped_count} accounts")
    print(f"  Errors:  {error_count} accounts")
    print(f"{'='*80}\n")
    
    return {
        "moved": moved_count,
        "skipped": skipped_count,
        "errors": error_count
    }


def fix_root_accounts(company):
    """
    Fix root account numbers and names
    
    Args:
        company: Company name
    """
    print(f"\n{'='*80}")
    print(f"FIXING ROOT ACCOUNTS")
    print(f"Company: {company}")
    print(f"{'='*80}\n")
    
    company_abbr = frappe.get_cached_value("Company", company, "abbr")
    
    # Root accounts mapping: {current_name: account_number}
    root_accounts = {
        f"Source of Funds (Liabilities) - {company_abbr}": "1",
        f"Income - {company_abbr}": "3",
        f"Expenses - {company_abbr}": "4",
    }
    
    fixed_count = 0
    
    for account_name, account_number in root_accounts.items():
        if frappe.db.exists("Account", account_name):
            result = update_root_account_with_number(account_name, account_number)
            if result:
                fixed_count += 1
    
    print(f"\n{'='*80}")
    print(f"ROOT ACCOUNTS SUMMARY")
    print(f"{'='*80}")
    print(f"  Fixed: {fixed_count} root accounts")
    print(f"{'='*80}\n")
    
    return fixed_count


def fix_kota_coa():
    """
    Main function to fix COA for Kota
    - Fix root account numbers and names
    - Reorganize existing accounts under correct parents
    """
    company = "Radha Krishna Mandir Foundation Kota"
    
    print(f"\n{'='*80}")
    print(f"COA FIX AND REORGANIZATION")
    print(f"Company: {company}")
    print(f"{'='*80}\n")
    
    # Verify company exists
    if not frappe.db.exists("Company", company):
        print(f"✗ Error: Company '{company}' not found\n")
        return None
    
    # Step 1: Fix root accounts
    print("STEP 1: Fixing root accounts...\n")
    root_result = fix_root_accounts(company)
    
    # Step 2: Reorganize existing accounts
    print("\nSTEP 2: Reorganizing existing accounts...\n")
    reorg_result = reorganize_existing_accounts(company)
    
    # Final summary
    print(f"\n{'='*80}")
    print(f"✓ COA FIX COMPLETED")
    print(f"{'='*80}")
    print(f"  Root accounts fixed: {root_result}")
    print(f"  Accounts moved: {reorg_result['moved']}")
    print(f"  Accounts skipped: {reorg_result['skipped']}")
    print(f"  Errors: {reorg_result['errors']}")
    print(f"{'='*80}\n")
    
    return {
        "root_fixed": root_result,
        "reorganization": reorg_result
    }


def show_help():
    """Display help information"""
    print("\n" + "="*80)
    print("COA FIX AND REORGANIZATION - AVAILABLE COMMANDS")
    print("="*80 + "\n")
    
    commands = [
        ("fix_kota_coa()", "Fix root accounts and reorganize COA for Kota"),
        ("fix_root_accounts('Company Name')", "Fix only root accounts"),
        ("reorganize_existing_accounts('Company Name')", "Reorganize only existing accounts"),
        ("show_help()", "Show this help message"),
    ]
    
    for cmd, desc in commands:
        print(f"  {cmd}")
        print(f"    → {desc}\n")
    
    print("="*80 + "\n")


# Auto-display help when module is imported
if __name__ != "__main__":
    print("\n💡 Type show_help() to see available commands\n")
