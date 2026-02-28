import frappe
from frappe.utils import getdate
from collections import defaultdict

def analyze_sales_invoice_gst_issues():
    """
    Analyze Sales Invoices with GST template but nil-rated treatment in FY 2025-26
    """
    
    # FY 2025-26: April 1, 2025 to March 31, 2026
    start_date = '2025-04-01'
    end_date = '2026-03-31'
    
    print("\n" + "="*80)
    print("SALES INVOICE GST ISSUE ANALYSIS - FY 2025-26")
    print("="*80)
    
    # Query to find affected Sales Invoices
    query = """
        SELECT 
            si.name,
            si.posting_date,
            si.customer,
            sii.item_code,
            sii.item_name,
            sii.item_tax_template,
            sii.gst_treatment,
            sii.qty,
            sii.rate,
            sii.amount,
            sii.taxable_value,
            sii.igst_rate,
            sii.igst_amount,
            sii.cgst_rate,
            sii.cgst_amount,
            sii.sgst_rate,
            sii.sgst_amount
        FROM 
            `tabSales Invoice` si
        INNER JOIN 
            `tabSales Invoice Item` sii ON si.name = sii.parent
        WHERE 
            si.docstatus = 1
            AND si.posting_date BETWEEN %s AND %s
            AND sii.item_tax_template IS NOT NULL
            AND sii.item_tax_template != ''
            AND (sii.gst_treatment = 'Nil-Rated' OR sii.gst_treatment IS NULL OR sii.gst_treatment = '')
            AND (sii.taxable_value = 0 OR sii.taxable_value IS NULL)
        ORDER BY 
            si.posting_date ASC
    """
    
    results = frappe.db.sql(query, (start_date, end_date), as_dict=1)
    
    if not results:
        print("\n✓ No issues found. All Sales Invoices have correct GST treatment.")
        return
    
    # Analyze patterns
    affected_invoices = set()
    date_wise = defaultdict(int)
    month_wise = defaultdict(int)
    template_wise = defaultdict(int)
    item_wise = defaultdict(int)
    
    for row in results:
        affected_invoices.add(row.name)
        posting_date = getdate(row.posting_date)
        date_wise[str(posting_date)] += 1
        month_key = posting_date.strftime('%Y-%m')
        month_wise[month_key] += 1
        template_wise[row.item_tax_template] += 1
        item_wise[row.item_code] += 1
    
    # Summary
    print(f"\n📊 SUMMARY")
    print(f"   Total Affected Sales Invoices: {len(affected_invoices)}")
    print(f"   Total Affected Line Items: {len(results)}")
    
    # Date Range
    first_date = min(date_wise.keys())
    last_date = max(date_wise.keys())
    print(f"\n📅 AFFECTED PERIOD")
    print(f"   From: {first_date}")
    print(f"   To: {last_date}")
    
    # Month-wise breakdown
    print(f"\n📆 MONTH-WISE BREAKDOWN")
    for month in sorted(month_wise.keys()):
        print(f"   {month}: {month_wise[month]} items")
    
    # Top GST Templates with issues
    print(f"\n🏷️  TOP GST TEMPLATES WITH ISSUES")
    sorted_templates = sorted(template_wise.items(), key=lambda x: x[1], reverse=True)
    for template, count in sorted_templates[:10]:
        print(f"   {template}: {count} items")
    
    # Top Items with issues
    print(f"\n📦 TOP ITEMS WITH ISSUES")
    sorted_items = sorted(item_wise.items(), key=lambda x: x[1], reverse=True)
    for item, count in sorted_items[:10]:
        print(f"   {item}: {count} occurrences")
    
    # Sample affected invoices
    print(f"\n📋 SAMPLE AFFECTED INVOICES (First 10)")
    sample_invoices = sorted(list(affected_invoices))[:10]
    for inv in sample_invoices:
        inv_date = frappe.db.get_value('Sales Invoice', inv, 'posting_date')
        print(f"   {inv} - {inv_date}")
    
    # Root cause analysis
    print(f"\n🔍 ROOT CAUSE ANALYSIS")
    
    # Check if it's a specific template issue
    if len(template_wise) == 1:
        print(f"   ⚠️  Single Template Issue: All cases have template '{list(template_wise.keys())[0]}'")
    elif len(template_wise) <= 3:
        print(f"   ⚠️  Limited Templates: Only {len(template_wise)} templates affected")
    else:
        print(f"   ⚠️  Multiple Templates: {len(template_wise)} different templates affected")
    
    # Check if it's date-specific
    date_span = (getdate(last_date) - getdate(first_date)).days
    if date_span <= 7:
        print(f"   ⚠️  Short Duration: All issues within {date_span} days")
    elif date_span <= 30:
        print(f"   ⚠️  Monthly Issue: Issues span {date_span} days")
    else:
        print(f"   ⚠️  Extended Period: Issues span {date_span} days")
    
    # Check concentration
    peak_month = max(month_wise.items(), key=lambda x: x[1])
    if peak_month[1] > len(results) * 0.5:
        print(f"   ⚠️  Concentrated in {peak_month[0]}: {peak_month[1]} items ({peak_month[1]*100//len(results)}%)")
    
    print("\n" + "="*80)
    print("CONCLUSION")
    print("="*80)
    print("Issue: Sales Invoice items have GST templates assigned but GST treatment")
    print("       is 'Nil-Rated', causing taxable_value and GST amounts to be zero.")
    print(f"\nPeriod: {first_date} to {last_date}")
    print(f"Impact: {len(affected_invoices)} invoices, {len(results)} line items")
    
    if len(template_wise) <= 3:
        print(f"\nLikely Cause: Template configuration issue with:")
        for template in sorted_templates[:3]:
            print(f"              - {template[0]}")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    analyze_sales_invoice_gst_issues()
