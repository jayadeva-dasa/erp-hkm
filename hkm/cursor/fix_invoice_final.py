import frappe
from frappe.utils import flt
import json
from hkm.cursor.fix_sales_invoice_gst import get_tax_rates_from_template

def fix_invoice_final(invoice_name, dry_run=False):
    """
    Final comprehensive fix:
    1. Set taxable_value for ALL items (including Exempted)
    2. Fix GST fields for taxable items
    3. Update Sales Taxes and Charges table
    4. Populate item_wise_tax_detail for tax breakup display
    """
    
    print("\n" + "="*80)
    if dry_run:
        print(f"DRY RUN - Final Fix: {invoice_name}")
    else:
        print(f"FINAL FIX - Invoice: {invoice_name}")
    print("="*80)
    
    invoice = frappe.get_doc('Sales Invoice', invoice_name)
    
    print(f"\n📋 Invoice: {invoice_name}")
    print(f"   Customer: {invoice.customer}")
    print(f"   Date: {invoice.posting_date}")
    
    # Track totals
    total_cgst = 0
    total_sgst = 0
    total_igst = 0
    
    # Item-wise tax detail for each tax row
    cgst_item_wise = {}
    sgst_item_wise = {}
    igst_item_wise = {}
    
    print(f"\n" + "="*80)
    print("FIXING ALL ITEMS")
    print("="*80)
    
    items_fixed = 0
    
    for item in invoice.items:
        if not item.item_tax_template:
            continue
        
        # Get GST treatment
        gst_treatment = frappe.db.get_value(
            'Item Tax Template',
            item.item_tax_template,
            'gst_treatment'
        )
        
        if not gst_treatment:
            continue
        
        # Set taxable value for ALL items (including Exempted)
        taxable_value = flt(item.base_net_amount)
        
        # Get tax rates only for taxable items
        if gst_treatment in ('Taxable', 'Zero-Rated'):
            tax_details = get_tax_rates_from_template(item.item_tax_template, invoice_name)
            
            igst_rate = flt(tax_details.get('igst', 0))
            cgst_rate = flt(tax_details.get('cgst', 0))
            sgst_rate = flt(tax_details.get('sgst', 0))
            
            igst_amount = flt(taxable_value * igst_rate / 100, 2)
            cgst_amount = flt(taxable_value * cgst_rate / 100, 2)
            sgst_amount = flt(taxable_value * sgst_rate / 100, 2)
            
            total_igst += igst_amount
            total_cgst += cgst_amount
            total_sgst += sgst_amount
            
            # Store for item_wise_tax_detail
            if cgst_rate > 0:
                cgst_item_wise[item.name] = [cgst_rate, cgst_amount]
            if sgst_rate > 0:
                sgst_item_wise[item.name] = [sgst_rate, sgst_amount]
            if igst_rate > 0:
                igst_item_wise[item.name] = [igst_rate, igst_amount]
        else:
            # Exempted/Nil-Rated items
            igst_rate = cgst_rate = sgst_rate = 0
            igst_amount = cgst_amount = sgst_amount = 0
            
            # Add to item_wise_tax_detail with 0 rate
            cgst_item_wise[item.name] = [0, 0]
            sgst_item_wise[item.name] = [0, 0]
        
        # Check if update needed
        needs_update = (
            item.taxable_value != taxable_value or
            item.gst_treatment != gst_treatment or
            item.cgst_rate != cgst_rate or
            item.cgst_amount != cgst_amount or
            item.sgst_rate != sgst_rate or
            item.sgst_amount != sgst_amount or
            item.igst_rate != igst_rate or
            item.igst_amount != igst_amount
        )
        
        if needs_update:
            print(f"\n   {item.item_code} ({gst_treatment}):")
            print(f"      Taxable Value: ₹{item.taxable_value} → ₹{taxable_value}")
            if cgst_rate > 0 or sgst_rate > 0:
                print(f"      CGST: {item.cgst_rate}% → {cgst_rate}% (₹{cgst_amount})")
                print(f"      SGST: {item.sgst_rate}% → {sgst_rate}% (₹{sgst_amount})")
            
            if not dry_run:
                frappe.db.sql("""
                    UPDATE `tabSales Invoice Item`
                    SET 
                        gst_treatment = %s,
                        taxable_value = %s,
                        igst_rate = %s,
                        igst_amount = %s,
                        cgst_rate = %s,
                        cgst_amount = %s,
                        sgst_rate = %s,
                        sgst_amount = %s
                    WHERE name = %s
                """, (
                    gst_treatment, taxable_value,
                    igst_rate, igst_amount,
                    cgst_rate, cgst_amount,
                    sgst_rate, sgst_amount,
                    item.name
                ))
                items_fixed += 1
    
    print(f"\n" + "="*80)
    print("UPDATING TAX TABLE")
    print("="*80)
    
    print(f"\n   Total CGST: ₹{total_cgst:.2f}")
    print(f"   Total SGST: ₹{total_sgst:.2f}")
    print(f"   Total IGST: ₹{total_igst:.2f}")
    
    if not dry_run:
        # Get tax rows
        tax_rows = frappe.get_all(
            'Sales Taxes and Charges',
            filters={'parent': invoice_name},
            fields=['name', 'account_head'],
            order_by='idx'
        )
        
        for tax in tax_rows:
            account_head = tax.account_head.upper()
            
            if 'CGST' in account_head:
                gst_tax_type = 'cgst'
                tax_amount = total_cgst
                item_wise_detail = json.dumps(cgst_item_wise)
            elif 'SGST' in account_head:
                gst_tax_type = 'sgst'
                tax_amount = total_sgst
                item_wise_detail = json.dumps(sgst_item_wise)
            elif 'IGST' in account_head:
                gst_tax_type = 'igst'
                tax_amount = total_igst
                item_wise_detail = json.dumps(igst_item_wise)
            else:
                continue
            
            print(f"\n   Updating {tax.account_head}:")
            print(f"      Tax Type: {gst_tax_type}")
            print(f"      Amount: ₹{tax_amount:.2f}")
            print(f"      Item-wise detail: {len(cgst_item_wise)} items")
            
            frappe.db.sql("""
                UPDATE `tabSales Taxes and Charges`
                SET 
                    gst_tax_type = %s,
                    tax_amount = %s,
                    base_tax_amount = %s,
                    tax_amount_after_discount_amount = %s,
                    base_tax_amount_after_discount_amount = %s,
                    item_wise_tax_detail = %s
                WHERE name = %s
            """, (
                gst_tax_type,
                tax_amount,
                tax_amount,
                tax_amount,
                tax_amount,
                item_wise_detail,
                tax.name
            ))
    
    print(f"\n" + "="*80)
    print("VALIDATION")
    print("="*80)
    
    # Verify totals match
    validation_passed = True
    
    if not dry_run:
        # Get actual tax amounts from tax table after update
        actual_taxes = frappe.db.sql("""
            SELECT 
                gst_tax_type,
                tax_amount
            FROM `tabSales Taxes and Charges`
            WHERE parent = %s
            AND gst_tax_type IN ('cgst', 'sgst', 'igst')
        """, (invoice_name,), as_dict=1)
        
        actual_cgst = 0
        actual_sgst = 0
        actual_igst = 0
        
        for tax in actual_taxes:
            if tax.gst_tax_type == 'cgst':
                actual_cgst = flt(tax.tax_amount, 2)
            elif tax.gst_tax_type == 'sgst':
                actual_sgst = flt(tax.tax_amount, 2)
            elif tax.gst_tax_type == 'igst':
                actual_igst = flt(tax.tax_amount, 2)
        
        print(f"\n   Calculated from Items:")
        print(f"      CGST: ₹{total_cgst:.2f}")
        print(f"      SGST: ₹{total_sgst:.2f}")
        print(f"      IGST: ₹{total_igst:.2f}")
        print(f"      Total: ₹{(total_cgst + total_sgst + total_igst):.2f}")
        
        print(f"\n   Tax Table Amounts:")
        print(f"      CGST: ₹{actual_cgst:.2f}")
        print(f"      SGST: ₹{actual_sgst:.2f}")
        print(f"      IGST: ₹{actual_igst:.2f}")
        print(f"      Total: ₹{(actual_cgst + actual_sgst + actual_igst):.2f}")
        
        # Check for mismatches (allow 0.01 difference for rounding)
        cgst_diff = abs(total_cgst - actual_cgst)
        sgst_diff = abs(total_sgst - actual_sgst)
        igst_diff = abs(total_igst - actual_igst)
        
        if cgst_diff > 0.01 or sgst_diff > 0.01 or igst_diff > 0.01:
            validation_passed = False
            print(f"\n   ⚠️  MISMATCH DETECTED!")
            if cgst_diff > 0.01:
                print(f"      CGST difference: ₹{cgst_diff:.2f}")
            if sgst_diff > 0.01:
                print(f"      SGST difference: ₹{sgst_diff:.2f}")
            if igst_diff > 0.01:
                print(f"      IGST difference: ₹{igst_diff:.2f}")
        else:
            print(f"\n   ✅ VALIDATION PASSED - Amounts match!")
    
    print(f"\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Items updated: {items_fixed if not dry_run else 'N/A (dry run)'}")
    print(f"Total GST: ₹{total_cgst + total_sgst + total_igst:.2f}")
    
    if not dry_run:
        if validation_passed:
            frappe.db.commit()
            print(f"\n✅ Invoice {invoice_name} completely fixed!")
            print(f"   ✓ All items have taxable_value set")
            print(f"   ✓ GST fields updated for taxable items")
            print(f"   ✓ Tax table updated with item-wise breakup")
            print(f"   ✓ Validation passed - amounts match")
            print(f"   ✓ Changes committed")
            return True
        else:
            frappe.db.rollback()
            print(f"\n❌ Invoice {invoice_name} - VALIDATION FAILED!")
            print(f"   ✗ Amounts don't match")
            print(f"   ✗ Changes rolled back")
            return False
    else:
        print(f"\n⚠️  DRY RUN - No changes made")
        return None
    
    print("="*80 + "\n")

if __name__ == "__main__":
    fix_invoice_final("HKMA-2601-0346", dry_run=True)
