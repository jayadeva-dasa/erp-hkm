import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    sites = ["hkmjerp.in"]
    if frappe.local.site not in sites:
        return
    add_custom_field_for_asset_category()
    add_custom_field_for_asset()


def add_custom_field_for_asset():
    # Make existing custodian field not mandatory
    if frappe.db.exists("Custom Field", {"dt": "Asset", "fieldname": "custodian"}):
        frappe.db.set_value(
            "Custom Field", {"dt": "Asset", "fieldname": "custodian"}, "reqd", 0
        )
    else:
        # If custom field doesn't exist, modify property setter
        if frappe.db.exists(
            "Property Setter",
            {"doc_type": "Asset", "field_name": "custodian", "property": "reqd"},
        ):
            frappe.db.set_value(
                "Property Setter",
                {"doc_type": "Asset", "field_name": "custodian", "property": "reqd"},
                "value",
                "0",
            )
        else:
            frappe.get_doc(
                {
                    "doctype": "Property Setter",
                    "doctype_or_field": "DocField",
                    "doc_type": "Asset",
                    "field_name": "custodian",
                    "property": "reqd",
                    "value": "0",
                    "property_type": "Check",
                }
            ).insert(ignore_permissions=True)

    # Define custom fields for Asset
    custom_fields = {
        "Asset": [
            dict(
                fieldname="custodian_department",
                label="Custodian Department",
                fieldtype="Link",
                options="Execution Department",
                insert_after="custodian",
                reqd=0,
                allow_on_submit=1,
                translatable=0,
                fetch_from="asset_category.execution_department",
                fetch_if_empty=1,
            ),
            dict(
                fieldname="barcode_id",
                label="Barcode ID",
                fieldtype="Data",
                insert_after="custodian_department",
                allow_on_submit=1,
                translatable=0,
            ),
            dict(
                fieldname="secondary_custodian",
                label="Secondary Custodian",
                fieldtype="Link",
                options="User",
                insert_after="barcode_id",
                reqd=0,
                allow_on_submit=1,
                translatable=0,
            ),
            dict(
                fieldname="specifications",
                label="Specifications",
                fieldtype="Table",
                options="HKM Asset Specification Value",
                insert_after="secondary_custodian",
                allow_on_submit=1,
                translatable=0,
            ),
        ],
    }

    # Create custom fields if they don't exist
    fields_to_create = []
    for field in custom_fields["Asset"]:
        if not frappe.db.exists(
            "Custom Field", {"dt": "Asset", "fieldname": field["fieldname"]}
        ):
            fields_to_create.append(field)

    if fields_to_create:
        create_custom_fields({"Asset": fields_to_create})

    # Update custodian_department field to add fetch_from if it already exists
    if frappe.db.exists("Custom Field", {"dt": "Asset", "fieldname": "custodian_department"}):
        frappe.db.set_value(
            "Custom Field",
            {"dt": "Asset", "fieldname": "custodian_department"},
            {
                "fetch_from": "asset_category.execution_department",
                "fetch_if_empty": 1,
                "reqd": 0,
            },
        )

    # Modify location field from Link to Data and allow on submit
    if frappe.db.exists("Custom Field", {"dt": "Asset", "fieldname": "location"}):
        frappe.db.set_value(
            "Custom Field",
            {"dt": "Asset", "fieldname": "location"},
            {"fieldtype": "Data", "options": "", "allow_on_submit": 1},
        )
    else:
        # If custom field doesn't exist, use property setter
        # Change fieldtype
        if frappe.db.exists(
            "Property Setter",
            {"doc_type": "Asset", "field_name": "location", "property": "fieldtype"},
        ):
            frappe.db.set_value(
                "Property Setter",
                {
                    "doc_type": "Asset",
                    "field_name": "location",
                    "property": "fieldtype",
                },
                "value",
                "Data",
            )
        else:
            frappe.get_doc(
                {
                    "doctype": "Property Setter",
                    "doctype_or_field": "DocField",
                    "doc_type": "Asset",
                    "field_name": "location",
                    "property": "fieldtype",
                    "value": "Data",
                    "property_type": "Select",
                }
            ).insert(ignore_permissions=True)

        # Remove options (since changing from Link to Data)
        if frappe.db.exists(
            "Property Setter",
            {"doc_type": "Asset", "field_name": "location", "property": "options"},
        ):
            frappe.db.set_value(
                "Property Setter",
                {
                    "doc_type": "Asset",
                    "field_name": "location",
                    "property": "options",
                },
                "value",
                "",
            )
        else:
            frappe.get_doc(
                {
                    "doctype": "Property Setter",
                    "doctype_or_field": "DocField",
                    "doc_type": "Asset",
                    "field_name": "location",
                    "property": "options",
                    "value": "",
                    "property_type": "Small Text",
                }
            ).insert(ignore_permissions=True)

        # Allow on submit
        if frappe.db.exists(
            "Property Setter",
            {
                "doc_type": "Asset",
                "field_name": "location",
                "property": "allow_on_submit",
            },
        ):
            frappe.db.set_value(
                "Property Setter",
                {
                    "doc_type": "Asset",
                    "field_name": "location",
                    "property": "allow_on_submit",
                },
                "value",
                "1",
            )
        else:
            frappe.get_doc(
                {
                    "doctype": "Property Setter",
                    "doctype_or_field": "DocField",
                    "doc_type": "Asset",
                    "field_name": "location",
                    "property": "allow_on_submit",
                    "value": "1",
                    "property_type": "Check",
                }
            ).insert(ignore_permissions=True)


def add_custom_field_for_asset_category():
    custom_fields = {
        "Asset Category": [
            dict(
                fieldname="execution_department",
                label="Execution Department",
                fieldtype="Link",
                options="Execution Department",
                insert_after="asset_category_name",
                translatable=0,
            ),
        ],
    }
    if not frappe.db.exists(
        "Custom Field", {"dt": "Asset Category", "fieldname": "execution_department"}
    ):
        create_custom_fields(custom_fields)
