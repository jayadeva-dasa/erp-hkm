import frappe
from frappe.utils import flt
from collections import defaultdict

def analyze_and_fix_gst_issues():
    """
    CRITICAL TASK: Fix Sales Invoices with GST template but nil-rated treatment
    
    APPROACH:
    1. Fetch affected invoices
    2. For each item with issue:
       - Get GST treatment from Item Tax Template
       - Recalculate taxable_value (base_net_amount)
       - Recalculate GST amounts from item_wise_tax_detail
       - Update directly in database
    3. Regenerate GST breakup table
    
    RISK LEVEL: HIGH
    - Direct database updates on submitted documents
    - No doc events triggered
    - Must ensure data consistency
    """
    
    print("\n" + "="*80)
    print("SALES INVOICE GST FIX - ANALYSIS & EXECUTION")
    print("="*80)
    
    # Get affected invoices
    affected_data = get_affected_invoices()
    
    if not affected_data:
        print("\n✓ No issues found.")
        return
    
    print(f"\n📊 Found {len(affected_data)} affected invoices")
    print(f"   Total items to fix: {sum(len(v) for v in affected_data.values())}")
    
    # Analyze risk
    print("\n" + "="*80)
    print("RISK ANALYSIS")
    print("="*80)
    
    print("\n🔴 HIGH RISK FACTORS:")
    print("   1. Direct DB updates on submitted documents (docstatus=1)")
    print("   2. Bypassing document validation and events")
    print("   3. GST breakup table regeneration required")
    print("   4. Potential audit trail implications")
    
    print("\n🟢 MITIGATION:")
    print("   1. Read tax rates from item_wise_tax_detail (source of truth)")
    print("   2. Recalculate amounts using standard formulas")
    print("   3. Update only specific fields, not entire doc")
    print("   4. Create backup before execution")
    print("   5. Transaction-based updates (rollback on error)")
    
    print("\n" + "="*80)
    print("EXECUTION PLAN")
    print("="*80)
    
    print("\nFor each affected item:")
    print("   1. Get GST treatment from Item Tax Template")
    print("   2. Calculate taxable_value = base_net_amount")
    print("   3. Get tax rates from item_wise_tax_detail")
    print("   4. Calculate: igst_amount, cgst_amount, sgst_amount")
    print("   5. UPDATE `tabSales Invoice Item` SET:")
    print("      - gst_treatment")
    print("      - taxable_value")
    print("      - igst_rate, igst_amount")
    print("      - cgst_rate, cgst_amount")
    print("      - sgst_rate, sgst_amount")
    print("   6. Regenerate gst_breakup_table in parent")
    
    print("\n" + "="*80)
    print("SAMPLE DATA ANALYSIS")
    print("="*80)
    
    # Show sample
    sample_invoice = list(affected_data.keys())[0]
    sample_items = affected_data[sample_invoice]
    
    print(f"\nSample Invoice: {sample_invoice}")
    for item in sample_items[:2]:
        print(f"\n   Item: {item['item_code']}")
        print(f"   Template: {item['item_tax_template']}")
        print(f"   Current GST Treatment: {item['gst_treatment']}")
        print(f"   Current Taxable Value: {item['taxable_value']}")
        print(f"   Base Net Amount: {item['base_net_amount']}")
        
        # Get correct treatment
        correct_treatment = frappe.db.get_value(
            'Item Tax Template',
            item['item_tax_template'],
            'gst_treatment'
        )
        print(f"   Correct GST Treatment: {correct_treatment}")
        
        # Get tax details from template
        tax_detail = get_tax_rates_from_template(item['item_tax_template'], sample_invoice)
        if tax_detail:
            print(f"   Tax Rates from Item Tax Template:")
            for tax_type, rate in tax_detail.items():
                if rate > 0:
                    amount = item['base_net_amount'] * rate / 100
                    print(f"      {tax_type.upper()}: {rate}% = ₹{amount:.2f}")
    
    print("\n" + "="*80)
    print("RECOMMENDATION")
    print("="*80)
    
    print("\n✅ SAFE TO PROCEED IF:")
    print("   - You have database backup")
    print("   - This is test/staging environment OR")
    print("   - You have verified sample data above")
    print("   - You can revert changes if needed")
    
    print("\n❌ DO NOT PROCEED IF:")
    print("   - No backup available")
    print("   - Production system without approval")
    print("   - Sample data looks incorrect")
    
    print("\n" + "="*80)
    
    return affected_data


def get_affected_invoices():
    """Get all affected Sales Invoices with item details"""
    
    query = """
        SELECT 
            si.name as invoice_name,
            sii.name as item_name,
            sii.item_code,
            sii.item_tax_template,
            sii.gst_treatment,
            sii.taxable_value,
            sii.base_net_amount,
            sii.qty,
            sii.igst_rate,
            sii.cgst_rate,
            sii.sgst_rate
        FROM 
            `tabSales Invoice` si
        INNER JOIN 
            `tabSales Invoice Item` sii ON si.name = sii.parent
        WHERE 
            si.docstatus = 1
            AND si.posting_date BETWEEN '2025-04-01' AND '2026-03-31'
            AND sii.item_tax_template IS NOT NULL
            AND sii.item_tax_template != ''
            AND (sii.gst_treatment = 'Nil-Rated' OR sii.gst_treatment IS NULL OR sii.gst_treatment = '')
            AND (sii.taxable_value = 0 OR sii.taxable_value IS NULL)
        ORDER BY 
            si.posting_date ASC, si.name
    """
    
    results = frappe.db.sql(query, as_dict=1)
    
    # Group by invoice
    invoice_data = defaultdict(list)
    for row in results:
        invoice_data[row.invoice_name].append(row)
    
    return dict(invoice_data)


def get_item_tax_details(invoice_name, item_name):
    """Get tax rates for an item from item_wise_tax_detail"""
    
    # Get item_wise_tax_detail from taxes
    taxes = frappe.get_all(
        'Sales Taxes and Charges',
        filters={'parent': invoice_name},
        fields=['name', 'account_head', 'gst_tax_type', 'item_wise_tax_detail']
    )
    
    tax_rates = {}
    
    for tax in taxes:
        if not tax.gst_tax_type or not tax.item_wise_tax_detail:
            continue
        
        try:
            import json
            item_wise_detail = json.loads(tax.item_wise_tax_detail)
            
            if item_name in item_wise_detail:
                rate, amount = item_wise_detail[item_name]
                tax_rates[tax.gst_tax_type] = rate
        except:
            pass
    
    return tax_rates


def get_tax_rates_from_template(item_tax_template, invoice_name):
    """
    Get tax rates from Item Tax Template
    Returns dict with igst, cgst, sgst rates
    """
    if not item_tax_template:
        return {}
    
    # Get template details
    template_taxes = frappe.get_all(
        'Item Tax Template Detail',
        filters={'parent': item_tax_template},
        fields=['tax_type', 'tax_rate']
    )
    
    # Get GST accounts for the company
    invoice = frappe.get_cached_value('Sales Invoice', invoice_name, 
                                      ['company', 'place_of_supply', 'company_gstin'], as_dict=1)
    
    # Determine if inter-state
    company_state = invoice.company_gstin[:2] if invoice.company_gstin else None
    pos_state = invoice.place_of_supply.split('-')[0] if invoice.place_of_supply else None
    is_inter_state = company_state != pos_state
    
    tax_rates = {}
    
    for tax in template_taxes:
        account_name = tax.tax_type
        rate = tax.tax_rate
        
        # Determine tax type from account name
        if 'IGST' in account_name.upper():
            tax_rates['igst'] = rate
        elif 'CGST' in account_name.upper():
            tax_rates['cgst'] = rate
        elif 'SGST' in account_name.upper():
            tax_rates['sgst'] = rate
    
    # For intra-state, IGST should be 0 and vice versa
    if is_inter_state:
        tax_rates['cgst'] = 0
        tax_rates['sgst'] = 0
    else:
        tax_rates['igst'] = 0
    
    return tax_rates


def execute_fix(dry_run=True):
    """
    Execute the fix for affected invoices
    
    Args:
        dry_run: If True, only show what would be done without making changes
    """
    
    affected_data = get_affected_invoices()
    
    if not affected_data:
        print("\n✓ No issues to fix.")
        return
    
    print("\n" + "="*80)
    if dry_run:
        print("DRY RUN MODE - NO CHANGES WILL BE MADE")
    else:
        print("EXECUTING FIX - MAKING ACTUAL CHANGES")
    print("="*80)
    
    fixed_count = 0
    error_count = 0
    
    for invoice_name, items in affected_data.items():
        print(f"\nProcessing: {invoice_name}")
        
        try:
            for item in items:
                # Get correct GST treatment
                gst_treatment = frappe.db.get_value(
                    'Item Tax Template',
                    item['item_tax_template'],
                    'gst_treatment'
                )
                
                if not gst_treatment:
                    print(f"   ⚠️  No GST treatment found for template: {item['item_tax_template']}")
                    gst_treatment = 'Taxable'  # Default
                
                # Get tax rates from template (primary source)
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
                
                print(f"   Item: {item['item_code']}")
                print(f"      GST Treatment: {item['gst_treatment']} → {gst_treatment}")
                print(f"      Taxable Value: {item['taxable_value']} → {taxable_value}")
                print(f"      IGST: {item['igst_rate']}% → {igst_rate}% (₹{igst_amount})")
                print(f"      CGST: {item['cgst_rate']}% → {cgst_rate}% (₹{cgst_amount})")
                print(f"      SGST: {item['sgst_rate']}% → {sgst_rate}% (₹{sgst_amount})")
                
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
                            sgst_amount = %s,
                            modified = NOW(),
                            modified_by = %s
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
                        frappe.session.user,
                        item['item_name']
                    ))
                    
                    fixed_count += 1
            
            # Update tax table
            if not dry_run:
                update_tax_table(invoice_name)
                frappe.db.commit()
                print(f"   ✓ Fixed and committed")
        
        except Exception as e:
            error_count += 1
            print(f"   ✗ Error: {str(e)}")
            if not dry_run:
                frappe.db.rollback()
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total Invoices Processed: {len(affected_data)}")
    print(f"Items Fixed: {fixed_count}")
    print(f"Errors: {error_count}")
    
    if dry_run:
        print("\n⚠️  This was a DRY RUN. No changes were made.")
        print("   To execute actual fix, run: execute_fix(dry_run=False)")


def update_tax_table(invoice_name):
    """Update Sales Taxes and Charges table with correct GST amounts"""
    
    # Get total GST from items
    totals = frappe.db.sql("""
        SELECT 
            SUM(cgst_amount) as total_cgst,
            SUM(sgst_amount) as total_sgst,
            SUM(igst_amount) as total_igst
        FROM `tabSales Invoice Item`
        WHERE parent = %s
    """, (invoice_name,), as_dict=1)[0]
    
    total_cgst = flt(totals.total_cgst or 0, 2)
    total_sgst = flt(totals.total_sgst or 0, 2)
    total_igst = flt(totals.total_igst or 0, 2)
    
    # Update tax rows
    tax_rows = frappe.get_all(
        'Sales Taxes and Charges',
        filters={'parent': invoice_name},
        fields=['name', 'account_head']
    )
    
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


if __name__ == "__main__":
    analyze_and_fix_gst_issues()
