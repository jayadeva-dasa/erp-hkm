"""
Update item_wise_tax_detail in Sales Taxes and Charges table
for invoices that already have item-level tax amounts
"""

import frappe
from frappe.utils import flt
import json

def update_item_wise_tax_detail(invoice_name):
    """
    Update item_wise_tax_detail field in Sales Taxes and Charges table
    based on existing item-level tax data
    """
    
    invoice = frappe.get_doc("Sales Invoice", invoice_name)
    
    # Build item_wise_tax_detail from items
    cgst_item_wise = {}
    sgst_item_wise = {}
    igst_item_wise = {}
    
    for item in invoice.items:
        # Use item_code as key (for tax breakup display)
        item_key = item.item_code
        
        # CGST
        if flt(item.cgst_rate) > 0:
            cgst_item_wise[item_key] = [flt(item.cgst_rate), flt(item.cgst_amount)]
        
        # SGST
        if flt(item.sgst_rate) > 0:
            sgst_item_wise[item_key] = [flt(item.sgst_rate), flt(item.sgst_amount)]
        
        # IGST
        if flt(item.igst_rate) > 0:
            igst_item_wise[item_key] = [flt(item.igst_rate), flt(item.igst_amount)]
    
    # Update Sales Taxes and Charges table
    updated_count = 0
    
    for tax in invoice.taxes:
        account_name = tax.account_head.lower()
        
        if 'cgst' in account_name and cgst_item_wise:
            item_wise_detail = json.dumps(cgst_item_wise)
            frappe.db.set_value('Sales Taxes and Charges', tax.name, {
                'item_wise_tax_detail': item_wise_detail
            }, update_modified=False)
            updated_count += 1
            
        elif 'sgst' in account_name and sgst_item_wise:
            item_wise_detail = json.dumps(sgst_item_wise)
            frappe.db.set_value('Sales Taxes and Charges', tax.name, {
                'item_wise_tax_detail': item_wise_detail
            }, update_modified=False)
            updated_count += 1
            
        elif 'igst' in account_name and igst_item_wise:
            item_wise_detail = json.dumps(igst_item_wise)
            frappe.db.set_value('Sales Taxes and Charges', tax.name, {
                'item_wise_tax_detail': item_wise_detail
            }, update_modified=False)
            updated_count += 1
    
    return {
        'invoice': invoice_name,
        'updated_count': updated_count,
        'cgst_items': len(cgst_item_wise),
        'sgst_items': len(sgst_item_wise),
        'igst_items': len(igst_item_wise)
    }


def update_multiple_invoices(invoice_list, commit=False):
    """
    Update item_wise_tax_detail for multiple invoices
    """
    
    print("\n" + "="*100)
    print(f"UPDATING ITEM_WISE_TAX_DETAIL - {len(invoice_list)} Invoices")
    print("="*100)
    print(f"Commit Mode: {'ENABLED' if commit else 'DISABLED (dry run)'}")
    print("="*100 + "\n")
    
    success_count = 0
    error_count = 0
    
    for i, invoice_name in enumerate(invoice_list, 1):
        try:
            result = update_item_wise_tax_detail(invoice_name)
            
            print(f"{i:2d}. ✅ {invoice_name}")
            print(f"     Updated {result['updated_count']} tax rows")
            print(f"     CGST items: {result['cgst_items']}, SGST items: {result['sgst_items']}, IGST items: {result['igst_items']}")
            
            success_count += 1
            
        except Exception as e:
            print(f"{i:2d}. ❌ {invoice_name} - Error: {str(e)}")
            error_count += 1
    
    if commit:
        frappe.db.commit()
        print("\n✅ Changes committed to database")
    else:
        print("\n⚠️  Dry run - No changes committed")
    
    print("\n" + "="*100)
    print("SUMMARY")
    print("="*100)
    print(f"Total: {len(invoice_list)}")
    print(f"✅ Success: {success_count}")
    print(f"❌ Errors: {error_count}")
    print("="*100 + "\n")
    
    return {
        'total': len(invoice_list),
        'success': success_count,
        'errors': error_count
    }


def update_golden_lotus_january_2026(commit=False):
    """
    Update item_wise_tax_detail for all Golden Lotus invoices from January 2026
    """
    
    invoice_list = [
        "GLF-2601-0519", "GLF-2601-0520", "GLF-2601-0521", "GLF-2601-0523", 
        "GLF-2601-0524", "GLF-2601-0525", "GLF-2601-0527", "GLF-2601-0528",
        "GLF-2601-0530", "GLF-2601-0531", "GLF-2601-0532", "GLF-2601-0533",
        "GLF-2601-0534", "GLF-2601-0535", "GLF-2601-0537", "GLF-2601-0538",
        "GLF-2601-0539", "GLF-2601-0540", "GLF-2601-0541", "GLF-2601-0543",
        "GLF-2601-0549", "GLF-2601-0479", "GLF-2601-0480", "GLF-2601-0481",
        "GLF-2601-0482", "GLF-2601-0483", "GLF-2601-0485", "GLF-2601-0487",
        "GLF-2601-0488", "GLF-2601-0490", "GLF-2601-0491", "GLF-2601-0492",
        "GLF-2601-0493", "GLF-2601-0494", "GLF-2601-0495", "GLF-2601-0497",
        "GLF-2601-0498", "GLF-2601-0499", "GLF-2601-0500", "GLF-2601-0502",
        "GLF-2601-0503", "GLF-2601-0505", "GLF-2601-0518"
    ]
    
    return update_multiple_invoices(invoice_list, commit=commit)


if __name__ == "__main__":
    # Test with one invoice first
    result = update_item_wise_tax_detail("GLF-2601-0549")
    print("\n" + "="*100)
    print("TEST RESULT")
    print("="*100)
    print(json.dumps(result, indent=2))
    print("\nTo update all invoices, run:")
    print("  bench --site hkmerp.in execute hkm.cursor.update_item_wise_tax_detail.update_golden_lotus_january_2026 --kwargs \"{'commit': True}\"")
