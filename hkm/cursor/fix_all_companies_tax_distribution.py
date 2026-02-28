"""
Universal fix for tax distribution issues across all companies
"""

import frappe
from hkm.cursor.fix_item_tax_distribution import fix_multiple_invoices

def get_affected_invoices_for_company(company, from_date='2025-04-01', to_date='2026-03-31'):
    """
    Get list of affected invoice names for a company
    """
    
    query = """
        SELECT 
            si.name,
            si.grand_total,
            si.total,
            SUM(si_item.cgst_amount + si_item.sgst_amount + si_item.igst_amount) as total_item_tax
        FROM 
            `tabSales Invoice` si
        INNER JOIN 
            `tabSales Invoice Item` si_item ON si.name = si_item.parent
        WHERE 
            si.company = %s
            AND si.docstatus = 1
            AND si.posting_date BETWEEN %s AND %s
            AND si.is_opening != 'Yes'
        GROUP BY si.name
        HAVING (grand_total - total) > 0.01 
            AND (total_item_tax = 0 OR total_item_tax IS NULL OR total_item_tax < 0.01)
        ORDER BY si.posting_date, si.name
    """
    
    results = frappe.db.sql(query, (company, from_date, to_date), as_dict=1)
    return [r.name for r in results]


def fix_company_invoices(company, from_date='2025-04-01', to_date='2026-03-31', commit=False):
    """
    Fix all affected invoices for a single company
    
    Args:
        company: Company name
        from_date: Start date
        to_date: End date
        commit: If True, commits changes
    
    Returns:
        dict with results
    """
    
    print("\n" + "="*100)
    print(f"FIXING TAX DISTRIBUTION - {company}")
    print("="*100)
    
    invoice_list = get_affected_invoices_for_company(company, from_date, to_date)
    
    if not invoice_list:
        print(f"\n✅ No affected invoices found for {company}")
        return {
            'company': company,
            'status': 'skip',
            'invoices_processed': 0
        }
    
    print(f"Found {len(invoice_list)} affected invoices")
    print(f"Period: {from_date} to {to_date}")
    print(f"Commit Mode: {'ENABLED' if commit else 'DISABLED (dry run)'}")
    print("="*100)
    
    # Fix invoices
    results = fix_multiple_invoices(invoice_list, commit=commit, print_details=True)
    
    # Update item_wise_tax_detail
    if commit and results['success']:
        print("\n" + "="*100)
        print("UPDATING ITEM_WISE_TAX_DETAIL")
        print("="*100)
        
        from hkm.cursor.update_item_wise_tax_detail import update_multiple_invoices
        
        success_invoices = [r['invoice'] for r in results['success']]
        update_results = update_multiple_invoices(success_invoices, commit=True)
        
        print(f"\n✅ Updated item_wise_tax_detail for {update_results['success']} invoices")
    
    return {
        'company': company,
        'status': 'success',
        'invoices_processed': len(invoice_list),
        'results': results
    }


def fix_all_companies(from_date='2025-04-01', to_date='2026-03-31', commit=False):
    """
    Fix tax distribution issues for all companies in the system
    
    Args:
        from_date: Start date for fix
        to_date: End date for fix
        commit: If True, commits changes
    
    Returns:
        Summary of all fixes
    """
    
    print("\n" + "="*100)
    print("UNIVERSAL TAX DISTRIBUTION FIX - ALL COMPANIES")
    print("="*100)
    print(f"Period: {from_date} to {to_date}")
    print(f"Commit Mode: {'ENABLED - Changes will be saved' if commit else 'DISABLED - Dry run only'}")
    print("="*100)
    
    # Run analysis first
    from hkm.cursor.analyze_tax_distribution_all_companies import analyze_all_companies
    
    print("\n📊 Running analysis...")
    analysis = analyze_all_companies(from_date, to_date, print_summary=False)
    
    if analysis['companies_with_issues'] == 0:
        print("\n✅ No companies have tax distribution issues!")
        return
    
    print(f"\nFound issues in {analysis['companies_with_issues']} companies:")
    for company in analysis['company_details'].keys():
        data = analysis['company_details'][company]
        print(f"  - {company}: {data['affected_invoice_count']} invoices, ₹{data['total_tax_amount']:,.2f}")
    
    # Ask for confirmation if not in commit mode
    if not commit:
        print("\n⚠️  DRY RUN MODE - No changes will be made")
        print("    Review the output and run with commit=True to apply fixes")
    
    print("\n" + "="*100)
    print("STARTING FIXES")
    print("="*100)
    
    all_results = {}
    
    for company in analysis['company_details'].keys():
        try:
            result = fix_company_invoices(company, from_date, to_date, commit=commit)
            all_results[company] = result
        except Exception as e:
            print(f"\n❌ Error fixing {company}: {str(e)}")
            all_results[company] = {
                'company': company,
                'status': 'error',
                'error': str(e)
            }
    
    # Final summary
    print("\n" + "="*100)
    print("FINAL SUMMARY - ALL COMPANIES")
    print("="*100)
    
    total_success = sum(
        r['results']['success'].__len__() 
        for r in all_results.values() 
        if r['status'] == 'success' and 'results' in r
    )
    
    total_errors = sum(
        r['results']['errors'].__len__() 
        for r in all_results.values() 
        if r['status'] == 'success' and 'results' in r
    )
    
    print(f"\nCompanies Processed: {len(all_results)}")
    print(f"Total Invoices Fixed: {total_success}")
    print(f"Total Errors: {total_errors}")
    
    for company, result in all_results.items():
        if result['status'] == 'success' and 'results' in result:
            r = result['results']
            print(f"\n  {company}:")
            print(f"    ✅ Success: {len(r['success'])}")
            print(f"    ⏭️  Skipped: {len(r['skipped'])}")
            if 'validation_failed' in r:
                print(f"    ⚠️  Validation Failed: {len(r['validation_failed'])}")
            print(f"    ❌ Errors: {len(r['errors'])}")
    
    print("\n" + "="*100)
    
    if commit:
        print("\n✅ ALL FIXES COMMITTED TO DATABASE")
    else:
        print("\n⚠️  DRY RUN COMPLETED - To apply fixes, run with commit=True")
    
    print("="*100 + "\n")
    
    return all_results


# Quick functions for individual companies
def fix_golden_lotus_foundation(commit=False):
    """Fix Golden Lotus Foundation invoices"""
    return fix_company_invoices("Golden Lotus Foundation", commit=commit)

def fix_hkma(commit=False):
    """Fix Hare Krishna Movement Ahmedabad invoices"""
    return fix_company_invoices("Hare Krishna Movement Ahmedabad", commit=commit)

def fix_tsf(commit=False):
    """Fix Touchstone Foundation Ahmedabad invoices"""
    return fix_company_invoices("Touchstone Foundation Ahmedabad", commit=commit)


if __name__ == "__main__":
    # Run analysis and show what needs fixing
    fix_all_companies(commit=False)
    
    print("\n" + "="*100)
    print("TO FIX ALL COMPANIES:")
    print("="*100)
    print('bench --site hkmerp.in execute hkm.cursor.fix_all_companies_tax_distribution.fix_all_companies --kwargs "{\'commit\': True}"')
    print("\n" + "="*100)
    print("TO FIX INDIVIDUAL COMPANIES:")
    print("="*100)
    print('# Golden Lotus Foundation:')
    print('bench --site hkmerp.in execute hkm.cursor.fix_all_companies_tax_distribution.fix_golden_lotus_foundation --kwargs "{\'commit\': True}"')
    print('\n# Hare Krishna Movement Ahmedabad:')
    print('bench --site hkmerp.in execute hkm.cursor.fix_all_companies_tax_distribution.fix_hkma --kwargs "{\'commit\': True}"')
    print('\n# Touchstone Foundation Ahmedabad:')
    print('bench --site hkmerp.in execute hkm.cursor.fix_all_companies_tax_distribution.fix_tsf --kwargs "{\'commit\': True}"')
    print("="*100 + "\n")
