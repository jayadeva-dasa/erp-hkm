import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    doctype = "POS Closing Entry"
    custom_fields = {
        doctype: [
            dict(
                fieldname="pos_sales_invoices_item",
                label="POS Sales Invoices Item",
                fieldtype="Text Editor",
                insert_after="sales_invoices",
                allow_on_submit=1,
                read_only=1,
                print_hide=1,
            ),
        ],
    }
    create_custom_fields(custom_fields, update=True)

    # Ensure schema and cache are synced so the new column exists and meta is fresh.
    # Without this, the Custom Field can exist in the list but the table may lack the
    # column (e.g. if the field was created earlier and updatedb was skipped), causing
    # "no such field" when setting the value.
    # frappe.clear_cache(doctype=doctype)
    # frappe.db.updatedb(doctype)