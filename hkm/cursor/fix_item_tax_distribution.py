"""
Fix item-level tax distribution for invoices where taxes were added as "Actual" charges
instead of being properly calculated per item.

This script:
1. Identifies invoices with taxes at invoice level but not distributed to items
2. Calculates proportional tax distribution to items
3. Updates item-level tax fields (cgst_amount, sgst_amount, igst_amount, rates, taxable_value)
4. Does NOT resubmit - direct database update

Date: 2026-02-10
Author: Cursor AI
"""

import frappe
from frappe.utils import flt

def fix_item_tax_distribution(invoice_name, commit=False, print_details=False):
    """
    Fix tax distribution for a single invoice with validation
    
    Args:
        invoice_name: Sales Invoice name
        commit: If True, commits the changes to database
        print_details: If True, prints detailed output
    
    Returns:
        dict with fix status and details
    """
    import json
    
    if print_details:
        print("\n" + "="*80)
        print(f"Processing Invoice: {invoice_name}")
        print("="*80)
    
    # Get invoice
    invoice = frappe.get_doc("Sales Invoice", invoice_name)
    
    # Get invoice-level taxes
    cgst_total = 0
    sgst_total = 0
    igst_total = 0
    
    for tax in invoice.taxes:
        account_name = tax.account_head.lower()
        if 'cgst' in account_name:
            cgst_total += flt(tax.tax_amount)
        elif 'sgst' in account_name:
            sgst_total += flt(tax.tax_amount)
        elif 'igst' in account_name:
            igst_total += flt(tax.tax_amount)
    
    total_tax = cgst_total + sgst_total + igst_total
    
    if total_tax == 0:
        return {
            'status': 'skip',
            'invoice': invoice_name,
            'reason': 'No taxes found'
        }
    
    # Check if items already have taxes
    item_tax_total = sum(
        flt(item.cgst_amount) + flt(item.sgst_amount) + flt(item.igst_amount) 
        for item in invoice.items
    )
    
    if item_tax_total > 0:
        return {
            'status': 'skip',
            'invoice': invoice_name,
            'reason': 'Items already have tax amounts'
        }
    
    # Calculate net total from items
    net_total = sum(flt(item.amount) for item in invoice.items)
    
    if net_total == 0:
        return {
            'status': 'error',
            'invoice': invoice_name,
            'reason': 'Net total is 0'
        }
    
    if print_details:
        print(f"\nInvoice Taxes:")
        print(f"  CGST: ₹{cgst_total:.2f}")
        print(f"  SGST: ₹{sgst_total:.2f}")
        print(f"  IGST: ₹{igst_total:.2f}")
        print(f"  Total: ₹{total_tax:.2f}")
        print(f"\nDistributing to {len(invoice.items)} items...")
    
    # Distribute taxes proportionally to items
    items_updated = []
    
    # Item-wise tax detail for each tax row (for tax breakup display)
    cgst_item_wise = {}
    sgst_item_wise = {}
    igst_item_wise = {}
    
    # Track calculated totals for validation
    calc_cgst_total = 0
    calc_sgst_total = 0
    calc_igst_total = 0
    
    # Calculate tax for each item
    item_taxes = []
    
    for item in invoice.items:
        item_amount = flt(item.amount)
        proportion = item_amount / net_total
        
        # Calculate item's share of tax
        item_cgst = flt(cgst_total * proportion, 2)
        item_sgst = flt(sgst_total * proportion, 2)
        item_igst = flt(igst_total * proportion, 2)
        
        item_taxes.append({
            'item': item,
            'item_amount': item_amount,
            'cgst': item_cgst,
            'sgst': item_sgst,
            'igst': item_igst
        })
        
        calc_cgst_total += item_cgst
        calc_sgst_total += item_sgst
        calc_igst_total += item_igst
    
    # Adjust last item to absorb rounding differences
    if item_taxes:
        cgst_diff = cgst_total - calc_cgst_total
        sgst_diff = sgst_total - calc_sgst_total
        igst_diff = igst_total - calc_igst_total
        
        item_taxes[-1]['cgst'] = flt(item_taxes[-1]['cgst'] + cgst_diff, 2)
        item_taxes[-1]['sgst'] = flt(item_taxes[-1]['sgst'] + sgst_diff, 2)
        item_taxes[-1]['igst'] = flt(item_taxes[-1]['igst'] + igst_diff, 2)
        
        # Recalculate totals after adjustment
        calc_cgst_total = sum(flt(t['cgst']) for t in item_taxes)
        calc_sgst_total = sum(flt(t['sgst']) for t in item_taxes)
        calc_igst_total = sum(flt(t['igst']) for t in item_taxes)
    
    # Now process and update items
    for item_data in item_taxes:
        item = item_data['item']
        item_amount = item_data['item_amount']
        item_cgst = item_data['cgst']
        item_sgst = item_data['sgst']
        item_igst = item_data['igst']
        
        # Calculate tax rates (reverse calculate from amounts)
        if item_amount > 0:
            # Tax rate = (tax_amount / item_amount) * 100
            cgst_rate = flt((item_cgst / item_amount) * 100, 2) if item_cgst > 0 else 0
            sgst_rate = flt((item_sgst / item_amount) * 100, 2) if item_sgst > 0 else 0
            igst_rate = flt((item_igst / item_amount) * 100, 2) if item_igst > 0 else 0
        else:
            cgst_rate = sgst_rate = igst_rate = 0
        
        # Taxable value is the item amount (before tax)
        taxable_value = item_amount
        
        # Update item in database
        frappe.db.set_value('Sales Invoice Item', item.name, {
            'taxable_value': taxable_value,
            'cgst_amount': item_cgst,
            'sgst_amount': item_sgst,
            'igst_amount': item_igst,
            'cgst_rate': cgst_rate,
            'sgst_rate': sgst_rate,
            'igst_rate': igst_rate
        }, update_modified=False)
        
        # Build item_wise_tax_detail for each tax type
        if cgst_rate > 0:
            cgst_item_wise[item.item_code] = [cgst_rate, item_cgst]
        if sgst_rate > 0:
            sgst_item_wise[item.item_code] = [sgst_rate, item_sgst]
        if igst_rate > 0:
            igst_item_wise[item.item_code] = [igst_rate, item_igst]
        
        items_updated.append({
            'item_code': item.item_code,
            'item_name': item.name,
            'amount': item_amount,
            'taxable_value': taxable_value,
            'cgst': item_cgst,
            'sgst': item_sgst,
            'igst': item_igst,
            'cgst_rate': cgst_rate,
            'sgst_rate': sgst_rate,
            'igst_rate': igst_rate
        })
    
    # VALIDATION: Check if calculated totals match invoice-level taxes
    cgst_diff = abs(calc_cgst_total - cgst_total)
    sgst_diff = abs(calc_sgst_total - sgst_total)
    igst_diff = abs(calc_igst_total - igst_total)
    
    validation_passed = True
    validation_messages = []
    
    if print_details:
        print(f"\n" + "="*80)
        print("VALIDATION")
        print("="*80)
        print(f"\nInvoice-level Taxes:")
        print(f"  CGST: ₹{cgst_total:.2f}")
        print(f"  SGST: ₹{sgst_total:.2f}")
        print(f"  IGST: ₹{igst_total:.2f}")
        print(f"\nCalculated from Items:")
        print(f"  CGST: ₹{calc_cgst_total:.2f}")
        print(f"  SGST: ₹{calc_sgst_total:.2f}")
        print(f"  IGST: ₹{calc_igst_total:.2f}")
    
    # Allow small rounding differences (0.01)
    if cgst_diff > 0.01:
        validation_passed = False
        msg = f"CGST mismatch: ₹{cgst_diff:.2f}"
        validation_messages.append(msg)
        if print_details:
            print(f"\n⚠️  {msg}")
    
    if sgst_diff > 0.01:
        validation_passed = False
        msg = f"SGST mismatch: ₹{sgst_diff:.2f}"
        validation_messages.append(msg)
        if print_details:
            print(f"⚠️  {msg}")
    
    if igst_diff > 0.01:
        validation_passed = False
        msg = f"IGST mismatch: ₹{igst_diff:.2f}"
        validation_messages.append(msg)
        if print_details:
            print(f"⚠️  {msg}")
    
    if not validation_passed:
        frappe.db.rollback()
        if print_details:
            print("\n❌ VALIDATION FAILED - Changes rolled back")
        return {
            'status': 'error',
            'invoice': invoice_name,
            'reason': 'Validation failed: ' + ', '.join(validation_messages),
            'cgst_diff': cgst_diff,
            'sgst_diff': sgst_diff,
            'igst_diff': igst_diff
        }
    
    if print_details:
        print("\n✅ VALIDATION PASSED")
    
    # Update Sales Taxes and Charges table with item_wise_tax_detail
    for tax in invoice.taxes:
        account_name = tax.account_head.lower()
        
        if 'cgst' in account_name:
            item_wise_detail = json.dumps(cgst_item_wise)
            frappe.db.set_value('Sales Taxes and Charges', tax.name, {
                'item_wise_tax_detail': item_wise_detail
            }, update_modified=False)
        elif 'sgst' in account_name:
            item_wise_detail = json.dumps(sgst_item_wise)
            frappe.db.set_value('Sales Taxes and Charges', tax.name, {
                'item_wise_tax_detail': item_wise_detail
            }, update_modified=False)
        elif 'igst' in account_name:
            item_wise_detail = json.dumps(igst_item_wise)
            frappe.db.set_value('Sales Taxes and Charges', tax.name, {
                'item_wise_tax_detail': item_wise_detail
            }, update_modified=False)
    
    if commit:
        frappe.db.commit()
        if print_details:
            print("\n✅ Changes committed to database")
    else:
        if print_details:
            print("\n⚠️  Dry run - Changes not committed")
    
    return {
        'status': 'success',
        'invoice': invoice_name,
        'total_tax_distributed': total_tax,
        'cgst_total': cgst_total,
        'sgst_total': sgst_total,
        'igst_total': igst_total,
        'items_updated': len(items_updated),
        'validation_passed': validation_passed,
        'items': items_updated
    }


def fix_multiple_invoices(invoice_list, commit=False, print_details=True):
    """
    Fix tax distribution for multiple invoices
    
    Args:
        invoice_list: List of invoice names
        commit: If True, commits changes to database
        print_details: If True, prints details for each invoice
    
    Returns:
        Summary dict with results
    """
    
    results = {
        'success': [],
        'skipped': [],
        'errors': [],
        'validation_failed': []
    }
    
    print("\n" + "="*100)
    print(f"FIXING ITEM TAX DISTRIBUTION WITH VALIDATION - {len(invoice_list)} Invoices")
    print("="*100)
    print(f"Commit Mode: {'ENABLED - Changes will be saved' if commit else 'DISABLED - Dry run only'}")
    print(f"Validation: ENABLED - Totals must match within ₹0.01")
    print("="*100 + "\n")
    
    for i, invoice_name in enumerate(invoice_list, 1):
        try:
            result = fix_item_tax_distribution(invoice_name, commit=commit, print_details=False)
            
            if result['status'] == 'success':
                results['success'].append(result)
                if print_details:
                    print(f"{i:2d}. ✅ {invoice_name}")
                    print(f"     Tax Distributed: ₹{result['total_tax_distributed']:,.2f} "
                          f"(CGST: ₹{result['cgst_total']:,.2f} + SGST: ₹{result['sgst_total']:,.2f} "
                          f"+ IGST: ₹{result['igst_total']:,.2f})")
                    print(f"     Items Updated: {result['items_updated']} | Validation: ✅")
            
            elif result['status'] == 'skip':
                results['skipped'].append(result)
                if print_details:
                    print(f"{i:2d}. ⏭️  {invoice_name} - SKIPPED: {result['reason']}")
            
            elif result['status'] == 'error' and 'Validation failed' in result['reason']:
                results['validation_failed'].append(result)
                if print_details:
                    print(f"{i:2d}. ⚠️  {invoice_name} - VALIDATION FAILED: {result['reason']}")
            
            else:
                results['errors'].append(result)
                if print_details:
                    print(f"{i:2d}. ❌ {invoice_name} - ERROR: {result['reason']}")
        
        except Exception as e:
            error_result = {
                'status': 'error',
                'invoice': invoice_name,
                'reason': str(e)
            }
            results['errors'].append(error_result)
            if print_details:
                print(f"{i:2d}. ❌ {invoice_name} - EXCEPTION: {str(e)}")
    
    # Print summary
    print("\n" + "="*100)
    print("SUMMARY")
    print("="*100)
    print(f"Total Invoices Processed: {len(invoice_list)}")
    print(f"  ✅ Successfully Fixed: {len(results['success'])}")
    print(f"  ⏭️  Skipped: {len(results['skipped'])}")
    print(f"  ⚠️  Validation Failed: {len(results['validation_failed'])}")
    print(f"  ❌ Other Errors: {len(results['errors'])}")
    
    if results['success']:
        total_tax_fixed = sum(r['total_tax_distributed'] for r in results['success'])
        print(f"\nTotal Tax Amount Distributed: ₹{total_tax_fixed:,.2f}")
    
    if results['validation_failed']:
        print(f"\n⚠️  Validation Failed Invoices (need manual review):")
        for err in results['validation_failed']:
            print(f"  - {err['invoice']}: {err['reason']}")
    
    if results['errors']:
        print(f"\n❌ Other Errors:")
        for err in results['errors']:
            print(f"  - {err['invoice']}: {err['reason']}")
    
    print("\n" + "="*100)
    
    return results


def fix_golden_lotus_january_2026(commit=False):
    """
    Fix all affected Golden Lotus Foundation invoices for January 2026
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
    
    return fix_multiple_invoices(invoice_list, commit=commit, print_details=True)


# Quick test with one invoice
def test_single_invoice():
    """Test with a single invoice first"""
    result = fix_item_tax_distribution("GLF-2601-0549", commit=False)
    
    print("\n" + "="*100)
    print("TEST: Single Invoice Fix")
    print("="*100)
    print(f"Invoice: {result['invoice']}")
    print(f"Status: {result['status']}")
    
    if result['status'] == 'success':
        print(f"Total Tax: ₹{result['total_tax_distributed']:,.2f}")
        print(f"  CGST: ₹{result['cgst_total']:,.2f}")
        print(f"  SGST: ₹{result['sgst_total']:,.2f}")
        print(f"  IGST: ₹{result['igst_total']:,.2f}")
        print(f"\nItems Updated: {result['items_updated']}")
        print("\nFirst 3 items:")
        for item in result['items'][:3]:
            print(f"  {item['item_code']}")
            print(f"    Amount: ₹{item['amount']:,.2f}")
            print(f"    CGST: ₹{item['cgst']:,.2f} @ {item['cgst_rate']}%")
            print(f"    SGST: ₹{item['sgst']:,.2f} @ {item['sgst_rate']}%")
    
    return result


if __name__ == "__main__":
    # Run test first
    print("\n🧪 RUNNING TEST WITH SINGLE INVOICE...")
    test_single_invoice()
    
    print("\n\n" + "="*100)
    print("To fix all invoices, run:")
    print("  bench --site hkmerp.in execute hkm_jaipur.cursor.fix_item_tax_distribution.fix_golden_lotus_january_2026 --kwargs \"{'commit': False}\"")
    print("\nTo commit changes, run with commit=True:")
    print("  bench --site hkmerp.in execute hkm_jaipur.cursor.fix_item_tax_distribution.fix_golden_lotus_january_2026 --kwargs \"{'commit': True}\"")
    print("="*100)
