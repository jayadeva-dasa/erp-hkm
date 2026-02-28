import frappe

def check_gst_treatment():
    """Check GST treatment for Golden Lotus Foundation invoices"""
    
    company = "Golden Lotus Foundation"
    year = 2026
    month = 1
    
    sql = """
        SELECT 
            si.name,
            si.posting_date,
            si.gst_category,
            si_item.item_code,
            si_item.gst_hsn_code,
            si_item.qty,
            si_item.taxable_value,
            si_item.gst_treatment,
            si_item.cgst_rate,
            si_item.sgst_rate,
            si_item.igst_rate
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
        LIMIT 10
    """
    
    data = frappe.db.sql(sql, (company, year, month), as_dict=1)
    
    print("\n" + "="*100)
    print(f"GST Treatment Analysis for {company} - {month}/{year}")
    print("="*100)
    
    for row in data:
        print(f"\nInvoice: {row.name} | Date: {row.posting_date}")
        print(f"  GST Category: {row.gst_category}")
        print(f"  Item: {row.item_code} | HSN: {row.gst_hsn_code}")
        print(f"  Qty: {row.qty} | Taxable Value: {row.taxable_value}")
        print(f"  GST Treatment: {row.gst_treatment}")
        print(f"  Tax Rates - CGST: {row.cgst_rate}% | SGST: {row.sgst_rate}% | IGST: {row.igst_rate}%")
    
    # Summary
    treatments = {}
    for row in data:
        treatment = row.gst_treatment or "Not Defined"
        treatments[treatment] = treatments.get(treatment, 0) + 1
    
    print("\n" + "="*100)
    print("GST Treatment Summary:")
    print("="*100)
    for treatment, count in treatments.items():
        print(f"  {treatment}: {count} items")
    
    return data

if __name__ == "__main__":
    check_gst_treatment()
