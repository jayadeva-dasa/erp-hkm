import frappe

def find_affected_invoices():
    """Find invoices with taxes but 0% item-level tax rates"""
    
    company = "Golden Lotus Foundation"
    year = 2026
    month = 1
    
    sql = """
        SELECT 
            si.name as invoice_name,
            si.posting_date,
            si.grand_total,
            si.total,
            (si.grand_total - si.total) as tax_difference,
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
            AND YEAR(si.posting_date) = %s
            AND MONTH(si.posting_date) = %s
        GROUP BY si.name
        HAVING tax_difference > 0 AND total_item_tax = 0
        ORDER BY si.posting_date DESC
    """
    
    invoices = frappe.db.sql(sql, (company, year, month), as_dict=1)
    
    print("\n" + "="*100)
    print(f"Invoices with Tax Calculation Issues - {company} - {month}/{year}")
    print("="*100)
    print(f"\nFound {len(invoices)} invoices with taxes at invoice level but not distributed to items")
    print()
    
    total_affected_taxable = 0
    total_affected_tax = 0
    
    for inv in invoices:
        print(f"Invoice: {inv.invoice_name} | Date: {inv.posting_date}")
        print(f"  Grand Total: {inv.grand_total:.2f} | Net Total: {inv.total:.2f} | Tax: {inv.tax_difference:.2f}")
        print(f"  Items: {inv.item_count} | Total Taxable Value: {inv.total_taxable_value:.2f}")
        print(f"  Item-level Tax: {inv.total_item_tax:.2f} (SHOULD MATCH Tax but is 0)")
        print()
        
        total_affected_taxable += inv.total_taxable_value or 0
        total_affected_tax += inv.tax_difference or 0
    
    print("="*100)
    print("SUMMARY:")
    print("="*100)
    print(f"Total Affected Invoices: {len(invoices)}")
    print(f"Total Taxable Value affected: ₹{total_affected_taxable:,.2f}")
    print(f"Total Tax amount not distributed: ₹{total_affected_tax:,.2f}")
    print()
    print("⚠️  These invoices have taxes collected but not distributed to items.")
    print("⚠️  This causes GSTR-1 HSN Summary to show 0 taxable values.")
    
    return invoices

if __name__ == "__main__":
    find_affected_invoices()
