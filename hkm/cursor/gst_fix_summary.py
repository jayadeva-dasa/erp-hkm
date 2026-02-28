import frappe
from hkm.cursor.fix_sales_invoice_gst import get_affected_invoices, get_item_tax_details

def show_summary():
    """Show concise summary of the GST issue and fix approach"""
    
    affected_data = get_affected_invoices()
    
    if not affected_data:
        print("\n✓ No issues found.")
        return
    
    total_items = sum(len(v) for v in affected_data.values())
    
    print("\n" + "="*80)
    print("GST FIX SUMMARY")
    print("="*80)
    
    print(f"\n📊 SCOPE:")
    print(f"   Affected Invoices: {len(affected_data)}")
    print(f"   Affected Items: {total_items}")
    print(f"   Period: Jan 29 - Feb 2, 2026")
    
    print(f"\n🔍 ISSUE:")
    print(f"   Items have Item Tax Template assigned")
    print(f"   BUT gst_treatment = 'Nil-Rated'")
    print(f"   AND taxable_value = 0")
    print(f"   AND all GST amounts = 0")
    
    print(f"\n✅ FIX APPROACH:")
    print(f"   1. Get correct GST treatment from Item Tax Template")
    print(f"   2. Set taxable_value = base_net_amount")
    print(f"   3. Get tax rates from item_wise_tax_detail (already in taxes)")
    print(f"   4. Calculate GST amounts = taxable_value × rate / 100")
    print(f"   5. Update database directly (no doc events)")
    print(f"   6. Regenerate GST breakup table")
    
    print(f"\n⚠️  RISK LEVEL: HIGH")
    print(f"   - Direct database update on submitted docs")
    print(f"   - Bypasses validation/events")
    print(f"   - Must ensure data consistency")
    
    print(f"\n🛡️  SAFETY MEASURES:")
    print(f"   - Transaction-based (rollback on error)")
    print(f"   - Uses existing tax rates from item_wise_tax_detail")
    print(f"   - Standard calculation formulas")
    print(f"   - Updates modified timestamp")
    
    # Sample verification
    print(f"\n📋 SAMPLE VERIFICATION:")
    sample_invoice = list(affected_data.keys())[0]
    sample_item = affected_data[sample_invoice][0]
    
    print(f"\n   Invoice: {sample_invoice}")
    print(f"   Item: {sample_item['item_code']}")
    print(f"   Template: {sample_item['item_tax_template']}")
    
    # Get correct treatment
    correct_treatment = frappe.db.get_value(
        'Item Tax Template',
        sample_item['item_tax_template'],
        'gst_treatment'
    )
    
    print(f"\n   BEFORE:")
    print(f"      GST Treatment: {sample_item['gst_treatment']}")
    print(f"      Taxable Value: ₹{sample_item['taxable_value']}")
    
    print(f"\n   AFTER (Expected):")
    print(f"      GST Treatment: {correct_treatment}")
    print(f"      Taxable Value: ₹{sample_item['base_net_amount']}")
    
    # Get tax rates
    tax_details = get_item_tax_details(sample_invoice, sample_item['item_name'])
    if tax_details:
        print(f"      Tax Rates:")
        for tax_type, rate in tax_details.items():
            amount = sample_item['base_net_amount'] * rate / 100
            print(f"         {tax_type.upper()}: {rate}% = ₹{amount:.2f}")
    
    print(f"\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    
    print("\n1. DRY RUN (Recommended first):")
    print('   bench --site hkmerp.in execute hkm.cursor.fix_sales_invoice_gst.execute_fix --kwargs \'{"dry_run": true}\'')
    
    print("\n2. ACTUAL FIX (After verifying dry run):")
    print('   bench --site hkmerp.in execute hkm.cursor.fix_sales_invoice_gst.execute_fix --kwargs \'{"dry_run": false}\'')
    
    print(f"\n⚠️  IMPORTANT: Take database backup before running actual fix!")
    print("="*80 + "\n")

if __name__ == "__main__":
    show_summary()
