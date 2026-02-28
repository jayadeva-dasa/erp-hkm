"""
Analyze tax distribution issues across all companies
Find invoices where taxes are at invoice-level but not distributed to items
"""

import frappe
from frappe.utils import flt
from collections import defaultdict

def analyze_all_companies(from_date='2025-04-01', to_date='2026-03-31', print_summary=True):
    """
    Analyze tax distribution issues across all companies in the system
    
    Args:
        from_date: Start date for analysis (default: FY 2025-26 start)
        to_date: End date for analysis (default: FY 2025-26 end)
        print_summary: Print detailed summary
    
    Returns:
        dict with company-wise analysis
    """
    
    if print_summary:
        print("\n" + "="*100)
        print("TAX DISTRIBUTION ISSUE ANALYSIS - ALL COMPANIES")
        print("="*100)
        print(f"Period: {from_date} to {to_date}")
        print("="*100)
    
    # Get all companies
    companies = frappe.get_all('Company', pluck='name', order_by='name')
    
    if print_summary:
        print(f"\nAnalyzing {len(companies)} companies...")
    
    results = {}
    total_affected_invoices = 0
    total_affected_companies = 0
    total_tax_amount = 0
    
    for company in companies:
        company_result = analyze_company(company, from_date, to_date, print_summary=False)
        
        if company_result['affected_invoice_count'] > 0:
            results[company] = company_result
            total_affected_invoices += company_result['affected_invoice_count']
            total_affected_companies += 1
            total_tax_amount += company_result['total_tax_amount']
            
            if print_summary:
                print(f"\n⚠️  {company}")
                print(f"    Affected Invoices: {company_result['affected_invoice_count']}")
                print(f"    Total Tax Amount: ₹{company_result['total_tax_amount']:,.2f}")
                print(f"    Date Range: {company_result['first_date']} to {company_result['last_date']}")
    
    if print_summary:
        print("\n" + "="*100)
        print("SUMMARY")
        print("="*100)
        print(f"Total Companies Analyzed: {len(companies)}")
        print(f"Companies with Issues: {total_affected_companies}")
        print(f"Total Affected Invoices: {total_affected_invoices}")
        print(f"Total Tax Amount Not Distributed: ₹{total_tax_amount:,.2f}")
        
        if total_affected_companies == 0:
            print("\n✅ No issues found in any company!")
        else:
            print(f"\n⚠️  {total_affected_companies} companies have tax distribution issues")
        
        print("="*100 + "\n")
    
    return {
        'companies_analyzed': len(companies),
        'companies_with_issues': total_affected_companies,
        'total_affected_invoices': total_affected_invoices,
        'total_tax_amount': total_tax_amount,
        'company_details': results
    }


def analyze_company(company, from_date='2025-04-01', to_date='2026-03-31', print_summary=True):
    """
    Analyze tax distribution issues for a single company
    
    Args:
        company: Company name
        from_date: Start date
        to_date: End date
        print_summary: Print detailed output
    
    Returns:
        dict with analysis results
    """
    
    # Query to find affected invoices
    query = """
        SELECT 
            si.name as invoice_name,
            si.posting_date,
            si.grand_total,
            si.total,
            (si.grand_total - si.total) as invoice_tax_amount,
            COUNT(si_item.name) as item_count,
            SUM(si_item.taxable_value) as total_taxable_value,
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
        HAVING invoice_tax_amount > 0.01 
            AND (total_item_tax = 0 OR total_item_tax IS NULL OR total_item_tax < 0.01)
        ORDER BY si.posting_date DESC, si.name
    """
    
    results = frappe.db.sql(query, (company, from_date, to_date), as_dict=1)
    
    if not results:
        return {
            'company': company,
            'affected_invoice_count': 0,
            'total_tax_amount': 0,
            'invoices': []
        }
    
    # Analyze results
    total_tax = sum(flt(r.invoice_tax_amount) for r in results)
    first_date = min(r.posting_date for r in results)
    last_date = max(r.posting_date for r in results)
    
    # Month-wise breakdown
    month_wise = defaultdict(lambda: {'count': 0, 'tax_amount': 0})
    for r in results:
        month_key = r.posting_date.strftime('%Y-%m')
        month_wise[month_key]['count'] += 1
        month_wise[month_key]['tax_amount'] += flt(r.invoice_tax_amount)
    
    if print_summary:
        print("\n" + "="*100)
        print(f"TAX DISTRIBUTION ANALYSIS: {company}")
        print("="*100)
        print(f"Period: {from_date} to {to_date}")
        print(f"\n📊 SUMMARY")
        print(f"   Affected Invoices: {len(results)}")
        print(f"   Total Tax Amount Not Distributed: ₹{total_tax:,.2f}")
        print(f"   Date Range: {first_date} to {last_date}")
        
        print(f"\n📅 MONTH-WISE BREAKDOWN")
        for month in sorted(month_wise.keys()):
            data = month_wise[month]
            print(f"   {month}: {data['count']} invoices, ₹{data['tax_amount']:,.2f} tax")
        
        print(f"\n📋 TOP 10 AFFECTED INVOICES")
        for i, inv in enumerate(sorted(results, key=lambda x: x.invoice_tax_amount, reverse=True)[:10], 1):
            print(f"   {i:2d}. {inv.invoice_name}: Grand Total ₹{inv.grand_total:,.2f}, Tax ₹{inv.invoice_tax_amount:,.2f}")
        
        print("="*100)
    
    return {
        'company': company,
        'affected_invoice_count': len(results),
        'total_tax_amount': total_tax,
        'first_date': str(first_date),
        'last_date': str(last_date),
        'month_wise': dict(month_wise),
        'invoices': [r.invoice_name for r in results]
    }


def get_affected_invoice_list(company, from_date='2025-04-01', to_date='2026-03-31'):
    """
    Get list of affected invoice names for a company
    """
    
    query = """
        SELECT 
            si.name
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
        HAVING (si.grand_total - si.total) > 0.01 
            AND (SUM(si_item.cgst_amount + si_item.sgst_amount + si_item.igst_amount) = 0 
                 OR SUM(si_item.cgst_amount + si_item.sgst_amount + si_item.igst_amount) IS NULL
                 OR SUM(si_item.cgst_amount + si_item.sgst_amount + si_item.igst_amount) < 0.01)
        ORDER BY si.posting_date DESC, si.name
    """
    
    return frappe.db.sql_list(query, (company, from_date, to_date))


def generate_fix_commands(summary_results):
    """
    Generate fix commands for all affected companies
    """
    
    print("\n" + "="*100)
    print("FIX COMMANDS")
    print("="*100)
    
    if not summary_results['company_details']:
        print("\n✅ No companies need fixing!")
        return
    
    print("\nTo fix all affected companies, run these commands:\n")
    
    for company, data in summary_results['company_details'].items():
        invoice_count = data['affected_invoice_count']
        tax_amount = data['total_tax_amount']
        
        print(f"\n# {company} ({invoice_count} invoices, ₹{tax_amount:,.2f})")
        print(f"# Copy the invoice list and create a fix function")
        print(f"invoices = {data['invoices'][:5]}  # ... ({invoice_count} total)")
        print()
    
    print("\nAlternatively, use the universal fix function:")
    print("="*100)
    print("""
def fix_company_invoices(company, from_date='2025-04-01', to_date='2026-03-31', commit=False):
    from hkm.cursor.fix_item_tax_distribution import fix_multiple_invoices
    from hkm.cursor.analyze_tax_distribution_all_companies import get_affected_invoice_list
    
    invoice_list = get_affected_invoice_list(company, from_date, to_date)
    
    if not invoice_list:
        print(f"No affected invoices found for {company}")
        return
    
    print(f"\\nFixing {len(invoice_list)} invoices for {company}...")
    return fix_multiple_invoices(invoice_list, commit=commit)

# Usage:
# bench --site sitename execute fix_company_invoices --kwargs "{'company': 'Company Name', 'commit': True}"
""")
    print("="*100)


def export_to_excel(summary_results, filename='tax_distribution_analysis.xlsx'):
    """
    Export analysis results to Excel
    """
    try:
        import pandas as pd
        from datetime import datetime
        
        # Company summary
        company_data = []
        for company, data in summary_results['company_details'].items():
            company_data.append({
                'Company': company,
                'Affected Invoices': data['affected_invoice_count'],
                'Total Tax Amount': data['total_tax_amount'],
                'First Date': data['first_date'],
                'Last Date': data['last_date']
            })
        
        df_companies = pd.DataFrame(company_data)
        
        # Overall summary
        summary_data = [{
            'Total Companies Analyzed': summary_results['companies_analyzed'],
            'Companies with Issues': summary_results['companies_with_issues'],
            'Total Affected Invoices': summary_results['total_affected_invoices'],
            'Total Tax Amount': summary_results['total_tax_amount']
        }]
        df_summary = pd.DataFrame(summary_data)
        
        # Write to Excel
        filepath = f"/tmp/{filename}"
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df_summary.to_excel(writer, sheet_name='Summary', index=False)
            df_companies.to_excel(writer, sheet_name='Company Details', index=False)
            
            # Invoice details per company
            for company, data in summary_results['company_details'].items():
                if len(data['invoices']) > 0:
                    df_invoices = pd.DataFrame({
                        'Invoice': data['invoices']
                    })
                    sheet_name = company[:31]  # Excel sheet name limit
                    df_invoices.to_excel(writer, sheet_name=sheet_name, index=False)
        
        print(f"\n✅ Analysis exported to: {filepath}")
        return filepath
        
    except ImportError:
        print("\n⚠️  pandas not available. Install with: pip install pandas openpyxl")
        return None


if __name__ == "__main__":
    # Run analysis for all companies
    summary = analyze_all_companies(
        from_date='2025-04-01',
        to_date='2026-03-31',
        print_summary=True
    )
    
    # Generate fix commands
    if summary['companies_with_issues'] > 0:
        generate_fix_commands(summary)
        
        # Try to export to Excel
        # export_to_excel(summary)
