import frappe

def print_affected_invoice_ids():
    """Print invoice IDs with tax distribution issues"""
    
    company = "Golden Lotus Foundation"
    year = 2026
    month = 1
    
    sql = """
        SELECT 
            si.name as invoice_name,
            si.posting_date,
            si.grand_total,
            si.total,
            (si.grand_total - si.total) as tax_amount
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
        HAVING tax_amount > 0 
            AND SUM(si_item.cgst_amount + si_item.sgst_amount + si_item.igst_amount) = 0
        ORDER BY si.posting_date DESC, si.name
    """
    
    invoices = frappe.db.sql(sql, (company, year, month), as_dict=1)
    
    print("\n" + "="*100)
    print(f"AFFECTED INVOICE IDs - {company} - January {year}")
    print("="*100)
    print(f"\nTotal Invoices with Tax Distribution Issue: {len(invoices)}\n")
    
    # Print as comma-separated list for easy copy
    invoice_ids = [inv.invoice_name for inv in invoices]
    
    print("Invoice IDs (comma-separated):")
    print("-" * 100)
    print(", ".join(invoice_ids))
    print()
    
    # Print as list
    print("\nInvoice IDs (list format):")
    print("-" * 100)
    for i, invoice_id in enumerate(invoice_ids, 1):
        print(f"{i:2d}. {invoice_id}")
    
    # Print with amounts
    print("\n" + "="*100)
    print("Invoice IDs with Amounts:")
    print("="*100)
    for inv in invoices:
        print(f"{inv.invoice_name:20s} | Date: {inv.posting_date} | Total: ₹{inv.grand_total:>12,.2f} | Tax: ₹{inv.tax_amount:>10,.2f}")
    
    return invoice_ids

if __name__ == "__main__":
    print_affected_invoice_ids()
