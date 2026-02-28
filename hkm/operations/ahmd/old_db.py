import mysql.connector

import frappe
def run_query(query):
    mydb = mysql.connector.connect(
        host="hkmtapf.mysql.database.azure.com",
        user="hkmtapf",
        database="ebdb",
        password="My123password",
    )
    cursor = mydb.cursor(dictionary=True)
    cursor.execute(query)
    return cursor.fetchall()
def correct_tax_details():
    import frappe

    doc = frappe.get_doc("POS Invoice", "HKMA-PS2603472")

    # --- Step 1: tax_row -> gst_tax_type (READ ONLY) ---
    tax_type_map = {t.name: t.gst_tax_type for t in doc.taxes}

    collected = {"sgst": 0.0, "cgst": 0.0, "igst": 0.0}

    # --- Step 2: collect rounding from EXEMPT rows ---
    for row in doc.item_wise_tax_details:
        if row.rate == 0 and abs(row.amount) > 0:
            gst_type = tax_type_map.get(row.tax_row)
            if gst_type in collected:
                collected[gst_type] += row.amount
                frappe.db.set_value(
                    "Item Wise Tax Detail",
                    row.name,
                    "amount",
                    0
                )

    # --- Step 3: push rounding into NON-EXEMPT rows ---
    for row in reversed(doc.item_wise_tax_details):
        if row.rate <= 0:
            continue

        gst_type = tax_type_map.get(row.tax_row)
        if gst_type in collected and abs(collected[gst_type]) > 0:
            frappe.db.set_value(
                "Item Wise Tax Detail",
                row.name,
                "amount",
                row.amount + collected[gst_type]
            )
            collected[gst_type] = 0

    # --- Step 4: safety check ---
    for gst_type, amt in collected.items():
        if abs(amt) > 0.0001:
            frappe.throw(f"Unabsorbed rounding amount for {gst_type}: {amt}")

    # --- Step 5: commit explicitly ---
    frappe.db.commit()

    return "Item-wise tax rounding corrected successfully"




def check_tax_details():
    pos = "HKMA-PS2603472"
    
    doc = frappe.get_doc("POS Invoice", pos)
    data = doc.as_dict()
    # print(data)
    print(data.get("item_wise_tax_details"))
    print(data.get("taxes"))


def close_pos():
    doc = frappe.get_doc("POS Closing Entry", "POS-CLO-2026-00335")
    
    # Print all POS invoices to identify which ones are being merged
    print("\n=== POS Invoices in Closing Entry ===")
    print(f"Total invoices: {len(doc.pos_invoices)}")
    
    for invoice_ref in doc.pos_invoices:
        print(f"\nInvoice: {invoice_ref.pos_invoice}")
        
        # Get each POS Invoice and check its taxes
        pos_inv = frappe.get_doc("POS Invoice", invoice_ref.pos_invoice)
        print(f"  Customer: {pos_inv.customer}")
        print(f"  Total: {pos_inv.grand_total}")
        print(f"  Items: {len(pos_inv.items)}")
        
        # Check taxes for problematic configuration
        if pos_inv.taxes:
            print(f"  Taxes: {len(pos_inv.taxes)} rows")
            for idx, tax in enumerate(pos_inv.taxes, 1):
                print(f"    Tax Row #{idx}: {tax.account_head}")
                print(f"      - Charge Type: {tax.charge_type}")
                print(f"      - Rate: {tax.rate}")
                print(f"      - Amount: {tax.tax_amount}")
                print(f"      - Item Wise Tax Detail: {tax.item_wise_tax_detail}")
                
                # Flag potential issues
                if tax.charge_type == "Actual" and tax.item_wise_tax_detail:
                    print(f"      ⚠️  WARNING: Charge Type 'Actual' with item_wise_tax_detail!")
                # Also flag when rate is 0 but amount exists
                if (tax.rate == 0 or not tax.rate) and tax.tax_amount:
                    print(f"      ⚠️  WARNING: Rate is 0 but tax amount is {tax.tax_amount}!")
        
        print("  Items:")
        for item in pos_inv.items:
            print(f"    - {item.item_code} ({item.item_name}): Qty {item.qty}, Amount {item.amount}")
        print("---")
    
    # print("\n=== Starting Submit ===")
    # print("\n⚠️  APPLYING WORKAROUND: Temporarily disabling GST item-wise tax validation")
    
    # # Monkey-patch the India Compliance validation to skip the Actual charge type check
    # from india_compliance.gst_india.overrides import transaction
    
    # original_validate_item_wise_tax = transaction.validate_item_wise_tax_detail
    
    # def bypass_validate_item_wise_tax(doc):
    #     """Skip validation for consolidated POS invoices with Actual charge type"""
    #     if hasattr(doc, 'is_consolidated') and doc.is_consolidated:
    #         print("  ✓ Skipping GST item-wise tax validation for consolidated invoice")
    #         return
    #     # For non-consolidated, run original validation
    #     return original_validate_item_wise_tax(doc)
    
    # # Replace the function temporarily
    # transaction.validate_item_wise_tax_detail = bypass_validate_item_wise_tax
    
    # try:
    #     doc.submit()
    #     print("✓ Successfully submitted POS Closing Entry")
    # except Exception as e:
    #     print(f"\n❌ ERROR during submit: {str(e)}")
    #     import traceback
    #     print(traceback.format_exc())
    #     raise
    # finally:
    #     # Restore original function
    #     transaction.validate_item_wise_tax_detail = original_validate_item_wise_tax
    #     print("\n✓ Restored original validation function")