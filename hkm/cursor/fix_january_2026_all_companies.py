"""
Fix tax distribution issues specifically for January 2026 across all companies
"""

import frappe
from collections import defaultdict
from hkm.cursor.fix_item_tax_distribution import fix_multiple_invoices
from hkm.cursor.update_item_wise_tax_detail import update_multiple_invoices

def fix_january_2026_all_companies(commit=False):
    """
    Fix all tax distribution issues for January 2026 across all companies
    
    Args:
        commit: If True, commits changes to database
    
    Returns:
        Summary of fixes
    """
    
    from_date = '2026-01-01'
    to_date = '2026-01-31'
    
    print("\n" + "="*100)
    print("FIX TAX DISTRIBUTION - JANUARY 2026 - ALL COMPANIES")
    print("="*100)
    print(f"Period: {from_date} to {to_date}")
    print(f"Commit Mode: {'ENABLED - Changes will be saved' if commit else 'DISABLED - Dry run only'}")
    print("="*100)
    
    # Get affected companies and invoices
    companies_data = get_january_affected_invoices()
    
    if not companies_data:
        print("\n✅ No companies have tax distribution issues in January 2026!")
        return
    
    print(f"\nFound issues in {len(companies_data)} companies:")
    for company, data in companies_data.items():
        print(f"  - {company}: {len(data)} invoices")
    
    all_results = {}
    
    for company, invoice_list in companies_data.items():
        print("\n" + "="*100)
        print(f"FIXING: {company}")
        print("="*100)
        
        try:
            # Fix item-level taxes
            results = fix_multiple_invoices(invoice_list, commit=commit, print_details=True)
            
            # Update item_wise_tax_detail for successful fixes
            if commit and results['success']:
                print("\n" + "-"*100)
                print("Updating item_wise_tax_detail...")
                print("-"*100)
                
                success_invoices = [r['invoice'] for r in results['success']]
                update_results = update_multiple_invoices(success_invoices, commit=True)
                
                print(f"✅ Updated item_wise_tax_detail for {update_results['success']} invoices")
            
            all_results[company] = {
                'status': 'success',
                'results': results
            }
            
        except Exception as e:
            print(f"\n❌ Error fixing {company}: {str(e)}")
            all_results[company] = {
                'status': 'error',
                'error': str(e)
            }
    
    # Final summary
    print("\n" + "="*100)
    print("FINAL SUMMARY - JANUARY 2026")
    print("="*100)
    
    total_success = 0
    total_skipped = 0
    total_validation_failed = 0
    total_errors = 0
    
    for company, result in all_results.items():
        if result['status'] == 'success' and 'results' in result:
            r = result['results']
            total_success += len(r['success'])
            total_skipped += len(r['skipped'])
            total_validation_failed += len(r.get('validation_failed', []))
            total_errors += len(r['errors'])
            
            print(f"\n{company}:")
            print(f"  ✅ Fixed: {len(r['success'])}")
            print(f"  ⏭️  Skipped: {len(r['skipped'])}")
            if r.get('validation_failed'):
                print(f"  ⚠️  Validation Failed: {len(r['validation_failed'])}")
            if r['errors']:
                print(f"  ❌ Errors: {len(r['errors'])}")
    
    print("\n" + "="*100)
    print(f"TOTALS:")
    print(f"  ✅ Successfully Fixed: {total_success}")
    print(f"  ⏭️  Skipped: {total_skipped}")
    print(f"  ⚠️  Validation Failed: {total_validation_failed}")
    print(f"  ❌ Errors: {total_errors}")
    
    if commit:
        print("\n✅ ALL CHANGES COMMITTED TO DATABASE")
    else:
        print("\n⚠️  DRY RUN - No changes committed")
        print("    To apply fixes, run with commit=True")
    
    print("="*100 + "\n")
    
    return all_results


def get_january_affected_invoices():
    """
    Get affected invoices for January 2026 by company
    """
    
    from_date = '2026-01-01'
    to_date = '2026-01-31'
    
    query = """
        SELECT 
            si.company,
            si.name as invoice_name,
            si.grand_total,
            si.total
        FROM 
            `tabSales Invoice` si
        INNER JOIN 
            `tabSales Invoice Item` si_item ON si.name = si_item.parent
        WHERE 
            si.docstatus = 1
            AND si.posting_date BETWEEN %s AND %s
            AND si.is_opening != 'Yes'
        GROUP BY si.name, si.company, si.grand_total, si.total
        HAVING (si.grand_total - si.total) > 0.01 
            AND (SUM(si_item.cgst_amount + si_item.sgst_amount + si_item.igst_amount) = 0 
                 OR SUM(si_item.cgst_amount + si_item.sgst_amount + si_item.igst_amount) IS NULL
                 OR SUM(si_item.cgst_amount + si_item.sgst_amount + si_item.igst_amount) < 0.01)
        ORDER BY si.company, si.posting_date, si.name
    """
    
    results = frappe.db.sql(query, (from_date, to_date), as_dict=1)
    
    # Group by company
    company_invoices = defaultdict(list)
    for row in results:
        company_invoices[row.company].append(row.invoice_name)
    
    return dict(company_invoices)


if __name__ == "__main__":
    # Show what needs fixing
    print("\nAnalyzing January 2026...")
    affected = get_january_affected_invoices()
    
    if not affected:
        print("✅ No issues found in January 2026!")
    else:
        print(f"\nFound issues in {len(affected)} companies:")
        for company, invoices in affected.items():
            print(f"  - {company}: {len(invoices)} invoices")
        
        print("\n" + "="*100)
        print("TO FIX JANUARY 2026 INVOICES:")
        print("="*100)
        print("\n# Dry run first:")
        print('bench --site hkmerp.in execute hkm.cursor.fix_january_2026_all_companies.fix_january_2026_all_companies --kwargs "{\'commit\': False}"')
        print("\n# Apply fixes:")
        print('bench --site hkmerp.in execute hkm.cursor.fix_january_2026_all_companies.fix_january_2026_all_companies --kwargs "{\'commit\': True}"')
        print("="*100 + "\n")
