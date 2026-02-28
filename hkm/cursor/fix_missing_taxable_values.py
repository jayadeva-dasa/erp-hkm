"""
Fix items where taxable_value is 0 but amount > 0
Even for NIL rated or exempted items, taxable_value should equal amount
"""

import frappe

def analyze_missing_taxable_values(invoice_name):
    """
    Analyze items with missing taxable values in specific invoice
    """
    
    items = frappe.get_all("Sales Invoice Item",
                          filters={"parent": invoice_name},
                          fields=["name", "idx", "item_code", "amount", "taxable_value", 
                                 "cgst_amount", "sgst_amount", "igst_amount"],
                          order_by="idx")
    
    print(f"\n{'='*100}")
    print(f"INVOICE: {invoice_name}")
    print(f"{'='*100}\n")
    
    missing_count = 0
    items_to_fix = []
    
    for item in items:
        if item.amount > 0 and (not item.taxable_value or item.taxable_value == 0):
            missing_count += 1
            items_to_fix.append(item)
            total_tax = item.cgst_amount + item.sgst_amount + item.igst_amount
            print(f"❌ {item.idx}. {item.item_code}")
            print(f"   Amount: ₹{item.amount:,.2f}")
            print(f"   Taxable Value: ₹{item.taxable_value or 0:,.2f} (MISSING!)")
            print(f"   Total Tax: ₹{total_tax:,.2f}")
            print()
    
    if missing_count == 0:
        print("✅ All items have taxable values populated!\n")
    else:
        print(f"⚠️  Found {missing_count} items with missing taxable values\n")
    
    return items_to_fix


def fix_missing_taxable_values(invoice_name, commit=False):
    """
    Fix items where taxable_value is missing but amount exists
    Set taxable_value = amount for all items
    """
    
    items_to_fix = analyze_missing_taxable_values(invoice_name)
    
    if not items_to_fix:
        return {"status": "nothing_to_fix"}
    
    print(f"{'='*100}")
    print(f"FIXING MISSING TAXABLE VALUES")
    print(f"{'='*100}\n")
    print(f"Commit Mode: {'ENABLED' if commit else 'DISABLED (dry run)'}\n")
    
    fixed_count = 0
    
    for item in items_to_fix:
        print(f"Fixing {item.item_code}: Setting taxable_value = ₹{item.amount:,.2f}")
        
        if commit:
            frappe.db.set_value("Sales Invoice Item", item.name, "taxable_value", item.amount)
        
        fixed_count += 1
    
    if commit:
        frappe.db.commit()
        print(f"\n✅ Fixed {fixed_count} items - Changes committed to database")
    else:
        print(f"\n⚠️  Dry run only - {fixed_count} items need fixing")
        print("   Run with commit=True to apply changes")
    
    return {
        "status": "success",
        "fixed_count": fixed_count,
        "committed": commit
    }


def fix_multiple_invoices(invoice_list, commit=False):
    """
    Fix missing taxable values for multiple invoices
    """
    
    print(f"\n{'='*100}")
    print(f"FIXING MISSING TAXABLE VALUES - MULTIPLE INVOICES")
    print(f"{'='*100}")
    print(f"Total Invoices: {len(invoice_list)}")
    print(f"Commit Mode: {'ENABLED' if commit else 'DISABLED (dry run)'}")
    print(f"{'='*100}\n")
    
    results = {
        "total": len(invoice_list),
        "fixed": 0,
        "nothing_to_fix": 0,
        "total_items_fixed": 0
    }
    
    for inv_name in invoice_list:
        result = fix_missing_taxable_values(inv_name, commit=commit)
        
        if result["status"] == "nothing_to_fix":
            results["nothing_to_fix"] += 1
        else:
            results["fixed"] += 1
            results["total_items_fixed"] += result["fixed_count"]
        
        print()
    
    print(f"{'='*100}")
    print(f"SUMMARY")
    print(f"{'='*100}")
    print(f"Total Invoices Processed: {results['total']}")
    print(f"  ✅ Fixed: {results['fixed']} invoices")
    print(f"  ⏭️  Nothing to Fix: {results['nothing_to_fix']} invoices")
    print(f"Total Items Fixed: {results['total_items_fixed']}")
    
    if commit:
        print(f"\n✅ All changes committed to database")
    else:
        print(f"\n⚠️  Dry run - No changes committed")
    
    print(f"{'='*100}\n")
    
    return results


if __name__ == "__main__":
    # Example: Check specific invoices
    invoices = ['TSFK-2601-0070', 'TSFK-2601-0067']
    
    for inv in invoices:
        analyze_missing_taxable_values(inv)
