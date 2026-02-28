# Copyright (c) 2022, HKM
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    add_custom_field_in_material_request()
    add_custom_field_in_purchase_order()


def add_custom_field_in_material_request():
    custom_fields = {
        "Material Request Item": [
            dict(
                fieldname="item_type",
                label="Item Type",
                insert_after="item_name",
                translatable=0,
                read_only=1,
            )
        ],
    }
    create_custom_fields(custom_fields)


def add_custom_field_in_purchase_order():
    custom_fields = {
        "Purchase Order Item": [
            dict(
                fieldname="item_type",
                label="Item Type",
                insert_after="item_name",
                translatable=0,
                read_only=1,
            )
        ],
    }
    # if not frappe.db.exists('Custom Field', {"dt": 'Purchase Order', "fieldname":'for_a_work_order'}):
    create_custom_fields(custom_fields)
