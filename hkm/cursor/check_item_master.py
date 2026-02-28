import frappe

def check_item_tax_template():
    """Check item tax templates for the items in question"""
    
    items = ['N-FDCR-0008', 'BKRY-0073', 'N-BKRY-0015', 'BKRY-0017']
    
    print("\n" + "="*100)
    print("Item Master Analysis")
    print("="*100)
    
    for item_code in items:
        item = frappe.get_doc("Item", item_code)
        
        print(f"\nItem: {item.name}")
        print(f"  HSN Code: {item.gst_hsn_code or 'Not Set'}")
        
        # Check for nil/exempt fields (these might have different field names)
        if hasattr(item, 'is_nil_exempt'):
            print(f"  Is Nil Exempt: {item.is_nil_exempt}")
        if hasattr(item, 'is_non_gst'):
            print(f"  Is Non GST: {item.is_non_gst}")
        
        # Check item tax templates
        if hasattr(item, 'taxes') and item.taxes:
            print(f"  Item Tax Templates:")
            for tax in item.taxes:
                print(f"    - Template: {tax.item_tax_template}")
                
                # Get template details
                try:
                    template = frappe.get_doc("Item Tax Template", tax.item_tax_template)
                    print(f"      Taxes:")
                    for t in template.taxes:
                        print(f"        {t.tax_type}: {t.tax_rate}%")
                except Exception as e:
                    print(f"      Error fetching template: {e}")
        else:
            print(f"  No Item Tax Templates defined")
        
        # Check standard tax rates
        sql = """
            SELECT 
                standard_rate,
                tax_rate_gst  
            FROM 
                `tabItem`
            WHERE 
                name = %s
        """
        rates = frappe.db.sql(sql, (item_code,), as_dict=1)
        if rates:
            print(f"  Standard Tax Rates: {rates[0]}")
    
    return True

if __name__ == "__main__":
    check_item_tax_template()
