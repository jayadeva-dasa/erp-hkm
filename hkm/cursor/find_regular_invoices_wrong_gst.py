import frappe

def find_regular_invoices():
    """Find regular (non-consolidated) Sales Invoices with wrong GST rates"""
    
    invoices = frappe.db.sql("""
        SELECT DISTINCT si.name, si.posting_date, si.company, si.is_consolidated
        FROM `tabSales Invoice` si
        INNER JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
        WHERE si.posting_date >= '2026-01-20'
        AND si.docstatus = 1
        AND (si.is_consolidated = 0 OR si.is_consolidated IS NULL)
        AND sii.item_tax_template IS NOT NULL
        AND sii.item_tax_template != ''
        AND (
            -- Items with wrong rates
            (sii.cgst_rate NOT IN (0, 0.05, 0.125, 1.5, 2.5, 6, 9, 14) AND sii.cgst_rate IS NOT NULL)
            OR
            -- Items with GST template but 0% rate
            (sii.cgst_rate = 0 AND sii.item_tax_template LIKE '%GST%' AND sii.item_tax_template NOT LIKE '%Exempt%')
        )
        ORDER BY si.posting_date, si.name
    """, as_dict=1)
    
    print("\n" + "="*80)
    print("REGULAR (NON-CONSOLIDATED) INVOICES WITH WRONG GST")
    print("="*80)
    print(f"Total found: {len(invoices)}")
    
    if invoices:
        print(f"\nInvoice List:")
        for inv in invoices:
            print(f"  - {inv.name} ({inv.posting_date}) - {inv.company} - Consolidated: {inv.is_consolidated}")
    
    return invoices

if __name__ == "__main__":
    find_regular_invoices()
