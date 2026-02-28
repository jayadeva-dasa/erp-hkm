"""
Auto-assign Balance Sheet Accounts to Categories
Automatically maps existing Asset and Liability accounts to appropriate categories
"""

import frappe
from frappe import _

# Account mapping patterns
# These patterns will be used to match account names to categories
ACCOUNT_PATTERNS = {
    'Asset': {
        'Cash & Bank': [
            'cash', 'bank', 'petty cash', 'cash in hand', 'bank account',
            'current account', 'savings account', 'hdfc', 'sbi', 'icici',
            'axis', 'pnb', 'canara'
        ],
        'Accounts Receivable': [
            'receivable', 'debtors', 'sundry debtors', 'trade receivables',
            'bills receivable', 'outstanding receivables'
        ],
        'Loans/Advances': [
            'imprest', 'advance', 'loan', 'staff advance', 'employee advance',
            'advance to staff', 'advance to employee', 'loans and advances',
            'security deposit', 'deposit', 'refundable deposit'
        ],
        'Inventory': [
            'inventory', 'stock', 'stock in hand', 'raw material',
            'finished goods', 'work in progress', 'wip'
        ],
        'Fixed Assets': [
            'fixed asset', 'building', 'land', 'furniture', 'fixture',
            'vehicle', 'equipment', 'machinery', 'computer', 'laptop',
            'plant', 'property', 'office equipment', 'electrical installation',
            'accumulated depreciation', 'depreciation'
        ],
        'Investments': [
            'investment', 'fixed deposit', 'fd', 'mutual fund', 'shares',
            'securities', 'bonds', 'debentures', 'corpus fund'
        ],
        'Current Assets': [
            'prepaid', 'advance', 'advance tax', 'tds receivable',
            'gst input', 'input credit', 'short term', 'current'
        ],
        'Other Assets': [
            'other asset', 'miscellaneous asset', 'intangible',
            'goodwill', 'preliminary expenses', 'deferred'
        ]
    },
    'Liability': {
        'Accounts Payable': [
            'payable', 'creditors', 'sundry creditors', 'trade payables',
            'bills payable', 'outstanding payables', 'outstanding expenses'
        ],
        'Current Liabilities': [
            'current liabilit', 'provision', 'tds payable', 'gst payable',
            'professional tax', 'pf payable', 'esi payable', 'salary payable',
            'wages payable', 'outstanding', 'accrued'
        ],
        'Short-term Loans': [
            'short term loan', 'short-term loan', 'unsecured loan - short',
            'secured loan - short', 'overdraft', 'cash credit'
        ],
        'Long-term Loans': [
            'long term loan', 'long-term loan', 'term loan', 'secured loan',
            'unsecured loan', 'bank loan', 'vehicle loan', 'housing loan',
            'mortgage'
        ],
        'Long-term Liabilities': [
            'long term liabilit', 'long-term liabilit', 'deferred tax'
        ],
        'Other Liabilities': [
            'other liabilit', 'miscellaneous liabilit', 'suspense'
        ]
    }
}


def get_leaf_accounts(company, root_type):
    """
    Get all leaf accounts for a company and root type
    """
    accounts = frappe.db.sql("""
        SELECT 
            name,
            account_name,
            account_type,
            root_type,
            is_group
        FROM `tabAccount`
        WHERE company = %s
            AND root_type = %s
            AND is_group = 0
            AND disabled = 0
        ORDER BY name
    """, (company, root_type), as_dict=True)
    
    return accounts


def match_account_to_category(account_name, patterns):
    """
    Match an account name to a category based on patterns
    Returns category name or None
    """
    account_lower = account_name.lower()
    
    # Try to match with each category's patterns
    for category, keywords in patterns.items():
        for keyword in keywords:
            if keyword.lower() in account_lower:
                return category
    
    return None


def auto_assign_accounts(company, dry_run=False):
    """
    Automatically assign accounts to categories based on patterns
    
    Args:
        company: Company name
        dry_run: If True, only show what would be assigned without saving
    """
    results = {
        'Asset': {},
        'Liability': {}
    }
    
    for root_type in ['Asset', 'Liability']:
        print(f"\n{'='*70}")
        print(f"Processing {root_type} accounts for {company}")
        print(f"{'='*70}")
        
        # Get all leaf accounts
        accounts = get_leaf_accounts(company, root_type)
        print(f"Found {len(accounts)} {root_type} accounts")
        
        patterns = ACCOUNT_PATTERNS[root_type]
        results[root_type] = {
            'total_accounts': len(accounts),
            'assigned': 0,
            'unassigned': 0,
            'assignments': {}
        }
        
        for account in accounts:
            # Try to match account to a category
            category = match_account_to_category(account.account_name, patterns)
            
            if category:
                if category not in results[root_type]['assignments']:
                    results[root_type]['assignments'][category] = []
                
                results[root_type]['assignments'][category].append({
                    'account': account.name,
                    'account_name': account.account_name
                })
                results[root_type]['assigned'] += 1
                
                if not dry_run:
                    # Save the assignment
                    try:
                        # Check if category exists
                        cat_exists = frappe.db.exists(
                            'HKM Analysis Category',
                            {
                                'company': company,
                                'category_name': category,
                                'root_type': root_type
                            }
                        )
                        
                        if cat_exists:
                            # Get the category doc
                            cat_doc = frappe.get_doc('HKM Analysis Category', cat_exists)
                            
                            # Check if account already assigned
                            account_exists = False
                            for acc in cat_doc.accounts:
                                if acc.account == account.name:
                                    account_exists = True
                                    break
                            
                            if not account_exists:
                                # Add account with 100% portion
                                cat_doc.append('accounts', {
                                    'account': account.name,
                                    'portion': 100
                                })
                                cat_doc.save(ignore_permissions=True)
                                print(f"✅ {account.account_name} → {category}")
                            else:
                                print(f"ℹ️  {account.account_name} already in {category}")
                        else:
                            print(f"⚠️  Category '{category}' not found for {company}")
                    except Exception as e:
                        print(f"❌ Error assigning {account.account_name}: {str(e)}")
                else:
                    print(f"[DRY RUN] {account.account_name} → {category}")
            else:
                results[root_type]['unassigned'] += 1
                print(f"⚪ {account.account_name} - No category match")
        
        print(f"\n{root_type} Summary:")
        print(f"  Total: {results[root_type]['total_accounts']}")
        print(f"  Assigned: {results[root_type]['assigned']}")
        print(f"  Unassigned: {results[root_type]['unassigned']}")
    
    if not dry_run:
        frappe.db.commit()  # v16: REVIEW - check if needed
    
    return results


@frappe.whitelist()
def auto_assign_for_company(company, dry_run=False):
    """
    Whitelisted method to auto-assign accounts for a company
    """
    return auto_assign_accounts(company, dry_run=dry_run)


def execute():
    """
    Execute from bench console
    """
    company = 'Hare Krishna Movement Jaipur'
    
    print("\n" + "="*70)
    print("AUTO-ASSIGNING BALANCE SHEET ACCOUNTS TO CATEGORIES")
    print("="*70)
    
    # First do a dry run to show what will be assigned
    print("\n🔍 DRY RUN - Showing what will be assigned...")
    auto_assign_accounts(company, dry_run=True)
    
    print("\n" + "="*70)
    print("📝 ACTUAL ASSIGNMENT - Saving to database...")
    print("="*70)
    
    # Now do the actual assignment
    results = auto_assign_accounts(company, dry_run=False)
    
    print("\n" + "="*70)
    print("✅ AUTO-ASSIGNMENT COMPLETED!")
    print("="*70)
    
    return results


if __name__ == '__main__':
    execute()

