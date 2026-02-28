"""
Check the specific HKMA invoices that are showing as affected
"""

import frappe

def check_hkma_invoices():
    """
    Check the 3 HKMA invoices in detail
    """
    
    invoices = ['HKMA-2601-0063', 'C-HKMA-2601-0001', 'HKMA-2601-0161']
    
    for inv_name in invoices:
        print("\n" + "="*100)
        print(f"INVOICE: {inv_name}")
        print("="*100)
        
        # Get invoice details
        inv = frappe.get_doc("Sales Invoice", inv_name)
        print(f"\nTotal: ₹{inv.total:,.2f}")
        print(f"Grand Total: ₹{inv.grand_total:,.2f}")
        print(f"Invoice-level Tax: ₹{inv.grand_total - inv.total:,.2f}")
        
        # Get item-level tax totals
        items = frappe.get_all("Sales Invoice Item",
                              filters={"parent": inv_name},
                              fields=["item_code", "amount", "taxable_value", 
                                     "cgst_amount", "sgst_amount", "igst_amount"])
        
        total_item_tax = sum(item.cgst_amount + item.sgst_amount + item.igst_amount for item in items)
        
        print(f"Item-level Tax Total: ₹{total_item_tax:,.2f}")
        
        print(f"\nItems ({len(items)}):")
        for item in items:
            print(f"  {item.item_code}: Amount=₹{item.amount:,.2f}, TaxVal=₹{item.taxable_value or 0:,.2f}, "
                  f"CGST=₹{item.cgst_amount:,.2f}, SGST=₹{item.sgst_amount:,.2f}, IGST=₹{item.igst_amount:,.2f}")
        
        # Get tax rows
        taxes = frappe.get_all("Sales Taxes and Charges",
                              filters={"parent": inv_name},
                              fields=["account_head", "charge_type", "rate", "tax_amount"],
                              order_by="idx")
        
        print(f"\nTax Rows ({len(taxes)}):")
        for tax in taxes:
            print(f"  {tax.account_head}: {tax.charge_type}, Rate={tax.rate}, Amount=₹{tax.tax_amount:,.2f}")
        
        # Check if issue exists
        invoice_tax = inv.grand_total - inv.total
        if invoice_tax > 0.01 and total_item_tax < 0.01:
            print(f"\n⚠️  ISSUE: Invoice has ₹{invoice_tax:,.2f} in taxes but item-level total is ₹{total_item_tax:,.2f}")
        elif abs(total_item_tax - invoice_tax) < 0.01:
            print(f"\n✅ OK: Item-level taxes match invoice-level taxes")
        elif invoice_tax < 0.01:
            print(f"\n✅ OK: No taxes on this invoice")
        else:
            print(f"\n❓ Unexpected: Invoice tax=₹{invoice_tax:,.2f}, Item tax=₹{total_item_tax:,.2f}")

if __name__ == "__main__":
    check_hkma_invoices()
