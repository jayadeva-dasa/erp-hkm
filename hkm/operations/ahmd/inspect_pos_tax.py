import frappe

def inspect_pos_invoice_tax_source():
    """Inspect where the tax configuration comes from for POS invoices"""
    
    # Get one of the problematic invoices
    invoice_name = "HKMA-PS2603472"
    
    print(f"\n=== Inspecting {invoice_name} ===")
    
    invoice = frappe.get_doc("POS Invoice", invoice_name)
    
    print(f"\nPOS Profile: {invoice.pos_profile}")
    print(f"Company: {invoice.company}")
    print(f"Customer: {invoice.customer}")
    
    # Get POS Profile
    if invoice.pos_profile:
        pos_profile = frappe.get_doc("POS Profile", invoice.pos_profile)
        print(f"\n=== POS Profile Configuration ===")
        print(f"Taxes and Charges: {pos_profile.get('taxes_and_charges')}")
        print(f"Tax Category: {pos_profile.get('tax_category')}")
        
        if pos_profile.get('applicable_for_company'):
            print(f"Company: {pos_profile.applicable_for_company}")
    
    # Check if there's a sales taxes and charges template
    print(f"\n=== Invoice Tax Template ===")
    print(f"Taxes and Charges: {invoice.get('taxes_and_charges')}")
    print(f"Tax Category: {invoice.get('tax_category')}")
    
    # Inspect each tax row
    print(f"\n=== Tax Row Details ===")
    for idx, tax in enumerate(invoice.taxes, 1):
        print(f"\nTax Row #{idx}:")
        print(f"  Account Head: {tax.account_head}")
        print(f"  Charge Type: {tax.charge_type}")
        print(f"  Rate: {tax.rate}")
        print(f"  Tax Amount: {tax.tax_amount}")
        print(f"  Tax Amount After Discount: {tax.tax_amount_after_discount_amount}")
        print(f"  Item Wise Tax Detail: {tax.item_wise_tax_detail}")
        print(f"  Included in Print Rate: {tax.included_in_print_rate}")
    
    # Check item tax templates
    print(f"\n=== Item Tax Templates ===")
    for item in invoice.items:
        print(f"\nItem: {item.item_code}")
        print(f"  Item Tax Template: {item.item_tax_template}")
        print(f"  Item Tax Rate: {item.item_tax_rate}")
        print(f"  GST HSN Code: {item.gst_hsn_code}")
        
        if item.item_tax_template:
            item_tax_template = frappe.get_doc("Item Tax Template", item.item_tax_template)
            print(f"  Tax Template Taxes:")
            for tax in item_tax_template.taxes:
                print(f"    - {tax.tax_type}: {tax.tax_rate}%")
    
    # Check if taxes_and_charges template exists
    if invoice.get('taxes_and_charges'):
        print(f"\n=== Sales Taxes and Charges Template ===")
        template = frappe.get_doc("Sales Taxes and Charges Template", invoice.taxes_and_charges)
        print(f"Template: {template.name}")
        print(f"Company: {template.company}")
        print(f"Taxes:")
        for tax in template.taxes:
            print(f"  - {tax.account_head}: Type={tax.charge_type}, Rate={tax.rate}")
