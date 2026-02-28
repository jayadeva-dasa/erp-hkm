"""
Analyze tax distribution issues specifically for January 2026 across all companies
"""

import frappe
from frappe.utils import flt
from collections import defaultdict

def analyze_january_2026_all_companies():
    """
    Analyze tax distribution issues for January 2026 only
    """
    
    from_date = '2026-01-01'
    to_date = '2026-01-31'
    
    print("\n" + "="*100)
    print("TAX DISTRIBUTION ANALYSIS - JANUARY 2026 - ALL COMPANIES")
    print("="*100)
    
    # Get all companies
    companies = frappe.get_all('Company', pluck='name', order_by='name')
    
    results = {}
    total_affected_invoices = 0
    total_affected_companies = 0
    total_tax_amount = 0
    
    for company in companies:
        query = """
            SELECT 
                si.name as invoice_name,
                si.posting_date,
                si.grand_total,
                si.total,
                (si.grand_total - si.total) as invoice_tax_amount,
                COUNT(si_item.name) as item_count,
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
            ORDER BY si.posting_date, si.name
        """
        
        invoices = frappe.db.sql(query, (company, from_date, to_date), as_dict=1)
        
        if invoices:
            total_tax = sum(flt(r.invoice_tax_amount) for r in invoices)
            
            results[company] = {
                'invoice_count': len(invoices),
                'total_tax': total_tax,
                'invoices': [r.invoice_name for r in invoices]
            }
            
            total_affected_invoices += len(invoices)
            total_affected_companies += 1
            total_tax_amount += total_tax
            
            print(f"\n⚠️  {company}")
            print(f"    Invoices: {len(invoices)}")
            print(f"    Tax Amount: ₹{total_tax:,.2f}")
            print(f"    Invoice IDs: {', '.join([r.invoice_name for r in invoices[:5]])}")
            if len(invoices) > 5:
                print(f"                 ... and {len(invoices) - 5} more")
    
    print("\n" + "="*100)
    print("JANUARY 2026 SUMMARY")
    print("="*100)
    print(f"Companies Analyzed: {len(companies)}")
    print(f"Companies with Issues: {total_affected_companies}")
    print(f"Total Affected Invoices: {total_affected_invoices}")
    print(f"Total Tax Amount Not Distributed: ₹{total_tax_amount:,.2f}")
    print("="*100 + "\n")
    
    return results


def get_january_invoice_list_by_company():
    """
    Get company-wise invoice lists for January 2026
    """
    
    results = analyze_january_2026_all_companies()
    
    print("\n" + "="*100)
    print("INVOICE LISTS BY COMPANY - JANUARY 2026")
    print("="*100)
    
    for company, data in results.items():
        print(f"\n## {company} ({data['invoice_count']} invoices)")
        print(f"```python")
        print(f"{company.upper().replace(' ', '_')}_JAN_2026 = [")
        for inv in data['invoices']:
            print(f'    "{inv}",')
        print(f"]")
        print(f"```")
    
    return results


if __name__ == "__main__":
    get_january_invoice_list_by_company()
