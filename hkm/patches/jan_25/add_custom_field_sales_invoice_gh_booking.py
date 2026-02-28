import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
def execute():

    custom_fields = {
        "Sales Invoice": [
            dict(
                fieldname="gh_room_booking",
                label="GH Room Booking",
                fieldtype="Link",
                options="GH Room Booking",
                insert_after="default_sales_income_account",
                read_only=1,
                allow_on_submit=1,
            ),
        ],
    }
    create_custom_fields(custom_fields , update=True)