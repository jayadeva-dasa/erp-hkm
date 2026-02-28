import frappe
from frappe.utils import flt
from hkm.cursor.fix_sales_invoice_gst import get_tax_rates_from_template

def fix_invoice_complete(invoice_name, dry_run=False):
    """
    Complete fix for Sales Invoice including:
    1. Item-level GST fields
    2. Sales Taxes and Charges table
    3. GST tax type mapping
    """
    
    print("\n" + "="*80)
    if dry_run:
        print(f"DRY RUN - Complete Analysis: {invoice_name}")
    else:
        print(f"COMPLETE FIX - Invoice: {invoice_name}")
    print("="*80)
    
    # Get invoice
    invoice = frappe.get_doc('Sales Invoice', invoice_name)
    
    print(f"\n📋 Invoice: {invoice_name}")
    print(f"   Customer: {invoice.customer}")
    print(f"   Date: {invoice.posting_date}")
    print(f"   Grand Total: ₹{invoice.grand_total}")
    
    # Get affected items
    affected_items = []
    for item in invoice.items:
        if (item.item_tax_template and 
            (not item.gst_treatment or item.gst_treatment == 'Nil-Rated') and
            (not item.taxable_value or item.taxable_value == 0)):
            affected_items.append(item)
    
    if not affected_items:
        print(f"\n✓ No issues found.")
        return
    
    print(f"\n📊 Found {len(affected_items)} affected items")
    
    # Calculate total GST by type
    total_cgst = 0
    total_sgst = 0
    total_igst = 0
    
    print(f"\n" + "="*80)
    print("STEP 1: FIX ITEM-LEVEL GST")
    print("="*80)
    
    for item in affected_items:
        # Get GST treatment
        gst_treatment = frappe.db.get_value(
            'Item Tax Template',
            item.item_tax_template,
            'gst_treatment'
        ) or 'Taxable'
        
        # Get tax rates
        tax_details = get_tax_rates_from_template(item.item_tax_template, invoice_name)
        
        # Calculate
        taxable_value = flt(item.base_net_amount)
        igst_rate = flt(tax_details.get('igst', 0))
        cgst_rate = flt(tax_details.get('cgst', 0))
        sgst_rate = flt(tax_details.get('sgst', 0))
        
        igst_amount = flt(taxable_value * igst_rate / 100, 2)
        cgst_amount = flt(taxable_value * cgst_rate / 100, 2)
        sgst_amount = flt(taxable_value * sgst_rate / 100, 2)
        
        total_igst += igst_amount
        total_cgst += cgst_amount
        total_sgst += sgst_amount
        
        print(f"\n   {item.item_code}: Taxable ₹{taxable_value:.2f}")
        print(f"      CGST: {cgst_rate}% = ₹{cgst_amount:.2f}")
        print(f"      SGST: {sgst_rate}% = ₹{sgst_amount:.2f}")
        
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
    
    print(f"\n" + "="*80)
    print("STEP 2: FIX SALES TAXES AND CHARGES TABLE")
    print("="*80)
    
    print(f"\n   Total CGST to charge: ₹{total_cgst:.2f}")
    print(f"   Total SGST to charge: ₹{total_sgst:.2f}")
    print(f"   Total IGST to charge: ₹{total_igst:.2f}")
    
    # Get tax rows
    tax_rows = frappe.get_all(
        'Sales Taxes and Charges',
        filters={'parent': invoice_name},
        fields=['name', 'account_head', 'charge_type', 'rate', 'tax_amount'],
        order_by='idx'
    )
    
    print(f"\n   Current tax rows:")
    for tax in tax_rows:
        print(f"      {tax.account_head}: ₹{tax.tax_amount}")
    
    if not dry_run:
        # Update tax rows with correct gst_tax_type and amounts
        for tax in tax_rows:
            account_head = tax.account_head.upper()
            
            if 'CGST' in account_head:
                gst_tax_type = 'cgst'
                tax_amount = total_cgst
            elif 'SGST' in account_head:
                gst_tax_type = 'sgst'
                tax_amount = total_sgst
            elif 'IGST' in account_head:
                gst_tax_type = 'igst'
                tax_amount = total_igst
            else:
                continue
            
            print(f"\n   Updating {tax.account_head}:")
            print(f"      Setting gst_tax_type = {gst_tax_type}")
            print(f"      Setting tax_amount = ₹{tax_amount:.2f}")
            
            frappe.db.sql("""
                UPDATE `tabSales Taxes and Charges`
                SET 
                    gst_tax_type = %s,
                    tax_amount = %s,
                    base_tax_amount = %s,
                    tax_amount_after_discount_amount = %s,
                    base_tax_amount_after_discount_amount = %s
                WHERE name = %s
            """, (
                gst_tax_type,
                tax_amount,
                tax_amount,
                tax_amount,
                tax_amount,
                tax.name
            ))
    
    print(f"\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Items fixed: {len(affected_items)}")
    print(f"Total GST: ₹{total_cgst + total_sgst + total_igst:.2f}")
    
    if not dry_run:
        frappe.db.commit()
        print(f"\n✅ Invoice {invoice_name} completely fixed!")
        print(f"   Changes committed to database")
    else:
        print(f"\n⚠️  DRY RUN - No changes made")
    
    print("="*80 + "\n")

if __name__ == "__main__":
    fix_invoice_complete("HKMA-2601-0346", dry_run=True)
