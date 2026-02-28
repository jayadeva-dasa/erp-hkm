"""
Assign All Imprest and Security Deposit Accounts to Loans/Advances Category
Creates the category if it doesn't exist and assigns all imprest and security deposit accounts to it
"""

import frappe
from frappe import _


def assign_imprest_accounts_to_loans_advances(company):
    """
    Create Loans/Advances category and assign all imprest and security deposit accounts to it
    
    Args:
        company: Company name
    """
    
    print(f"\n{'='*60}")
    print(f"Assigning Imprest & Security Deposit Accounts to Loans/Advances")
    print(f"Company: {company}")
    print(f"{'='*60}\n")
    
    # Step 1: Create or get Loans/Advances category
    category_name = "Loans/Advances"
    root_type = "Asset"
    
    # Check if category name exists
    category_name_doc = frappe.db.exists(
        "HKM Analysis Category Name",
        {"category_name": category_name, "root_type": root_type}
    )
    
    if not category_name_doc:
        print(f"Creating category name: {category_name}")
        category_name_doc = frappe.get_doc({
            "doctype": "HKM Analysis Category Name",
            "category_name": category_name,
            "root_type": root_type,
            "description": "Loans given and advances (including imprest accounts and security deposits)"
        })
        category_name_doc.insert()
        frappe.db.commit()  # v16: REVIEW - check if needed
        print(f"✓ Created category name: {category_name}")
    else:
        print(f"✓ Category name already exists: {category_name}")
    
    # Step 2: Get all imprest and security deposit accounts for the company
    target_accounts = frappe.db.sql("""
        SELECT 
            name,
            account_name,
            account_type,
            root_type
        FROM `tabAccount`
        WHERE company = %(company)s
            AND root_type = 'Asset'
            AND (
                LOWER(account_name) LIKE '%%imprest%%'
                OR LOWER(name) LIKE '%%imprest%%'
                OR LOWER(account_name) LIKE '%%security deposit%%'
                OR LOWER(name) LIKE '%%security deposit%%'
                OR LOWER(account_name) LIKE '%%advance%%'
                OR LOWER(name) LIKE '%%advance%%'
            )
            AND is_group = 0
            AND disabled = 0
        ORDER BY name
    """, {"company": company}, as_dict=True)
    
    if not target_accounts:
        print(f"\n⚠️  No imprest/security deposit/advance accounts found for {company}")
        return
    
    print(f"\nFound {len(target_accounts)} account(s):")
    for acc in target_accounts:
        print(f"  - {acc.name} ({acc.account_name})")
    
    # Step 3: Remove these accounts from other categories first
    print(f"\nRemoving accounts from other categories...")
    target_account_names = [acc.name for acc in target_accounts]
    
    # Get all categories for this company (Asset type)
    all_categories = frappe.get_all(
        "HKM Analysis Category",
        filters={"company": company, "root_type": "Asset"},
        pluck="name"
    )
    
    removed_count = 0
    for cat_name in all_categories:
        cat = frappe.get_doc("HKM Analysis Category", cat_name)
        original_count = len(cat.accounts)
        
        # Remove target accounts from this category
        cat.accounts = [
            acc for acc in cat.accounts 
            if acc.account not in target_account_names
        ]
        
        if len(cat.accounts) < original_count:
            removed = original_count - len(cat.accounts)
            removed_count += removed
            print(f"  Removed {removed} account(s) from '{cat.category_name}'")
            cat.save()
    
    if removed_count > 0:
        frappe.db.commit()  # v16: REVIEW - check if needed
        print(f"  ✓ Total removed from other categories: {removed_count}")
    else:
        print(f"  ✓ No accounts found in other categories")
    
    # Step 4: Create or update HKM Analysis Category for Loans/Advances
    category_doc = frappe.db.exists(
        "HKM Analysis Category",
        {"company": company, "category_name": category_name}
    )
    
    if category_doc:
        print(f"\nUpdating existing '{category_name}' category for {company}...")
        category = frappe.get_doc("HKM Analysis Category", category_doc)
    else:
        print(f"\nCreating new '{category_name}' category for {company}...")
        category = frappe.get_doc({
            "doctype": "HKM Analysis Category",
            "company": company,
            "category_name": category_name,
            "root_type": root_type
        })
    
    # Step 5: Assign all accounts to this category
    # Clear existing accounts first
    category.accounts = []
    
    # Add all accounts with 100% allocation
    for acc in target_accounts:
        category.append("accounts", {
            "account": acc.name,
            "percentage": 100
        })
        print(f"  ✓ Added: {acc.name} (100%)")
    
    # Save the category
    if category_doc:
        category.save()
    else:
        category.insert()
    
    frappe.db.commit()  # v16: REVIEW - check if needed
    
    print(f"\n{'='*60}")
    print(f"✅ SUCCESS!")
    print(f"{'='*60}")
    print(f"Category: {category_name}")
    print(f"Company: {company}")
    print(f"Accounts Assigned: {len(target_accounts)}")
    print(f"{'='*60}\n")
    
    return {
        "success": True,
        "category": category_name,
        "company": company,
        "accounts_assigned": len(target_accounts),
        "accounts": [acc.name for acc in target_accounts]
    }


def assign_imprest_for_all_companies():
    """
    Assign imprest accounts to Loan/Advances category for all companies
    """
    companies = frappe.get_all("Company", pluck="name")
    
    print(f"\n{'='*60}")
    print(f"Processing {len(companies)} companies")
    print(f"{'='*60}\n")
    
    results = []
    for company in companies:
        try:
            result = assign_imprest_accounts_to_loans_advances(company)
            results.append(result)
        except Exception as e:
            print(f"\n❌ Error processing {company}: {str(e)}")
            results.append({
                "success": False,
                "company": company,
                "error": str(e)
            })
    
    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    successful = [r for r in results if r and r.get("success")]
    failed = [r for r in results if r and not r.get("success")]
    
    print(f"Total Companies: {len(companies)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    
    if successful:
        total_accounts = sum(r.get("accounts_assigned", 0) for r in successful)
        print(f"Total Imprest Accounts Assigned: {total_accounts}")
    
    if failed:
        print(f"\nFailed Companies:")
        for r in failed:
            print(f"  - {r.get('company')}: {r.get('error')}")
    
    print(f"{'='*60}\n")
    
    return results


# For bench execute
def run_for_company(company_name):
    """
    Wrapper function for bench execute
    Usage: bench execute hkm_jaipur.api.category_analytics.assign_imprest_to_loans_advances.run_for_company --args "['Company Name']"
    """
    return assign_imprest_accounts_to_loans_advances(company_name)


def run_for_all_companies():
    """
    Wrapper function for bench execute
    Usage: bench execute hkm_jaipur.api.category_analytics.assign_imprest_to_loans_advances.run_for_all_companies
    """
    return assign_imprest_for_all_companies()

