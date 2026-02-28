import frappe

def check_invoice_taxes():
    """Check why taxes aren't applied on the invoice"""
    
    invoice_name = "GLF-2601-0549"
    
    print("\n" + "="*100)
    print(f"Invoice Analysis: {invoice_name}")
    print("="*100)
    
    invoice = frappe.get_doc("Sales Invoice", invoice_name)
    
    print(f"\nInvoice Details:")
    print(f"  Company: {invoice.company}")
    print(f"  Customer: {invoice.customer}")
    print(f"  Customer Name: {invoice.customer_name}")
    print(f"  GST Category: {invoice.gst_category}")
    print(f"  Place of Supply: {invoice.place_of_supply}")
    print(f"  Company GSTIN: {invoice.company_gstin}")
    print(f"  Customer GSTIN: {invoice.billing_address_gstin or 'Not Set'}")
    print(f"  Posting Date: {invoice.posting_date}")
    
    print(f"\n  Invoice Items ({len(invoice.items)} items):")
    for item in invoice.items[:3]:  # First 3 items
        print(f"    Item: {item.item_code}")
        print(f"      Qty: {item.qty} | Rate: {item.rate} | Amount: {item.amount}")
        print(f"      Taxable Value: {item.taxable_value}")
        print(f"      GST Treatment: {item.gst_treatment}")
        print(f"      CGST Rate: {item.cgst_rate}% | SGST Rate: {item.sgst_rate}% | IGST Rate: {item.igst_rate}%")
        print(f"      CGST Amount: {item.cgst_amount} | SGST Amount: {item.sgst_amount} | IGST Amount: {item.igst_amount}")
        print(f"      Item Tax Template: {item.item_tax_template or 'Not Set'}")
        print()
    
    print(f"\n  Sales Taxes and Charges ({len(invoice.taxes)} entries):")
    if invoice.taxes:
        for tax in invoice.taxes:
            print(f"    Account: {tax.account_head}")
            print(f"      Charge Type: {tax.charge_type}")
            print(f"      Rate: {tax.rate}")
            print(f"      Tax Amount: {tax.tax_amount}")
            print()
    else:
        print(f"    NO TAX ENTRIES FOUND!")
    
    print(f"\n  Totals:")
    print(f"    Total: {invoice.total}")
    print(f"    Grand Total: {invoice.grand_total}")
    print(f"    Net Total: {invoice.net_total}")
    
    return invoice

if __name__ == "__main__":
    check_invoice_taxes()
