"""
Replicate COA to All Kota Companies
====================================

This script replicates the Jaipur COA structure to all companies on Kota site:
- Hare Krishna Movement Kota
- Touchstone Foundation Kota

Usage:
    bench --site erp.hkmkota.org console
    >>> from hkm.cursor.replicate_to_all_kota_companies import replicate_to_all_kota
    >>> replicate_to_all_kota()

Author: Cursor AI Assistant
Date: 2026-02-07
"""

import frappe
from hkm.cursor.cross_site_coa_replication import import_coa_structure_from_json
from hkm.cursor.fix_root_accounts_and_reorganize import fix_root_accounts
from hkm.cursor.intelligent_coa_reorganization import reorganize_all_kota_accounts


def replicate_to_company(company_name, json_file="/tmp/coa_jaipur.json"):
    """
    Replicate COA to a specific company
    
    Args:
        company_name: Target company name
        json_file: Path to COA JSON export from Jaipur
    """
    print(f"\n{'='*80}")
    print(f"REPLICATING COA TO: {company_name}")
    print(f"{'='*80}\n")
    
    # Step 1: Import from JSON
    print("STEP 1: Importing COA structure from JSON...")
    try:
        result = import_coa_structure_from_json(json_file, company_name)
        print(f"\n✓ Import completed")
        print(f"  Created: {result.get('created', 0)}")
        print(f"  Updated: {result.get('updated', 0)}")
        print(f"  Renamed: {result.get('renamed', 0)}")
        print(f"  Errors: {result.get('errors', 0)}")
    except Exception as e:
        print(f"✗ Error during import: {str(e)}")
        return None
    
    # Step 2: Fix root accounts
    print(f"\nSTEP 2: Fixing root accounts...")
    try:
        fixed = fix_root_accounts(company_name)
        print(f"✓ Fixed {fixed} root accounts")
    except Exception as e:
        print(f"✗ Error fixing root accounts: {str(e)}")
    
    # Step 3: Reorganize all accounts
    print(f"\nSTEP 3: Reorganizing accounts under numbered parents...")
    try:
        # Temporarily modify the function to work with any company
        stats = reorganize_accounts_for_company(company_name)
        print(f"\n✓ Reorganization completed")
        print(f"  Moved: {stats['moved']}")
        print(f"  No match: {stats['no_match']}")
        print(f"  Errors: {stats['errors']}")
    except Exception as e:
        print(f"✗ Error during reorganization: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print(f"\n{'='*80}")
    print(f"✓ REPLICATION COMPLETED FOR: {company_name}")
    print(f"{'='*80}\n")
    
    return True


def reorganize_accounts_for_company(company):
    """
    Reorganize accounts for a specific company
    Modified version of intelligent_coa_reorganization for any company
    """
    from hkm.cursor.intelligent_coa_reorganization import (
        get_intelligent_account_mapping,
        find_best_parent,
        move_account_to_new_parent
    )
    
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
    
    print(f"  Found {len(accounts_to_move)} accounts to reorganize")
    
    # Get mapping
    mapping = get_intelligent_account_mapping()
    
    # Statistics
    stats = {
        "moved": 0,
        "skipped": 0,
        "errors": 0,
        "no_match": 0
    }
    
    # Process each account
    for acc in accounts_to_move:
        account_name_only = acc['account_name']
        
        # Find best parent
        best_parent = find_best_parent(account_name_only, acc['account_type'], mapping)
        
        if not best_parent:
            stats['no_match'] += 1
            continue
        
        # Move account
        success, message = move_account_to_new_parent(acc['name'], best_parent, company_abbr)
        
        if success:
            if "Already correct" in message:
                stats['skipped'] += 1
            else:
                stats['moved'] += 1
        else:
            stats['errors'] += 1
    
    return stats


def replicate_to_all_kota():
    """
    Main function to replicate COA to all Kota companies
    """
    print(f"\n{'='*80}")
    print(f"COA REPLICATION TO ALL KOTA COMPANIES")
    print(f"{'='*80}\n")
    
    # Check if JSON file exists
    json_file = "/tmp/coa_jaipur.json"
    import os
    if not os.path.exists(json_file):
        print(f"✗ Error: JSON file not found: {json_file}")
        print(f"\nPlease export COA from Jaipur first:")
        print(f"  bench --site hkmjerp.in execute \\")
        print(f"    hkm.cursor.cross_site_coa_replication.export_coa_structure_to_json \\")
        print(f"    --args '[\"Sri Radha Krishna Mandir Foundation\", \"/tmp/coa_jaipur.json\"]'")
        return None
    
    print(f"✓ Found COA export: {json_file}\n")
    
    # Companies to replicate to
    companies = [
        "Hare Krishna Movement Kota",
        "Touchstone Foundation Kota"
    ]
    
    results = {}
    
    for company in companies:
        # Check if company exists
        if not frappe.db.exists("Company", company):
            print(f"⚠ Warning: Company '{company}' not found, skipping\n")
            continue
        
        # Replicate
        result = replicate_to_company(company, json_file)
        results[company] = result
        
        # Small delay between companies
        import time
        time.sleep(2)
    
    # Final summary
    print(f"\n{'='*80}")
    print(f"FINAL SUMMARY")
    print(f"{'='*80}\n")
    
    for company, result in results.items():
        status = "✓ Success" if result else "✗ Failed"
        print(f"  {company}: {status}")
    
    print(f"\n{'='*80}\n")
    
    return results


def verify_all_companies():
    """
    Verify COA structure for all Kota companies
    """
    from hkm.cursor.execute_coa_replication import verify_coa_structure
    
    companies = [
        "Radha Krishna Mandir Foundation Kota",
        "Hare Krishna Movement Kota",
        "Touchstone Foundation Kota"
    ]
    
    print(f"\n{'='*80}")
    print(f"VERIFYING ALL KOTA COMPANIES")
    print(f"{'='*80}\n")
    
    results = {}
    
    for company in companies:
        if not frappe.db.exists("Company", company):
            continue
        
        print(f"\n{'='*80}")
        print(f"Company: {company}")
        print(f"{'='*80}\n")
        
        result = verify_coa_structure(company)
        results[company] = result
    
    # Summary
    print(f"\n{'='*80}")
    print(f"VERIFICATION SUMMARY")
    print(f"{'='*80}\n")
    
    for company, result in results.items():
        if result:
            print(f"{company}:")
            print(f"  Total accounts: {result.get('total_accounts', 0)}")
            print(f"  Issues: {result.get('issues', 0)}")
            status = "✓" if result.get('issues', 0) == 0 else "⚠"
            print(f"  Status: {status}\n")
    
    return results


def show_help():
    """Display help"""
    print("\n" + "="*80)
    print("COA REPLICATION TO ALL KOTA COMPANIES - COMMANDS")
    print("="*80 + "\n")
    
    print("  replicate_to_all_kota()")
    print("    → Replicate COA to all Kota companies\n")
    
    print("  replicate_to_company('Company Name')")
    print("    → Replicate COA to a specific company\n")
    
    print("  verify_all_companies()")
    print("    → Verify COA structure for all companies\n")
    
    print("  show_help()")
    print("    → Show this help\n")
    
    print("="*80 + "\n")


# Auto-display help
if __name__ != "__main__":
    print("\n💡 Type show_help() to see available commands\n")
