"""
Verify that TSFJ invoices were actually fixed
"""

import frappe

def verify_tsfj_fix():
    """
    Verify a few TSFJ invoices to confirm the fix was applied
    """
    
    # Check a few sample invoices
    sample_invoices = ['TSFJ-2601-0216', 'TSFJ-2601-0217', 'TSFJ-2601-0220']
    
    print("\n" + "="*100)
    print("VERIFYING TOUCHSTONE FOUNDATION JAIPUR INVOICES")
    print("="*100)
    
    for inv_name in sample_invoices:
        print(f"\n{inv_name}:")
        
        # Check if invoice exists
        if not frappe.db.exists("Sales Invoice", inv_name):
            print(f"  ❌ Invoice not found")
            continue
        
        # Get invoice
        inv = frappe.get_doc("Sales Invoice", inv_name)
        
        invoice_tax = inv.grand_total - inv.total
        
        # Get item-level taxes
        items = frappe.get_all("Sales Invoice Item",
                              filters={"parent": inv_name},
                              fields=["item_code", "cgst_amount", "sgst_amount", "igst_amount"])
        
        item_tax_total = sum(item.cgst_amount + item.sgst_amount + item.igst_amount for item in items)
        
        print(f"  Invoice Tax: ₹{invoice_tax:,.2f}")
        print(f"  Item Tax Total: ₹{item_tax_total:,.2f}")
        print(f"  Difference: ₹{abs(invoice_tax - item_tax_total):,.2f}")
        
        if abs(invoice_tax - item_tax_total) < 0.01:
            print(f"  ✅ FIXED - Taxes match!")
        elif invoice_tax > 0.01 and item_tax_total < 0.01:
            print(f"  ❌ NOT FIXED - Item taxes still zero")
        else:
            print(f"  ⚠️ Status unclear")
    
    # Count all affected invoices
    print("\n" + "="*100)
    print("CHECKING ALL TSFJ INVOICES FROM JAN-FEB 2026")
    print("="*100)
    
    query = """
        SELECT 
            si.name,
            si.grand_total,
            si.total,
            (si.grand_total - si.total) as invoice_tax,
            SUM(si_item.cgst_amount + si_item.sgst_amount + si_item.igst_amount) as item_tax
        FROM 
            `tabSales Invoice` si
        INNER JOIN 
            `tabSales Invoice Item` si_item ON si.name = si_item.parent
        WHERE 
            si.docstatus = 1
            AND si.company = 'Touchstone Foundation Jaipur'
            AND si.posting_date BETWEEN '2026-01-01' AND '2026-02-10'
            AND (si.is_return IS NULL OR si.is_return = 0)
        GROUP BY si.name
    """
    
    results = frappe.db.sql(query, as_dict=1)
    
    fixed_count = 0
    not_fixed_count = 0
    no_tax_count = 0
    
    for row in results:
        invoice_tax = row['invoice_tax']
        item_tax = row['item_tax'] or 0
        
        if abs(invoice_tax - item_tax) < 0.01:
            if invoice_tax > 0.01:
                fixed_count += 1
            else:
                no_tax_count += 1
        elif invoice_tax > 0.01 and item_tax < 0.01:
            not_fixed_count += 1
    
    print(f"\nTotal TSFJ Invoices: {len(results)}")
    print(f"  ✅ Fixed (taxes distributed): {fixed_count}")
    print(f"  ⚠️ No taxes (skipped): {no_tax_count}")
    print(f"  ❌ Not fixed (still have issue): {not_fixed_count}")
    print("="*100 + "\n")

if __name__ == "__main__":
    verify_tsfj_fix()
