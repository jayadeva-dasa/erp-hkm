import frappe

def check_discount_invoice():
    """Check HKMA-2601-0269 to see current state"""
    
    si = frappe.get_doc("Sales Invoice", "HKMA-2601-0269")
    
    print("\n" + "="*80)
    print(f"CHECKING: HKMA-2601-0269")
    print("="*80)
    print(f"Date: {si.posting_date}")
    print(f"Grand Total: ₹{si.grand_total:,.2f}")
    print(f"Discount Amount: ₹{si.discount_amount:,.2f}")
    
    print(f"\n{'='*80}")
    print("ITEMS:")
    print(f"{'='*80}")
    
    for item in si.items:
        print(f"\n{item.item_code}:")
        print(f"  Rate: ₹{item.rate}")
        print(f"  Amount: ₹{item.amount}")
        if hasattr(item, 'discount_amount') and item.discount_amount:
            print(f"  Discount Amount: ₹{item.discount_amount}")
        print(f"  Base Net Amount: ₹{item.base_net_amount}")
        print(f"  Taxable Value: ₹{item.taxable_value or 0}")
        print(f"  CGST: {item.cgst_rate}% = ₹{item.cgst_amount or 0}")
        print(f"  SGST: {item.sgst_rate}% = ₹{item.sgst_amount or 0}")
        print(f"  IGST: {item.igst_rate}% = ₹{item.igst_amount or 0}")
    
    print(f"\n{'='*80}")
    print("TAX TABLE:")
    print(f"{'='*80}")
    
    for tax in si.taxes:
        print(f"\n{tax.account_head}:")
        print(f"  Tax Amount: ₹{tax.tax_amount:,.2f}")
    
    print(f"\n{'='*80}")
    print("VERIFICATION:")
    print(f"{'='*80}")
    
    # Calculate what tax should be
    total_taxable = sum(item.taxable_value or item.base_net_amount for item in si.items)
    total_igst_calculated = sum(item.igst_amount or 0 for item in si.items)
    
    igst_from_table = next((tax.tax_amount for tax in si.taxes if 'IGST' in tax.account_head), 0)
    
    print(f"Total Taxable Value: ₹{total_taxable:,.2f}")
    print(f"IGST from items: ₹{total_igst_calculated:,.2f}")
    print(f"IGST from tax table: ₹{igst_from_table:,.2f}")
    print(f"Difference: ₹{abs(total_igst_calculated - igst_from_table):.2f}")
    
    if abs(total_igst_calculated - igst_from_table) <= 1:
        print(f"\n✅ Invoice is CORRECT!")
    else:
        print(f"\n❌ Invoice still has mismatch")

if __name__ == "__main__":
    check_discount_invoice()
