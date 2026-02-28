import frappe
from frappe.utils import flt
from hkm.cursor.fix_sales_invoice_gst import (
    get_tax_rates_from_template,
    get_item_tax_details,
    regenerate_gst_breakup
)

def fix_single_invoice(invoice_name, dry_run=False):
    """
    Fix a single Sales Invoice
    """
    
    print("\n" + "="*80)
    if dry_run:
        print(f"DRY RUN - Analyzing Invoice: {invoice_name}")
    else:
        print(f"FIXING Invoice: {invoice_name}")
    print("="*80)
    
    # Get affected items for this invoice
    query = """
        SELECT 
            sii.name as item_name,
            sii.item_code,
            sii.item_tax_template,
            sii.gst_treatment,
            sii.taxable_value,
            sii.base_net_amount,
            sii.qty,
            sii.rate,
            sii.amount,
            sii.igst_rate,
            sii.igst_amount,
            sii.cgst_rate,
            sii.cgst_amount,
            sii.sgst_rate,
            sii.sgst_amount
        FROM 
            `tabSales Invoice Item` sii
        WHERE 
            sii.parent = %s
            AND sii.item_tax_template IS NOT NULL
            AND sii.item_tax_template != ''
            AND (sii.gst_treatment = 'Nil-Rated' OR sii.gst_treatment IS NULL OR sii.gst_treatment = '')
            AND (sii.taxable_value = 0 OR sii.taxable_value IS NULL)
        ORDER BY 
            sii.idx
    """
    
    items = frappe.db.sql(query, (invoice_name,), as_dict=1)
    
    if not items:
        print(f"\n✓ No issues found in this invoice.")
        return
    
    print(f"\n📊 Found {len(items)} affected items")
    
    # Get invoice details
    invoice = frappe.get_doc('Sales Invoice', invoice_name)
    print(f"\n📋 Invoice Details:")
    print(f"   Customer: {invoice.customer}")
    print(f"   Date: {invoice.posting_date}")
    print(f"   Grand Total: ₹{invoice.grand_total}")
    print(f"   Place of Supply: {invoice.place_of_supply}")
    
    print(f"\n" + "="*80)
    print("CHANGES TO BE MADE")
    print("="*80)
    
    fixed_count = 0
    total_gst_to_add = 0
    
    for item in items:
        print(f"\n📦 Item: {item['item_code']}")
        print(f"   Template: {item['item_tax_template']}")
        
        # Get correct GST treatment
        gst_treatment = frappe.db.get_value(
            'Item Tax Template',
            item['item_tax_template'],
            'gst_treatment'
        )
        
        if not gst_treatment:
            gst_treatment = 'Taxable'
        
        # Get tax rates from template
        tax_details = get_tax_rates_from_template(item['item_tax_template'], invoice_name)
        
        # Fallback to item_wise_tax_detail if available
        if not tax_details:
            tax_details = get_item_tax_details(invoice_name, item['item_name'])
        
        # Calculate values
        taxable_value = flt(item['base_net_amount'])
        
        igst_rate = flt(tax_details.get('igst', 0))
        cgst_rate = flt(tax_details.get('cgst', 0))
        sgst_rate = flt(tax_details.get('sgst', 0))
        
        igst_amount = flt(taxable_value * igst_rate / 100, 2)
        cgst_amount = flt(taxable_value * cgst_rate / 100, 2)
        sgst_amount = flt(taxable_value * sgst_rate / 100, 2)
        
        total_item_gst = igst_amount + cgst_amount + sgst_amount
        total_gst_to_add += total_item_gst
        
        print(f"\n   BEFORE:")
        print(f"      GST Treatment: {item['gst_treatment']}")
        print(f"      Taxable Value: ₹{item['taxable_value']}")
        print(f"      IGST: {item['igst_rate']}% = ₹{item['igst_amount']}")
        print(f"      CGST: {item['cgst_rate']}% = ₹{item['cgst_amount']}")
        print(f"      SGST: {item['sgst_rate']}% = ₹{item['sgst_amount']}")
        print(f"      Total GST: ₹{item['igst_amount'] + item['cgst_amount'] + item['sgst_amount']}")
        
        print(f"\n   AFTER:")
        print(f"      GST Treatment: {gst_treatment}")
        print(f"      Taxable Value: ₹{taxable_value}")
        print(f"      IGST: {igst_rate}% = ₹{igst_amount}")
        print(f"      CGST: {cgst_rate}% = ₹{cgst_amount}")
        print(f"      SGST: {sgst_rate}% = ₹{sgst_amount}")
        print(f"      Total GST: ₹{total_item_gst}")
        
        if not dry_run:
            # Update database
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
                gst_treatment,
                taxable_value,
                igst_rate,
                igst_amount,
                cgst_rate,
                cgst_amount,
                sgst_rate,
                sgst_amount,
                item['item_name']
            ))
            
            fixed_count += 1
    
    print(f"\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Items to fix: {len(items)}")
    print(f"Total GST to be added: ₹{total_gst_to_add:.2f}")
    
    if not dry_run:
        # Commit changes
        frappe.db.commit()
        
        print(f"\n✅ Invoice {invoice_name} fixed successfully!")
        print(f"   Items updated: {fixed_count}")
        print(f"   Changes committed to database")
        print(f"\n   Note: GST breakup table will be regenerated on next invoice load")
    else:
        print(f"\n⚠️  DRY RUN - No changes made")
        print(f"   To apply changes, run with dry_run=False")
    
    print("="*80 + "\n")

if __name__ == "__main__":
    fix_single_invoice("HKMA-2601-0346", dry_run=True)
