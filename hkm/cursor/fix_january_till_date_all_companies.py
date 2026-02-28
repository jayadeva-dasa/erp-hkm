"""
Fix tax distribution issues from January 2026 till date across all companies
"""

import frappe
from collections import defaultdict
from hkm.cursor.fix_item_tax_distribution import fix_multiple_invoices
from hkm.cursor.update_item_wise_tax_detail import update_multiple_invoices

def fix_january_till_date_all_companies(commit=False):
    """
    Fix all tax distribution issues from January 2026 till date across all companies
    
    Args:
        commit: If True, commits changes to database
    
    Returns:
        Summary of fixes
    """
    
    from_date = '2026-01-01'
    to_date = '2026-02-10'  # Today's date
    
    print("\n" + "="*100)
    print("FIX TAX DISTRIBUTION - JANUARY 2026 TILL DATE - ALL COMPANIES")
    print("="*100)
    print(f"Period: {from_date} to {to_date}")
    print(f"Commit Mode: {'ENABLED - Changes will be saved' if commit else 'DISABLED - Dry run only'}")
    print("="*100)
    
    # Get affected companies and invoices
    companies_data = get_period_affected_invoices(from_date, to_date)
    
    if not companies_data:
        print("\n✅ No companies have tax distribution issues in this period!")
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
    print("FINAL SUMMARY - JANUARY 2026 TILL DATE")
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


def get_period_affected_invoices(from_date, to_date):
    """
    Get affected invoices for a date period by company
    """
    
    query = """
        SELECT 
            si.company,
            si.name as invoice_name,
            si.grand_total,
            si.total,
            si.is_return
        FROM 
            `tabSales Invoice` si
        INNER JOIN 
            `tabSales Invoice Item` si_item ON si.name = si_item.parent
        WHERE 
            si.docstatus = 1
            AND si.posting_date BETWEEN %s AND %s
            AND si.is_opening != 'Yes'
            AND (si.is_return IS NULL OR si.is_return = 0)
            AND si.grand_total > 0
        GROUP BY si.name, si.company, si.grand_total, si.total, si.is_return
        HAVING (si.grand_total - si.total) > 0.01 
            AND (SUM(si_item.cgst_amount + si_item.sgst_amount + si_item.igst_amount) = 0 
                 OR SUM(si_item.cgst_amount + si_item.sgst_amount + si_item.igst_amount) IS NULL
                 OR ABS(SUM(si_item.cgst_amount + si_item.sgst_amount + si_item.igst_amount)) < 0.01)
        ORDER BY si.company, si.posting_date, si.name
    """
    
    results = frappe.db.sql(query, (from_date, to_date), as_dict=1)
    
    # Group by company
    company_invoices = defaultdict(list)
    for row in results:
        company_invoices[row.company].append(row.invoice_name)
    
    return dict(company_invoices)


def analyze_january_till_date():
    """
    Analyze the tax distribution issue from January 2026 till date
    """
    from_date = '2026-01-01'
    to_date = '2026-02-10'
    
    query = """
        SELECT 
            si.company,
            si.name as invoice_name,
            si.grand_total,
            si.total,
            si.is_return
        FROM 
            `tabSales Invoice` si
        INNER JOIN 
            `tabSales Invoice Item` si_item ON si.name = si_item.parent
        WHERE 
            si.docstatus = 1
            AND si.posting_date BETWEEN %s AND %s
            AND si.is_opening != 'Yes'
            AND (si.is_return IS NULL OR si.is_return = 0)
            AND si.grand_total > 0
        GROUP BY si.name, si.company, si.grand_total, si.total, si.is_return
        HAVING (si.grand_total - si.total) > 0.01 
            AND (SUM(si_item.cgst_amount + si_item.sgst_amount + si_item.igst_amount) = 0 
                 OR SUM(si_item.cgst_amount + si_item.sgst_amount + si_item.igst_amount) IS NULL
                 OR ABS(SUM(si_item.cgst_amount + si_item.sgst_amount + si_item.igst_amount)) < 0.01)
        ORDER BY si.company, si.posting_date, si.name
    """
    
    # Get detailed results
    detailed_results = frappe.db.sql(query, (from_date, to_date), as_dict=1)
    
    # Group by company
    company_summary = defaultdict(lambda: {'count': 0, 'tax_amount': 0, 'invoices': []})
    
    for row in detailed_results:
        company = row['company']
        company_summary[company]['count'] += 1
        company_summary[company]['tax_amount'] += (row.get('grand_total', 0) - row.get('total', 0))
        company_summary[company]['invoices'].append(row['invoice_name'])
    
    print("\n" + "="*100)
    print(f"TAX DISTRIBUTION ANALYSIS - JANUARY 2026 TILL DATE - ALL COMPANIES")
    print("="*100)
    print(f"Period: {from_date} to {to_date}\n")
    
    if not company_summary:
        print("✅ No issues found!\n")
        return
    
    for company, data in sorted(company_summary.items()):
        print(f"⚠️  {company}")
        print(f"    Invoices: {data['count']}")
        print(f"    Tax Amount: ₹{data['tax_amount']:,.2f}")
        
        # Show first 5 invoice IDs
        invoice_ids = data['invoices'][:5]
        print(f"    Invoice IDs: {', '.join(invoice_ids)}")
        if data['count'] > 5:
            print(f"                 ... and {data['count'] - 5} more\n")
        else:
            print()
    
    print("="*100)
    print("PERIOD SUMMARY")
    print("="*100)
    total_count = sum(d['count'] for d in company_summary.values())
    total_tax = sum(d['tax_amount'] for d in company_summary.values())
    
    print(f"Companies with Issues: {len(company_summary)}")
    print(f"Total Affected Invoices: {total_count}")
    print(f"Total Tax Amount Not Distributed: ₹{total_tax:,.2f}")
    print("="*100 + "\n")


if __name__ == "__main__":
    # Show what needs fixing
    print("\nAnalyzing January 2026 till date...")
    analyze_january_till_date()
    
    print("\n" + "="*100)
    print("TO FIX INVOICES FROM JANUARY 2026 TILL DATE:")
    print("="*100)
    print("\n# Dry run first:")
    print('bench --site hkmerp.in execute hkm.cursor.fix_january_till_date_all_companies.fix_january_till_date_all_companies --kwargs "{\'commit\': False}"')
    print("\n# Apply fixes:")
    print('bench --site hkmerp.in execute hkm.cursor.fix_january_till_date_all_companies.fix_january_till_date_all_companies --kwargs "{\'commit\': True}"')
    print("="*100 + "\n")
