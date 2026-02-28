"""
Analyze and fix missing taxable values across all invoices in January till date
"""

import frappe

def analyze_missing_taxable_values_all():
    """
    Find all invoices with items where amount > 0 but taxable_value = 0
    """
    
    from_date = '2026-01-01'
    to_date = '2026-02-10'
    
    query = """
        SELECT 
            si.name as invoice_name,
            si.company,
            si_item.name as item_row_name,
            si_item.item_code,
            si_item.amount,
            si_item.taxable_value,
            si_item.cgst_amount,
            si_item.sgst_amount,
            si_item.igst_amount
        FROM 
            `tabSales Invoice` si
        INNER JOIN 
            `tabSales Invoice Item` si_item ON si.name = si_item.parent
        WHERE 
            si.docstatus = 1
            AND si.posting_date BETWEEN %s AND %s
            AND (si.is_return IS NULL OR si.is_return = 0)
            AND si_item.amount > 0
            AND (si_item.taxable_value IS NULL OR si_item.taxable_value = 0)
        ORDER BY si.company, si.name, si_item.idx
    """
    
    results = frappe.db.sql(query, (from_date, to_date), as_dict=1)
    
    print("\n" + "="*100)
    print("MISSING TAXABLE VALUES ANALYSIS - JANUARY 2026 TILL DATE")
    print("="*100)
    print(f"Period: {from_date} to {to_date}\n")
    
    if not results:
        print("✅ No missing taxable values found!\n")
        return []
    
    # Group by company and invoice
    from collections import defaultdict
    company_data = defaultdict(lambda: defaultdict(list))
    
    for row in results:
        company_data[row['company']][row['invoice_name']].append(row)
    
    total_items = 0
    total_amount = 0
    
    for company, invoices in sorted(company_data.items()):
        print(f"⚠️  {company}")
        print(f"   Invoices with missing taxable values: {len(invoices)}")
        
        company_items = 0
        company_amount = 0
        
        for inv_name, items in list(invoices.items())[:3]:  # Show first 3 invoices
            print(f"   - {inv_name}: {len(items)} items")
            company_items += len(items)
            company_amount += sum(item['amount'] for item in items)
        
        if len(invoices) > 3:
            remaining_invoices = list(invoices.items())[3:]
            remaining_items = sum(len(items) for _, items in remaining_invoices)
            remaining_amount = sum(sum(item['amount'] for item in items) for _, items in remaining_invoices)
            company_items += remaining_items
            company_amount += remaining_amount
            print(f"   ... and {len(remaining_invoices)} more invoices")
        
        print(f"   Total Items: {company_items}, Total Amount: ₹{company_amount:,.2f}\n")
        total_items += company_items
        total_amount += company_amount
    
    print("="*100)
    print("SUMMARY")
    print("="*100)
    print(f"Companies Affected: {len(company_data)}")
    print(f"Total Invoices: {sum(len(invs) for invs in company_data.values())}")
    print(f"Total Items: {total_items}")
    print(f"Total Amount Missing: ₹{total_amount:,.2f}")
    print("="*100 + "\n")
    
    # Return unique invoice list
    unique_invoices = set()
    for invoices in company_data.values():
        unique_invoices.update(invoices.keys())
    
    return sorted(unique_invoices)


def fix_all_missing_taxable_values(commit=False):
    """
    Fix all invoices with missing taxable values
    """
    
    print("\n" + "="*100)
    print("FIXING ALL MISSING TAXABLE VALUES")
    print("="*100)
    
    # Get all affected invoices
    invoices = analyze_missing_taxable_values_all()
    
    if not invoices:
        print("Nothing to fix!")
        return
    
    print(f"\nFound {len(invoices)} invoices to fix")
    print(f"Commit Mode: {'ENABLED' if commit else 'DISABLED (dry run)'}")
    print("="*100 + "\n")
    
    from hkm.cursor.fix_missing_taxable_values import fix_multiple_invoices
    
    # Process in batches
    batch_size = 50
    total_fixed = 0
    
    for i in range(0, len(invoices), batch_size):
        batch = invoices[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1} ({len(batch)} invoices)...")
        
        result = fix_multiple_invoices(batch, commit=commit)
        total_fixed += result['total_items_fixed']
        
        print(f"Batch {i//batch_size + 1} complete: {result['total_items_fixed']} items fixed\n")
    
    print("="*100)
    print("FINAL SUMMARY")
    print("="*100)
    print(f"Total Invoices: {len(invoices)}")
    print(f"Total Items Fixed: {total_fixed}")
    
    if commit:
        print("\n✅ ALL CHANGES COMMITTED TO DATABASE")
    else:
        print("\n⚠️  DRY RUN - No changes committed")
        print("    Run with commit=True to apply fixes")
    
    print("="*100 + "\n")


if __name__ == "__main__":
    analyze_missing_taxable_values_all()
