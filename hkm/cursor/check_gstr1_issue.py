import frappe
from frappe.utils import getdate

def check_sales_invoice_data():
    """Check sales invoice data for Golden Lotus Foundation"""
    
    company = "Golden Lotus Foundation"
    year = 2026
    month = 1
    
    # Get sales invoices
    sql = """
        SELECT 
            si.name,
            si.posting_date,
            si.company_gstin,
            si_item.item_code,
            si_item.qty,
            si_item.rate,
            si_item.amount,
            si_item.taxable_value,
            si_item.cgst_amount,
            si_item.sgst_amount,
            si_item.igst_amount,
            si_item.gst_hsn_code
        FROM 
            `tabSales Invoice` si
        INNER JOIN 
            `tabSales Invoice Item` si_item ON si.name = si_item.parent
        WHERE 
            si.company = %s
            AND si.docstatus = 1
            AND YEAR(si.posting_date) = %s
            AND MONTH(si.posting_date) = %s
        ORDER BY si.posting_date DESC
        LIMIT 20
    """
    
    data = frappe.db.sql(sql, (company, year, month), as_dict=1)
    
    print("\n" + "="*100)
    print(f"Sales Invoice Data for {company} - {month}/{year}")
    print("="*100)
    
    if not data:
        print("No sales invoices found for this period")
        return
    
    for row in data:
        print(f"\nInvoice: {row.name}")
        print(f"  Date: {row.posting_date}")
        print(f"  GSTIN: {row.company_gstin}")
        print(f"  Item: {row.item_code}")
        print(f"  HSN: {row.gst_hsn_code}")
        print(f"  Qty: {row.qty}")
        print(f"  Rate: {row.rate}")
        print(f"  Amount: {row.amount}")
        print(f"  Taxable Value: {row.taxable_value}")
        print(f"  CGST: {row.cgst_amount}")
        print(f"  SGST: {row.sgst_amount}")
        print(f"  IGST: {row.igst_amount}")
    
    # Check if taxable_value is None or 0
    zero_taxable = [r for r in data if not r.taxable_value or r.taxable_value == 0]
    if zero_taxable:
        print(f"\n⚠️  Found {len(zero_taxable)} items with zero or null taxable_value")
        print("\nInvoices with zero taxable value:")
        for row in zero_taxable:
            print(f"  - {row.name}: qty={row.qty}, amount={row.amount}, taxable_value={row.taxable_value}")
    
    return data

if __name__ == "__main__":
    check_sales_invoice_data()
