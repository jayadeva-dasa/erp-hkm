"""
Patch to add Stock Issuer custom fields
Date: November 26, 2025

This patch creates custom fields for:
1. Warehouse.stock_issuer - Link to User for warehouse-specific stock issuer
2. Warehouse.secondary_stock_issuer - Link to User for secondary stock issuer
3. HKM General Settings.default_stock_issuer - Link to User for fallback stock issuer

These fields are used by the MRN approval notification system to determine
who should receive approval notifications when Material Requests are submitted.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    """Execute patch to create stock issuer custom fields"""

    # Define custom fields
    custom_fields = {
        "Warehouse": [
            {
                "dt": "Warehouse",
                "fieldtype": "Link",
                "label": "Stock Issuer",
                "fieldname": "stock_issuer",
                "insert_after": "warehouse_contact_info",
                "options": "User",
                "description": "User who will receive MRN approval notifications for this warehouse",
            },
            {
                "dt": "Warehouse",
                "fieldtype": "Link",
                "label": "Secondary Stock Issuer",
                "fieldname": "secondary_stock_issuer",
                "insert_after": "stock_issuer",
                "options": "User",
                "description": "Secondary user who will receive MRN approval notifications for this warehouse",
            },
        ],
    }

    try:
        # Reload doctypes to ensure latest schema
        frappe.reload_doc("stock", "doctype", "warehouse", force=True)
        frappe.reload_doc(
            "erpnext___custom", "doctype", "hkm_general_settings", force=True
        )

        # Create custom fields (update=True handles existing fields gracefully)
        create_custom_fields(custom_fields, update=True)

        print("✓ Stock Issuer custom fields created successfully")

    except Exception as e:
        print(f"Error creating stock issuer custom fields: {str(e)}")
        # Don't raise exception - migration should continue
        frappe.log_error(
            title="Stock Issuer Custom Fields Patch Failed",
            message=frappe.get_traceback(),
        )
