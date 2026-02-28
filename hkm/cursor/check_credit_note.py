"""
Check the credit note C-HKMA-2601-0001 in detail
"""

import frappe
import json

def check_credit_note():
    """
    Check the credit note C-HKMA-2601-0001
    """
    
    inv_name = 'C-HKMA-2601-0001'
    
    print("\n" + "="*100)
    print(f"INVOICE: {inv_name}")
    print("="*100)
    
    # Get invoice
    inv = frappe.get_doc("Sales Invoice", inv_name)
    
    print(f"\nIs Return: {inv.is_return}")
    print(f"Total: ₹{inv.total:,.2f}")
    print(f"Grand Total: ₹{inv.grand_total:,.2f}")
    print(f"Difference (grand_total - total): ₹{inv.grand_total - inv.total:,.2f}")
    
    # Get all tax rows with full details
    taxes = frappe.get_all("Sales Taxes and Charges",
                          filters={"parent": inv_name},
                          fields=["*"],
                          order_by="idx")
    
    print(f"\nTax Rows ({len(taxes)}):")
    print("-"*100)
    
    for idx, tax in enumerate(taxes, 1):
        print(f"\n{idx}. {tax.account_head}")
        print(f"   Charge Type: {tax.charge_type}")
        print(f"   Rate: {tax.rate}")
        print(f"   Tax Amount: ₹{tax.tax_amount:,.2f}")
        print(f"   Total: ₹{tax.total:,.2f}")
        print(f"   Base Tax Amount: ₹{tax.base_tax_amount:,.2f}")
        print(f"   Base Total: ₹{tax.base_total:,.2f}")
        
        if tax.item_wise_tax_detail:
            print(f"   Item Wise Tax Detail: {tax.item_wise_tax_detail}")
    
    # Calculate what the actual tax should be
    print("\n" + "="*100)
    print("ANALYSIS")
    print("="*100)
    
    total_tax_amount = sum(t.tax_amount for t in taxes)
    print(f"\nSum of all tax_amount fields: ₹{total_tax_amount:,.2f}")
    print(f"Grand Total - Total: ₹{inv.grand_total - inv.total:,.2f}")
    
    # Get items
    items = frappe.get_all("Sales Invoice Item",
                          filters={"parent": inv_name},
                          fields=["item_code", "amount", "taxable_value", 
                                 "cgst_amount", "sgst_amount", "igst_amount"])
    
    print(f"\nItems ({len(items)}):")
    for item in items:
        print(f"  {item.item_code}:")
        print(f"    Amount: ₹{item.amount:,.2f}")
        print(f"    Taxable Value: ₹{item.taxable_value or 0:,.2f}")
        print(f"    CGST: ₹{item.cgst_amount:,.2f}")
        print(f"    SGST: ₹{item.sgst_amount:,.2f}")
        print(f"    IGST: ₹{item.igst_amount:,.2f}")
        print(f"    Total Item Tax: ₹{item.cgst_amount + item.sgst_amount + item.igst_amount:,.2f}")

if __name__ == "__main__":
    check_credit_note()
