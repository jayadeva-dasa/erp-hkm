import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    custom_fields = {
        "User": [
            dict(
                fieldname="approval_scale",
                label="Approval Scale",
                fieldtype="Int",
                insert_after="purchase_order_whatsapp_approval",
                translatable=0,
                default=0,
            ),
        ],
    }
    create_custom_fields(custom_fields)
