import frappe
import json

def check_invoice():
    """Check GLF-2601-0525 GST breakup table"""
    
    invoice_name = "GLF-2601-0525"
    
    si = frappe.get_doc("Sales Invoice", invoice_name)
    
    print("\n" + "="*80)
    print(f"CHECKING: {invoice_name}")
    print("="*80)
    print(f"Date: {si.posting_date}")
    print(f"Is Consolidated: {si.is_consolidated}")
    print(f"Grand Total: ₹{si.grand_total:,.2f}")
    
    # Check GST Breakup Table
    print(f"\n{'='*80}")
    print("GST BREAKUP TABLE (gst_breakup_table):")
    print(f"{'='*80}")
    
    if hasattr(si, 'gst_breakup_table') and si.gst_breakup_table:
        for row in si.gst_breakup_table:
            print(f"\nHSN: {row.hsn_sac}")
            print(f"  Taxable Amount: ₹{row.taxable_amount:,.2f}")
            print(f"  CGST Rate: {row.cgst_rate}%")
            print(f"  CGST Amount: ₹{row.cgst_amount:,.2f}")
            print(f"  SGST Rate: {row.sgst_rate}%")
            print(f"  SGST Amount: ₹{row.sgst_amount:,.2f}")
    else:
        print("  ⚠️  No GST Breakup Table found!")
    
    # Check item-level GST rates
    print(f"\n{'='*80}")
    print("ITEM-LEVEL GST RATES:")
    print(f"{'='*80}")
    
    rate_summary = {}
    for item in si.items:
        cgst_rate = item.cgst_rate or 0
        if cgst_rate not in rate_summary:
            rate_summary[cgst_rate] = {"count": 0, "amount": 0, "cgst": 0}
        rate_summary[cgst_rate]["count"] += 1
        rate_summary[cgst_rate]["amount"] += item.amount
        rate_summary[cgst_rate]["cgst"] += (item.cgst_amount or 0)
    
    for rate in sorted(rate_summary.keys()):
        data = rate_summary[rate]
        print(f"\nCGST Rate: {rate}%")
        print(f"  Items: {data['count']}")
        print(f"  Amount: ₹{data['amount']:,.2f}")
        print(f"  CGST: ₹{data['cgst']:,.2f}")
    
    # Check tax table item_wise_tax_detail
    print(f"\n{'='*80}")
    print("TAX TABLE - ITEM_WISE_TAX_DETAIL:")
    print(f"{'='*80}")
    
    for tax in si.taxes:
        if 'CGST' in tax.account_head or 'SGST' in tax.account_head:
            print(f"\n{tax.account_head}:")
            print(f"  Tax Amount: ₹{tax.tax_amount:,.2f}")
            
            if tax.item_wise_tax_detail:
                try:
                    detail = json.loads(tax.item_wise_tax_detail)
                    print(f"  Items in detail: {len(detail)}")
                    
                    # Check for wrong rates
                    wrong_rates = []
                    for item_name, values in detail.items():
                        rate, amount = values
                        if rate not in [0, 2.5, 5, 6, 9, 12, 14, 18, 28] and rate > 0:
                            wrong_rates.append((item_name, rate, amount))
                    
                    if wrong_rates:
                        print(f"  ❌ Found {len(wrong_rates)} items with WRONG rates")
                        for item, rate, amt in wrong_rates[:5]:
                            print(f"     - {rate}% = ₹{amt}")
                    else:
                        print(f"  ✅ All rates correct")
                        
                except Exception as e:
                    print(f"  Error: {e}")

if __name__ == "__main__":
    check_invoice()
