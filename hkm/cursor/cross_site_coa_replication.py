"""
Cross-Site Chart of Accounts Replication
=========================================

This script replicates the COA structure from hkmjerp.in to erp.hkmkota.org

Usage:
    bench --site erp.hkmkota.org console
    >>> from hkm.cursor.cross_site_coa_replication import replicate_coa_from_jaipur_to_kota
    >>> replicate_coa_from_jaipur_to_kota()

Author: Cursor AI Assistant
Date: 2026-02-06
"""

import frappe
import pymysql
from typing import Dict, List, Optional, Tuple
import json


class CrossSiteCOAReplicator:
    """
    Handles replication of Chart of Accounts from one site to another
    """
    
    def __init__(self, source_site: str, source_company: str, target_company: str):
        """
        Initialize the replicator
        
        Args:
            source_site: Source site database name (e.g., 'hkmjerp_in')
            source_company: Source company name
            target_company: Target company name (on current site)
        """
        self.source_site = source_site
        self.source_company = source_company
        self.target_company = target_company
        self.target_abbr = frappe.get_cached_value("Company", target_company, "abbr")
        
        # Statistics
        self.stats = {
            "created": 0,
            "updated": 0,
            "renamed": 0,
            "skipped": 0,
            "errors": 0
        }
    
    def get_source_db_connection(self):
        """
        Get database connection to source site
        """
        # Get database config from common_site_config.json
        db_config = frappe.conf.get('db_config', {})
        
        # Default connection parameters
        connection_params = {
            'host': db_config.get('host', 'localhost'),
            'user': db_config.get('user', frappe.conf.get('db_name')),
            'password': db_config.get('password', frappe.conf.get('db_password')),
            'database': self.source_site,
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }
        
        return pymysql.connect(**connection_params)
    
    def fetch_source_coa_structure(self) -> List[Dict]:
        """
        Fetch complete COA structure from source site
        Returns accounts in hierarchical order (parent-first)
        """
        print(f"\n{'='*80}")
        print(f"Fetching COA structure from {self.source_site}")
        print(f"Company: {self.source_company}")
        print(f"{'='*80}\n")
        
        try:
            conn = self.get_source_db_connection()
            cursor = conn.cursor()
            
            # Fetch all accounts ordered by lft (tree order - parent before children)
            query = """
                SELECT 
                    name,
                    account_name,
                    account_number,
                    parent_account,
                    is_group,
                    root_type,
                    report_type,
                    account_type,
                    account_currency,
                    lft,
                    rgt
                FROM `tabAccount`
                WHERE company = %s
                ORDER BY lft ASC
            """
            
            cursor.execute(query, (self.source_company,))
            accounts = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            print(f"✓ Fetched {len(accounts)} accounts from source\n")
            
            return accounts
            
        except Exception as e:
            print(f"✗ Error fetching source COA: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_target_parent_name(self, source_parent_name: str, source_accounts: List[Dict]) -> Optional[str]:
        """
        Get the corresponding parent account name in target company
        
        Args:
            source_parent_name: Parent account name from source
            source_accounts: List of all source accounts
            
        Returns:
            Target parent account name or None
        """
        if not source_parent_name:
            return None
        
        # Find the parent in source accounts
        parent_info = None
        for acc in source_accounts:
            if acc['name'] == source_parent_name:
                parent_info = acc
                break
        
        if not parent_info:
            return None
        
        # Build target parent name
        parent_account_name = parent_info['account_name']
        parent_account_number = parent_info['account_number']
        
        # Try with number first
        if parent_account_number:
            target_name = f"{parent_account_number} - {parent_account_name} - {self.target_abbr}"
            if frappe.db.exists("Account", target_name):
                return target_name
        
        # Try without number
        target_name = f"{parent_account_name} - {self.target_abbr}"
        if frappe.db.exists("Account", target_name):
            return target_name
        
        return None
    
    def create_or_update_account(self, source_account: Dict, source_accounts: List[Dict]) -> bool:
        """
        Create or update an account in target company
        
        Args:
            source_account: Source account data
            source_accounts: All source accounts (for parent lookup)
            
        Returns:
            True if successful, False otherwise
        """
        account_name = source_account['account_name']
        account_number = source_account['account_number']
        parent_account = source_account['parent_account']
        
        # Skip root accounts - they should already exist
        if not parent_account:
            print(f"○ Skipping root account: {account_name}")
            return True
        
        # Get target parent name
        target_parent = self.get_target_parent_name(parent_account, source_accounts)
        if not target_parent:
            print(f"⚠ Parent not found for {account_name}, skipping")
            self.stats['skipped'] += 1
            return False
        
        # Check if account already exists in target
        existing_account = frappe.db.get_value(
            "Account",
            {
                "account_name": account_name,
                "company": self.target_company,
                "parent_account": target_parent
            },
            ["name", "account_number"],
            as_dict=True
        )
        
        if existing_account:
            # Account exists - update number if different
            if existing_account.account_number != account_number:
                try:
                    frappe.db.set_value("Account", existing_account.name, "account_number", account_number)
                    print(f"✓ Updated: {account_number} - {account_name}")
                    self.stats['updated'] += 1
                    return True
                except Exception as e:
                    print(f"✗ Error updating {account_name}: {str(e)}")
                    self.stats['errors'] += 1
                    return False
            else:
                print(f"○ Exists: {account_number} - {account_name}")
                return True
        else:
            # Create new account
            try:
                # Get parent details
                parent_doc = frappe.get_doc("Account", target_parent)
                
                # Create account
                account_doc = frappe.new_doc("Account")
                account_doc.account_name = account_name
                account_doc.company = self.target_company
                account_doc.parent_account = target_parent
                account_doc.is_group = source_account['is_group']
                account_doc.account_number = account_number
                account_doc.root_type = parent_doc.root_type
                account_doc.report_type = parent_doc.report_type
                account_doc.account_currency = parent_doc.account_currency
                
                # Set account type if specified
                if source_account.get('account_type'):
                    account_doc.account_type = source_account['account_type']
                
                account_doc.flags.ignore_permissions = True
                account_doc.insert()
                
                print(f"✓ Created: {account_number} - {account_name}")
                self.stats['created'] += 1
                return True
                
            except Exception as e:
                print(f"✗ Error creating {account_name}: {str(e)}")
                self.stats['errors'] += 1
                return False
    
    def fix_account_names(self):
        """
        Fix all account names to include account numbers in the name
        This renames accounts to format: "number - name - abbr"
        """
        print(f"\n{'='*80}")
        print(f"Fixing account names for {self.target_company}")
        print(f"{'='*80}\n")
        
        # Get all accounts with account numbers
        accounts = frappe.get_all(
            "Account",
            filters={
                "company": self.target_company,
                "account_number": ["!=", ""]
            },
            fields=["name", "account_name", "account_number", "parent_account"]
        )
        
        print(f"Found {len(accounts)} accounts with numbers\n")
        
        for account in accounts:
            expected_name = f"{account['account_number']} - {account['account_name']} - {self.target_abbr}"
            
            # Check if name matches expected format
            if account['name'] != expected_name:
                # Skip root accounts
                if not account['parent_account']:
                    print(f"○ Skipping root: {account['name']}")
                    continue
                
                try:
                    # Set test flag to bypass idle check
                    old_flag = frappe.in_test
                    frappe.in_test = True
                    
                    try:
                        # Check if target name already exists
                        if frappe.db.exists("Account", expected_name):
                            print(f"○ Already correct: {expected_name}")
                            continue
                        
                        # Rename the account
                        frappe.rename_doc("Account", account['name'], expected_name, force=True)
                        print(f"✓ Renamed: {account['name']} -> {expected_name}")
                        self.stats['renamed'] += 1
                        
                    finally:
                        frappe.in_test = old_flag
                        
                except Exception as e:
                    print(f"✗ Error renaming {account['name']}: {str(e)}")
                    self.stats['errors'] += 1
            else:
                print(f"○ Already correct: {account['name']}")
    
    def replicate(self):
        """
        Main replication method
        """
        print(f"\n{'='*80}")
        print(f"COA REPLICATION")
        print(f"Source: {self.source_site} / {self.source_company}")
        print(f"Target: Current Site / {self.target_company}")
        print(f"{'='*80}\n")
        
        # Step 1: Fetch source structure
        source_accounts = self.fetch_source_coa_structure()
        if not source_accounts:
            print("✗ Failed to fetch source accounts")
            return self.stats
        
        # Step 2: Update root accounts first
        print(f"\n{'='*80}")
        print("Step 1: Updating root accounts")
        print(f"{'='*80}\n")
        
        root_accounts = [acc for acc in source_accounts if not acc['parent_account']]
        for root_acc in root_accounts:
            if root_acc['account_number']:
                target_name = f"{root_acc['account_name']} - {self.target_abbr}"
                if frappe.db.exists("Account", target_name):
                    try:
                        frappe.db.set_value("Account", target_name, "account_number", root_acc['account_number'])
                        print(f"✓ Updated root: {root_acc['account_number']} - {root_acc['account_name']}")
                        self.stats['updated'] += 1
                    except Exception as e:
                        print(f"✗ Error updating root {root_acc['account_name']}: {str(e)}")
                        self.stats['errors'] += 1
        
        frappe.db.commit()
        
        # Step 3: Create/update child accounts in hierarchical order
        print(f"\n{'='*80}")
        print("Step 2: Creating/updating child accounts")
        print(f"{'='*80}\n")
        
        child_accounts = [acc for acc in source_accounts if acc['parent_account']]
        for account in child_accounts:
            self.create_or_update_account(account, source_accounts)
        
        frappe.db.commit()
        
        # Step 4: Fix account names
        print(f"\n{'='*80}")
        print("Step 3: Fixing account names")
        print(f"{'='*80}\n")
        
        self.fix_account_names()
        frappe.db.commit()
        
        # Print summary
        print(f"\n{'='*80}")
        print("REPLICATION SUMMARY")
        print(f"{'='*80}")
        print(f"  Created:  {self.stats['created']} accounts")
        print(f"  Updated:  {self.stats['updated']} accounts")
        print(f"  Renamed:  {self.stats['renamed']} accounts")
        print(f"  Skipped:  {self.stats['skipped']} accounts")
        print(f"  Errors:   {self.stats['errors']} accounts")
        print(f"{'='*80}\n")
        
        return self.stats


def replicate_coa_from_jaipur_to_kota():
    """
    Main function to replicate COA from hkmjerp.in to erp.hkmkota.org
    
    This should be run on erp.hkmkota.org site:
        bench --site erp.hkmkota.org console
        >>> from hkm.cursor.cross_site_coa_replication import replicate_coa_from_jaipur_to_kota
        >>> replicate_coa_from_jaipur_to_kota()
    """
    
    # Configuration
    SOURCE_SITE = "hkmjerp_in"  # Database name for hkmjerp.in
    SOURCE_COMPANY = "Sri Radha Krishna Mandir Foundation"
    TARGET_COMPANY = "Radha Krishna Mandir Foundation Kota"
    
    # Verify target company exists
    if not frappe.db.exists("Company", TARGET_COMPANY):
        print(f"✗ Error: Target company '{TARGET_COMPANY}' not found on current site")
        print("\nAvailable companies:")
        companies = frappe.get_all("Company", fields=["name"])
        for company in companies:
            print(f"  - {company['name']}")
        return None
    
    # Create replicator and run
    replicator = CrossSiteCOAReplicator(
        source_site=SOURCE_SITE,
        source_company=SOURCE_COMPANY,
        target_company=TARGET_COMPANY
    )
    
    return replicator.replicate()


def export_coa_structure_to_json(company: str, output_file: str = None):
    """
    Export COA structure to JSON file for manual inspection or transfer
    
    Args:
        company: Company name to export
        output_file: Output file path (optional)
    
    Usage:
        bench --site hkmjerp.in console
        >>> from hkm.cursor.cross_site_coa_replication import export_coa_structure_to_json
        >>> export_coa_structure_to_json("Sri Radha Krishna Mandir Foundation", "/tmp/coa_structure.json")
    """
    
    accounts = frappe.get_all(
        "Account",
        filters={"company": company},
        fields=[
            "name", "account_name", "account_number", "parent_account",
            "is_group", "root_type", "report_type", "account_type",
            "account_currency", "lft", "rgt"
        ],
        order_by="lft ASC"
    )
    
    if not output_file:
        output_file = f"/tmp/coa_{company.replace(' ', '_').lower()}.json"
    
    with open(output_file, 'w') as f:
        json.dump(accounts, f, indent=2, default=str)
    
    print(f"✓ Exported {len(accounts)} accounts to {output_file}")
    return output_file


def import_coa_structure_from_json(json_file: str, target_company: str):
    """
    Import COA structure from JSON file
    
    Args:
        json_file: Path to JSON file with COA structure
        target_company: Target company name
    
    Usage:
        bench --site erp.hkmkota.org console
        >>> from hkm.cursor.cross_site_coa_replication import import_coa_structure_from_json
        >>> import_coa_structure_from_json("/tmp/coa_structure.json", "Radha Krishna Mandir Foundation Kota")
    """
    
    print(f"\n{'='*80}")
    print(f"Importing COA structure from {json_file}")
    print(f"Target company: {target_company}")
    print(f"{'='*80}\n")
    
    # Load JSON
    with open(json_file, 'r') as f:
        source_accounts = json.load(f)
    
    print(f"Loaded {len(source_accounts)} accounts from JSON\n")
    
    # Get target company abbr
    target_abbr = frappe.get_cached_value("Company", target_company, "abbr")
    
    stats = {"created": 0, "updated": 0, "renamed": 0, "skipped": 0, "errors": 0}
    
    # Update root accounts
    print("Step 1: Updating root accounts\n")
    for acc in source_accounts:
        if not acc['parent_account'] and acc['account_number']:
            target_name = f"{acc['account_name']} - {target_abbr}"
            if frappe.db.exists("Account", target_name):
                try:
                    frappe.db.set_value("Account", target_name, "account_number", acc['account_number'])
                    print(f"✓ Updated root: {acc['account_number']} - {acc['account_name']}")
                    stats['updated'] += 1
                except Exception as e:
                    print(f"✗ Error: {str(e)}")
                    stats['errors'] += 1
    
    frappe.db.commit()
    
    # Create/update child accounts
    print("\nStep 2: Creating/updating child accounts\n")
    
    # Build parent lookup
    parent_map = {}
    for acc in source_accounts:
        if acc['account_number']:
            parent_map[acc['name']] = f"{acc['account_number']} - {acc['account_name']} - {target_abbr}"
        else:
            parent_map[acc['name']] = f"{acc['account_name']} - {target_abbr}"
    
    for acc in source_accounts:
        if not acc['parent_account']:
            continue
        
        # Get target parent
        source_parent_name = acc['parent_account']
        if source_parent_name not in parent_map:
            print(f"⚠ Parent not found for {acc['account_name']}")
            stats['skipped'] += 1
            continue
        
        target_parent = parent_map[source_parent_name]
        
        # Check if parent exists
        if not frappe.db.exists("Account", target_parent):
            # Try without number
            source_parent_info = next((a for a in source_accounts if a['name'] == source_parent_name), None)
            if source_parent_info:
                target_parent = f"{source_parent_info['account_name']} - {target_abbr}"
                if not frappe.db.exists("Account", target_parent):
                    print(f"⚠ Parent {target_parent} not found for {acc['account_name']}")
                    stats['skipped'] += 1
                    continue
        
        # Check if account exists
        existing = frappe.db.get_value(
            "Account",
            {
                "account_name": acc['account_name'],
                "company": target_company,
                "parent_account": target_parent
            },
            ["name", "account_number"],
            as_dict=True
        )
        
        if existing:
            if existing.account_number != acc['account_number']:
                try:
                    frappe.db.set_value("Account", existing.name, "account_number", acc['account_number'])
                    print(f"✓ Updated: {acc['account_number']} - {acc['account_name']}")
                    stats['updated'] += 1
                except Exception as e:
                    print(f"✗ Error: {str(e)}")
                    stats['errors'] += 1
            else:
                print(f"○ Exists: {acc['account_number']} - {acc['account_name']}")
        else:
            try:
                parent_doc = frappe.get_doc("Account", target_parent)
                
                account_doc = frappe.new_doc("Account")
                account_doc.account_name = acc['account_name']
                account_doc.company = target_company
                account_doc.parent_account = target_parent
                account_doc.is_group = acc['is_group']
                account_doc.account_number = acc['account_number']
                account_doc.root_type = parent_doc.root_type
                account_doc.report_type = parent_doc.report_type
                account_doc.account_currency = parent_doc.account_currency
                
                if acc.get('account_type'):
                    account_doc.account_type = acc['account_type']
                
                account_doc.flags.ignore_permissions = True
                account_doc.insert()
                
                print(f"✓ Created: {acc['account_number']} - {acc['account_name']}")
                stats['created'] += 1
                
            except Exception as e:
                print(f"✗ Error creating {acc['account_name']}: {str(e)}")
                stats['errors'] += 1
    
    frappe.db.commit()
    
    # Fix account names
    print("\nStep 3: Fixing account names\n")
    
    accounts = frappe.get_all(
        "Account",
        filters={
            "company": target_company,
            "account_number": ["!=", ""]
        },
        fields=["name", "account_name", "account_number", "parent_account"]
    )
    
    for account in accounts:
        expected_name = f"{account['account_number']} - {account['account_name']} - {target_abbr}"
        
        if account['name'] != expected_name and account['parent_account']:
            try:
                old_flag = frappe.in_test
                frappe.in_test = True
                
                try:
                    if not frappe.db.exists("Account", expected_name):
                        frappe.rename_doc("Account", account['name'], expected_name, force=True)
                        print(f"✓ Renamed: {account['name']} -> {expected_name}")
                        stats['renamed'] += 1
                finally:
                    frappe.in_test = old_flag
                    
            except Exception as e:
                print(f"✗ Error renaming: {str(e)}")
                stats['errors'] += 1
    
    frappe.db.commit()
    
    print(f"\n{'='*80}")
    print("IMPORT SUMMARY")
    print(f"{'='*80}")
    print(f"  Created:  {stats['created']} accounts")
    print(f"  Updated:  {stats['updated']} accounts")
    print(f"  Renamed:  {stats['renamed']} accounts")
    print(f"  Skipped:  {stats['skipped']} accounts")
    print(f"  Errors:   {stats['errors']} accounts")
    print(f"{'='*80}\n")
    
    return stats
