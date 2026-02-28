import frappe

def show_failed_examples():
    """Show details of 2 failed invoices for manual review"""
    
    # Pick 2 different types of failed invoices
    examples = ["TSF-2602-0010", "HKMA-2601-0281"]
    
    for inv_name in examples:
        si = frappe.get_doc("Sales Invoice", inv_name)
        
        print("\n" + "="*80)
        print(f"INVOICE: {inv_name}")
        print("="*80)
        print(f"Date: {si.posting_date}")
        print(f"Company: {si.company}")
        print(f"Customer: {si.customer}")
        print(f"Grand Total: ₹{si.grand_total:,.2f}")
        print(f"Discount Amount: ₹{si.discount_amount:,.2f}")
        print(f"Is Consolidated: {si.is_consolidated}")
        
        print(f"\n{'='*80}")
        print("ITEMS (First 5):")
        print(f"{'='*80}")
        
        for idx, item in enumerate(si.items[:5], 1):
            print(f"\n{idx}. {item.item_code}:")
            print(f"   Template: {item.item_tax_template or 'None'}")
            print(f"   Amount: ₹{item.amount:,.2f}")
            print(f"   Base Net Amount: ₹{item.base_net_amount:,.2f}")
            print(f"   Taxable Value: ₹{item.taxable_value or 0:,.2f}")
            print(f"   CGST: {item.cgst_rate}% = ₹{item.cgst_amount or 0:.2f}")
            print(f"   SGST: {item.sgst_rate}% = ₹{item.sgst_amount or 0:.2f}")
            print(f"   IGST: {item.igst_rate}% = ₹{item.igst_amount or 0:.2f}")
        
        if len(si.items) > 5:
            print(f"\n   ... and {len(si.items) - 5} more items")
        
        print(f"\n{'='*80}")
        print("TAX TABLE:")
        print(f"{'='*80}")
        
        for tax in si.taxes:
            if 'GST' in tax.account_head:
                print(f"\n{tax.account_head}:")
                print(f"  Tax Amount: ₹{tax.tax_amount:,.2f}")
        
        print(f"\n{'='*80}")
        print("CALCULATED vs EXISTING:")
        print(f"{'='*80}")
        
        # Calculate totals from items
        total_cgst = sum(item.cgst_amount or 0 for item in si.items)
        total_sgst = sum(item.sgst_amount or 0 for item in si.items)
        total_igst = sum(item.igst_amount or 0 for item in si.items)
        
        # Get from tax table
        cgst_table = next((tax.tax_amount for tax in si.taxes if 'CGST' in tax.account_head), 0)
        sgst_table = next((tax.tax_amount for tax in si.taxes if 'SGST' in tax.account_head), 0)
        igst_table = next((tax.tax_amount for tax in si.taxes if 'IGST' in tax.account_head), 0)
        
        print(f"\nCGST:")
        print(f"  From Items: ₹{total_cgst:,.2f}")
        print(f"  From Table: ₹{cgst_table:,.2f}")
        print(f"  Difference: ₹{abs(total_cgst - cgst_table):.2f}")
        
        print(f"\nSGST:")
        print(f"  From Items: ₹{total_sgst:,.2f}")
        print(f"  From Table: ₹{sgst_table:,.2f}")
        print(f"  Difference: ₹{abs(total_sgst - sgst_table):.2f}")
        
        print(f"\nIGST:")
        print(f"  From Items: ₹{total_igst:,.2f}")
        print(f"  From Table: ₹{igst_table:,.2f}")
        print(f"  Difference: ₹{abs(total_igst - igst_table):.2f}")
        
        print(f"\nTotal GST:")
        print(f"  From Items: ₹{total_cgst + total_sgst + total_igst:,.2f}")
        print(f"  From Table: ₹{cgst_table + sgst_table + igst_table:,.2f}")
        print(f"  Difference: ₹{abs((total_cgst + total_sgst + total_igst) - (cgst_table + sgst_table + igst_table)):.2f}")

if __name__ == "__main__":
    show_failed_examples()
