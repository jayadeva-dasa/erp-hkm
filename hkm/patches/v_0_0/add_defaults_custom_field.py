import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    custom_fields = {
        "Stock Entry": [
            dict(
                fieldname="default_difference_account",
                label="Default Difference Account",
                fieldtype="Link",
                options="Account",
                insert_after="source_address_display",
                translatable=0,
                mandatory_depends_on="eval:doc.purpose=='Material Issue' || doc.purpose=='Material Receipt'",
            ),
            dict(
                fieldname="cost_center",
                label="Cost Center",
                fieldtype="Link",
                options="Cost Center",
                reqd=1,
                insert_after="project",
                translatable=0,
            ),
        ],
        "Purchase Invoice": [
            dict(
                fieldname="default_difference_account",
                label="Default Difference Account",
                fieldtype="Link",
                options="Account",
                insert_after="items_section",
                translatable=0,
            ),
        ],
        "Sales Invoice": [
            dict(
                fieldname="default_sales_income_account",
                label="Default Sales Income Account",
                fieldtype="Link",
                options="Account",
                insert_after="items_section",
                translatable=0,
            ),
        ],
    }
    create_custom_fields(custom_fields)
