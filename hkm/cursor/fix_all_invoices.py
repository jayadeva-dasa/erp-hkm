import frappe
from hkm.cursor.fix_invoice_final import fix_invoice_final

def fix_all_gst_invoices():
    """
    Fix all affected Sales Invoices in FY 2025-26
    with validation to ensure amounts match
    """
    
    print("\n" + "="*80)
    print("BATCH FIX - ALL AFFECTED SALES INVOICES")
    print("="*80)
    
    # Get all affected invoices
    query = """
        SELECT DISTINCT si.name
        FROM `tabSales Invoice` si
        INNER JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
        WHERE 
            si.docstatus = 1
            AND si.posting_date BETWEEN '2025-04-01' AND '2026-03-31'
            AND sii.item_tax_template IS NOT NULL
            AND sii.item_tax_template != ''
            AND (
                (sii.gst_treatment = 'Nil-Rated' OR sii.gst_treatment IS NULL OR sii.gst_treatment = '')
                AND (sii.taxable_value = 0 OR sii.taxable_value IS NULL)
                OR
                (sii.gst_treatment = 'Exempted' AND (sii.taxable_value = 0 OR sii.taxable_value IS NULL))
            )
        ORDER BY si.posting_date, si.name
    """
    
    invoices = frappe.db.sql(query, as_dict=1)
    
    print(f"\n📊 Found {len(invoices)} invoices to process")
    print("="*80)
    
    success_count = 0
    failed_count = 0
    failed_invoices = []
    
    for idx, inv in enumerate(invoices, 1):
        print(f"\n[{idx}/{len(invoices)}] Processing: {inv.name}")
        print("-" * 80)
        
        try:
            result = fix_invoice_final(inv.name, dry_run=False)
            
            if result:
                success_count += 1
                print(f"✅ Success")
            else:
                failed_count += 1
                failed_invoices.append(inv.name)
                print(f"❌ Failed - Validation error")
        
        except Exception as e:
            failed_count += 1
            failed_invoices.append(inv.name)
            print(f"❌ Error: {str(e)}")
            frappe.db.rollback()
    
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    print(f"\nTotal Invoices: {len(invoices)}")
    print(f"✅ Successfully Fixed: {success_count}")
    print(f"❌ Failed: {failed_count}")
    
    if failed_invoices:
        print(f"\n⚠️  Failed Invoices (need manual review):")
        for inv in failed_invoices:
            print(f"   - {inv}")
    
    print("\n" + "="*80 + "\n")
    
    return {
        'total': len(invoices),
        'success': success_count,
        'failed': failed_count,
        'failed_invoices': failed_invoices
    }

if __name__ == "__main__":
    fix_all_gst_invoices()
