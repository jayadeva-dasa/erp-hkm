import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
def execute():

    custom_fields = {
        "Purchase Invoice": [
            {
                "fieldname": "hkm_tds_section",
                "label": "TDS Section",
                "fieldtype": "Section Break",
                "tab_break": 1,
                "insert_after": "net_total",
            },
            dict(
                fieldname="tds_taxable_amount",
                label="TDS Taxable Amount",
                fieldtype="Currency",
                insert_after="hkm_tds_section",
                allow_on_submit=1,
            ),
            dict(
                fieldname="tds_deduction_amount",
                label="TDS Deduction Amount",
                fieldtype="Currency",
                insert_after="tds_taxable_amount",
                allow_on_submit=1,
            ),
            dict(
                fieldname="tds_percentage",
                label="TDS Percentage",
                fieldtype="Float",
                insert_after="tds_deduction_amount",
                allow_on_submit=1,
            ),
        ],
        "Journal Entry": [
            {
                "fieldname": "hkm_tds_section",
                "label": "TDS Section",
                "fieldtype": "Section Break",
                "tab_break": 1,
                "insert_after": "accounts",
            },
            dict(
                fieldname="tds_taxable_amount",
                label="TDS Taxable Amount",
                fieldtype="Currency",
                insert_after="hkm_tds_section",
                allow_on_submit=1,
            ),
            dict(
                fieldname="tds_deduction_amount",
                label="TDS Deduction Amount",
                fieldtype="Currency",
                insert_after="tds_taxable_amount",
                allow_on_submit=1,
            ),
            dict(
                fieldname="tds_percentage",
                label="TDS Percentage",
                fieldtype="Float",
                insert_after="tds_deduction_amount",
                allow_on_submit=1,
            ),
        ],
    }
    create_custom_fields(custom_fields, update=True)