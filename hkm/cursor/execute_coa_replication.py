"""
Simple Execution Script for COA Replication
============================================

This script provides simple commands to replicate COA structure.

Usage Examples:
--------------

1. Replicate from Jaipur to Kota (cross-site):
   bench --site erp.hkmkota.org console
   >>> from hkm.cursor.execute_coa_replication import replicate_jaipur_to_kota
   >>> replicate_jaipur_to_kota()

2. Export COA to JSON (on source site):
   bench --site hkmjerp.in console
   >>> from hkm.cursor.execute_coa_replication import export_jaipur_coa
   >>> export_jaipur_coa()

3. Import COA from JSON (on target site):
   bench --site erp.hkmkota.org console
   >>> from hkm.cursor.execute_coa_replication import import_to_kota
   >>> import_to_kota("/tmp/coa_jaipur.json")

4. Fix account names on current site:
   >>> from hkm.cursor.execute_coa_replication import fix_all_account_names
   >>> fix_all_account_names()
"""

import frappe
from hkm.cursor.cross_site_coa_replication import (
    CrossSiteCOAReplicator,
    export_coa_structure_to_json,
    import_coa_structure_from_json
)
from hkm.cursor.coa_replication import (
    fix_account_names_with_numbers,
    replicate_coa_to_company,
    replicate_coa_to_all_companies_on_site
)


def replicate_jaipur_to_kota():
    """
    Replicate COA from Sri Radha Krishna Mandir Foundation (Jaipur) 
    to Radha Krishna Mandir Foundation Kota
    
    Run this on: erp.hkmkota.org
    """
    print("\n" + "="*80)
    print("COA REPLICATION: Jaipur → Kota")
    print("="*80 + "\n")
    
    # Check if we're on the right site
    current_site = frappe.local.site
    print(f"Current site: {current_site}\n")
    
    # Configuration
    SOURCE_SITE = "hkmjerp_in"
    SOURCE_COMPANY = "Sri Radha Krishna Mandir Foundation"
    TARGET_COMPANY = "Radha Krishna Mandir Foundation Kota"
    
    # Verify target company exists
    if not frappe.db.exists("Company", TARGET_COMPANY):
        print(f"✗ Error: Company '{TARGET_COMPANY}' not found\n")
        print("Available companies on this site:")
        companies = frappe.get_all("Company", fields=["name", "abbr"])
        for company in companies:
            print(f"  - {company['name']} ({company['abbr']})")
        print("\nPlease update TARGET_COMPANY in the script if needed.\n")
        return None
    
    # Confirm before proceeding
    print(f"Source: {SOURCE_SITE} / {SOURCE_COMPANY}")
    print(f"Target: {current_site} / {TARGET_COMPANY}\n")
    
    response = input("Proceed with replication? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Replication cancelled.")
        return None
    
    # Create replicator
    replicator = CrossSiteCOAReplicator(
        source_site=SOURCE_SITE,
        source_company=SOURCE_COMPANY,
        target_company=TARGET_COMPANY
    )
    
    # Run replication
    try:
        result = replicator.replicate()
        
        print("\n" + "="*80)
        print("✓ REPLICATION COMPLETED SUCCESSFULLY")
        print("="*80 + "\n")
        
        return result
        
    except Exception as e:
        print(f"\n✗ Error during replication: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return None


def export_jaipur_coa(output_file="/tmp/coa_jaipur.json"):
    """
    Export COA structure from Sri Radha Krishna Mandir Foundation to JSON
    
    Run this on: hkmjerp.in
    
    Args:
        output_file: Path to save JSON file
    """
    print("\n" + "="*80)
    print("EXPORTING COA STRUCTURE TO JSON")
    print("="*80 + "\n")
    
    company = "Sri Radha Krishna Mandir Foundation"
    
    # Verify company exists
    if not frappe.db.exists("Company", company):
        print(f"✗ Error: Company '{company}' not found\n")
        print("Available companies:")
        companies = frappe.get_all("Company", fields=["name"])
        for c in companies:
            print(f"  - {c['name']}")
        return None
    
    try:
        result = export_coa_structure_to_json(company, output_file)
        print(f"\n✓ Export completed: {result}\n")
        print("Next steps:")
        print(f"1. Copy file to target site: scp {output_file} target-server:/tmp/")
        print(f"2. On target site, run: import_to_kota('{output_file}')\n")
        return result
        
    except Exception as e:
        print(f"\n✗ Error during export: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return None


def import_to_kota(json_file="/tmp/coa_jaipur.json"):
    """
    Import COA structure from JSON to Radha Krishna Mandir Foundation Kota
    
    Run this on: erp.hkmkota.org
    
    Args:
        json_file: Path to JSON file with COA structure
    """
    print("\n" + "="*80)
    print("IMPORTING COA STRUCTURE FROM JSON")
    print("="*80 + "\n")
    
    target_company = "Radha Krishna Mandir Foundation Kota"
    
    # Verify target company exists
    if not frappe.db.exists("Company", target_company):
        print(f"✗ Error: Company '{target_company}' not found\n")
        print("Available companies:")
        companies = frappe.get_all("Company", fields=["name"])
        for c in companies:
            print(f"  - {c['name']}")
        return None
    
    # Verify JSON file exists
    import os
    if not os.path.exists(json_file):
        print(f"✗ Error: JSON file not found: {json_file}\n")
        return None
    
    print(f"Source file: {json_file}")
    print(f"Target company: {target_company}\n")
    
    response = input("Proceed with import? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Import cancelled.")
        return None
    
    try:
        result = import_coa_structure_from_json(json_file, target_company)
        
        print("\n" + "="*80)
        print("✓ IMPORT COMPLETED SUCCESSFULLY")
        print("="*80 + "\n")
        
        return result
        
    except Exception as e:
        print(f"\n✗ Error during import: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return None


def fix_all_account_names():
    """
    Fix account names for all companies on current site
    This renames accounts to include account numbers in the name
    
    Run this on any site to fix account naming
    """
    print("\n" + "="*80)
    print("FIXING ACCOUNT NAMES FOR ALL COMPANIES")
    print("="*80 + "\n")
    
    companies = frappe.get_all("Company", fields=["name", "abbr"])
    print(f"Found {len(companies)} companies:\n")
    for company in companies:
        print(f"  - {company['name']} ({company['abbr']})")
    
    print()
    response = input("Proceed with fixing account names? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Operation cancelled.")
        return None
    
    total_fixed = 0
    
    for company in companies:
        print(f"\n{'='*80}")
        print(f"Processing: {company['name']}")
        print(f"{'='*80}\n")
        
        try:
            fixed = fix_account_names_with_numbers(company['name'])
            total_fixed += fixed
            print(f"\n✓ Fixed {fixed} accounts for {company['name']}")
            
        except Exception as e:
            print(f"\n✗ Error processing {company['name']}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*80}")
    print(f"TOTAL FIXED: {total_fixed} accounts across all companies")
    print(f"{'='*80}\n")
    
    return total_fixed


def replicate_within_site(target_company, source_company="Hare Krishna Movement Jaipur"):
    """
    Replicate COA from one company to another on the same site
    
    Args:
        target_company: Target company name
        source_company: Source company name (default: Hare Krishna Movement Jaipur)
    """
    print("\n" + "="*80)
    print("COA REPLICATION WITHIN SAME SITE")
    print("="*80 + "\n")
    
    # Verify companies exist
    if not frappe.db.exists("Company", source_company):
        print(f"✗ Error: Source company '{source_company}' not found\n")
        return None
    
    if not frappe.db.exists("Company", target_company):
        print(f"✗ Error: Target company '{target_company}' not found\n")
        return None
    
    print(f"Source: {source_company}")
    print(f"Target: {target_company}\n")
    
    response = input("Proceed with replication? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Replication cancelled.")
        return None
    
    try:
        result = replicate_coa_to_company(target_company, source_company)
        
        print("\n" + "="*80)
        print("✓ REPLICATION COMPLETED SUCCESSFULLY")
        print("="*80 + "\n")
        
        return result
        
    except Exception as e:
        print(f"\n✗ Error during replication: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return None


def replicate_to_all_companies(source_company="Hare Krishna Movement Jaipur"):
    """
    Replicate COA from source company to ALL other companies on current site
    
    Args:
        source_company: Source company name
    """
    print("\n" + "="*80)
    print("COA REPLICATION TO ALL COMPANIES")
    print("="*80 + "\n")
    
    # Verify source company exists
    if not frappe.db.exists("Company", source_company):
        print(f"✗ Error: Source company '{source_company}' not found\n")
        return None
    
    companies = frappe.get_all("Company", fields=["name"])
    target_companies = [c['name'] for c in companies if c['name'] != source_company]
    
    print(f"Source: {source_company}")
    print(f"\nTarget companies ({len(target_companies)}):")
    for company in target_companies:
        print(f"  - {company}")
    
    print()
    response = input("Proceed with replication to ALL companies? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Replication cancelled.")
        return None
    
    try:
        result = replicate_coa_to_all_companies_on_site()
        
        print("\n" + "="*80)
        print("✓ REPLICATION COMPLETED FOR ALL COMPANIES")
        print("="*80 + "\n")
        
        return result
        
    except Exception as e:
        print(f"\n✗ Error during replication: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return None


def verify_coa_structure(company):
    """
    Verify COA structure for a company
    
    Args:
        company: Company name to verify
    """
    print("\n" + "="*80)
    print(f"VERIFYING COA STRUCTURE: {company}")
    print("="*80 + "\n")
    
    if not frappe.db.exists("Company", company):
        print(f"✗ Error: Company '{company}' not found\n")
        return None
    
    # Get all accounts with numbers
    accounts = frappe.get_all(
        "Account",
        filters={"company": company, "account_number": ["!=", ""]},
        fields=["name", "account_name", "account_number", "parent_account", "is_group"],
        order_by="lft ASC"
    )
    
    print(f"Total accounts with numbers: {len(accounts)}\n")
    
    # Group by root category
    from collections import defaultdict
    by_root = defaultdict(list)
    
    for acc in accounts:
        root = acc['account_number'].split('.')[0]
        by_root[root].append(acc)
    
    # Display structure
    for root in sorted(by_root.keys()):
        accs = by_root[root]
        root_acc = next((a for a in accs if a['account_number'] == root), None)
        
        if root_acc:
            print(f"\n{root} - {root_acc['account_name']} ({len(accs)} accounts)")
        else:
            print(f"\n{root} - ({len(accs)} accounts)")
        
        # Show first 10 accounts
        for acc in accs[:10]:
            indent = "  " * (len(acc['account_number'].split('.')) - 1)
            group_marker = "📁" if acc['is_group'] else "📄"
            print(f"  {indent}{group_marker} {acc['account_number']} - {acc['account_name']}")
        
        if len(accs) > 10:
            print(f"  ... and {len(accs) - 10} more accounts")
    
    # Check for issues
    print(f"\n{'='*80}")
    print("CHECKING FOR ISSUES")
    print(f"{'='*80}\n")
    
    issues = []
    
    # Check for accounts without proper naming
    company_abbr = frappe.get_cached_value("Company", company, "abbr")
    for acc in accounts:
        expected_name = f"{acc['account_number']} - {acc['account_name']} - {company_abbr}"
        if acc['name'] != expected_name:
            issues.append(f"Name mismatch: {acc['name']} (expected: {expected_name})")
    
    if issues:
        print(f"Found {len(issues)} issues:\n")
        for issue in issues[:10]:
            print(f"  ⚠ {issue}")
        if len(issues) > 10:
            print(f"  ... and {len(issues) - 10} more issues")
    else:
        print("✓ No issues found")
    
    print(f"\n{'='*80}\n")
    
    return {
        "total_accounts": len(accounts),
        "by_category": {k: len(v) for k, v in by_root.items()},
        "issues": len(issues)
    }


def show_help():
    """
    Display help information
    """
    print("\n" + "="*80)
    print("COA REPLICATION - AVAILABLE COMMANDS")
    print("="*80 + "\n")
    
    commands = [
        ("replicate_jaipur_to_kota()", "Replicate from Jaipur to Kota (cross-site)"),
        ("export_jaipur_coa()", "Export Jaipur COA to JSON file"),
        ("import_to_kota('/path/to/file.json')", "Import COA from JSON to Kota"),
        ("fix_all_account_names()", "Fix account names on current site"),
        ("replicate_within_site('Target Company')", "Replicate within same site"),
        ("replicate_to_all_companies()", "Replicate to all companies on site"),
        ("verify_coa_structure('Company Name')", "Verify COA structure"),
        ("show_help()", "Show this help message"),
    ]
    
    for cmd, desc in commands:
        print(f"  {cmd}")
        print(f"    → {desc}\n")
    
    print("="*80 + "\n")
    
    print("TYPICAL WORKFLOW:\n")
    print("Method 1 - Direct Cross-Site Replication:")
    print("  1. On erp.hkmkota.org: replicate_jaipur_to_kota()")
    print("  2. Verify: verify_coa_structure('Radha Krishna Mandir Foundation Kota')\n")
    
    print("Method 2 - JSON Export/Import:")
    print("  1. On hkmjerp.in: export_jaipur_coa()")
    print("  2. Copy JSON file to target server")
    print("  3. On erp.hkmkota.org: import_to_kota('/tmp/coa_jaipur.json')")
    print("  4. Verify: verify_coa_structure('Radha Krishna Mandir Foundation Kota')\n")
    
    print("="*80 + "\n")


# Auto-display help when module is imported
if __name__ != "__main__":
    print("\n💡 Type show_help() to see available commands\n")
