"""
Check specific TSFK invoices for detailed analysis
"""

import frappe
import json

def check_specific_invoices():
    """
    Check the specific TSFK invoices mentioned by user
    """
    
    invoices = ['TSFK-2601-0070', 'TSFK-2601-0067']
    
    for inv_name in invoices:
        print("\n" + "="*100)
        print(f"INVOICE: {inv_name}")
        print("="*100)
        
        # Check if invoice exists
        if not frappe.db.exists("Sales Invoice", inv_name):
            print(f"❌ Invoice not found")
            continue
        
        # Get invoice
        inv = frappe.get_doc("Sales Invoice", inv_name)
        
        print(f"\nBasic Details:")
        print(f"  Customer: {inv.customer}")
        print(f"  Posting Date: {inv.posting_date}")
        print(f"  Status: {'Submitted' if inv.docstatus == 1 else 'Draft' if inv.docstatus == 0 else 'Cancelled'}")
        print(f"  Is Return: {inv.is_return}")
        
        print(f"\nAmounts:")
        print(f"  Total (Net): ₹{inv.total:,.2f}")
        print(f"  Grand Total: ₹{inv.grand_total:,.2f}")
        print(f"  Invoice-level Tax: ₹{inv.grand_total - inv.total:,.2f}")
        
        # Get items
        items = frappe.get_all("Sales Invoice Item",
                              filters={"parent": inv_name},
                              fields=["idx", "item_code", "item_name", "qty", "rate", "amount", 
                                     "taxable_value", "cgst_amount", "sgst_amount", "igst_amount",
                                     "cgst_rate", "sgst_rate", "igst_rate", "gst_hsn_code"],
                              order_by="idx")
        
        print(f"\nItems ({len(items)}):")
        print("-"*100)
        
        total_item_tax = 0
        for item in items:
            item_tax = item.cgst_amount + item.sgst_amount + item.igst_amount
            total_item_tax += item_tax
            
            print(f"\n  {item.idx}. {item.item_code} - {item.item_name}")
            print(f"     Qty: {item.qty}, Rate: ₹{item.rate:,.2f}, Amount: ₹{item.amount:,.2f}")
            print(f"     Taxable Value: ₹{item.taxable_value or 0:,.2f}")
            print(f"     HSN: {item.gst_hsn_code or 'N/A'}")
            print(f"     CGST: ₹{item.cgst_amount:,.2f} ({item.cgst_rate}%)")
            print(f"     SGST: ₹{item.sgst_amount:,.2f} ({item.sgst_rate}%)")
            print(f"     IGST: ₹{item.igst_amount:,.2f} ({item.igst_rate}%)")
            print(f"     Total Item Tax: ₹{item_tax:,.2f}")
        
        print(f"\n  Total Item-level Tax: ₹{total_item_tax:,.2f}")
        
        # Get tax rows
        taxes = frappe.get_all("Sales Taxes and Charges",
                              filters={"parent": inv_name},
                              fields=["idx", "account_head", "charge_type", "rate", 
                                     "tax_amount", "total", "item_wise_tax_detail"],
                              order_by="idx")
        
        print(f"\nTax Rows ({len(taxes)}):")
        print("-"*100)
        
        for tax in taxes:
            print(f"\n  {tax.idx}. {tax.account_head}")
            print(f"     Charge Type: {tax.charge_type}")
            print(f"     Rate: {tax.rate}")
            print(f"     Tax Amount: ₹{tax.tax_amount:,.2f}")
            print(f"     Running Total: ₹{tax.total:,.2f}")
            
            if tax.item_wise_tax_detail:
                try:
                    item_wise = json.loads(tax.item_wise_tax_detail)
                    if item_wise:
                        print(f"     Item Wise Tax Detail:")
                        for item_code, detail in item_wise.items():
                            print(f"       - {item_code}: Rate={detail[0]}%, Amount=₹{detail[1]:,.2f}")
                    else:
                        print("     Item Wise Tax Detail: {} (empty)")
                except:
                    print(f"     Item Wise Tax Detail: {tax.item_wise_tax_detail}")
            else:
                print(f"     Item Wise Tax Detail: None")
        
        # Analysis
        print("\n" + "="*100)
        print("ANALYSIS")
        print("="*100)
        
        invoice_tax = inv.grand_total - inv.total
        difference = abs(invoice_tax - total_item_tax)
        
        print(f"\nInvoice-level Tax: ₹{invoice_tax:,.2f}")
        print(f"Item-level Tax Total: ₹{total_item_tax:,.2f}")
        print(f"Difference: ₹{difference:,.2f}")
        
        if difference < 0.01:
            print("\n✅ STATUS: Taxes are properly distributed!")
        elif invoice_tax > 0.01 and total_item_tax < 0.01:
            print("\n❌ STATUS: Tax distribution issue - Item taxes are zero!")
        elif difference > 0.01:
            print(f"\n⚠️  STATUS: Tax mismatch - Difference of ₹{difference:,.2f}")
        else:
            print("\n✅ STATUS: OK")

if __name__ == "__main__":
    check_specific_invoices()
