# Copyright (c) 2022, HKM
# For license information, please see license.txt

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
	add_custom_field_in_supplier()


def add_custom_field_in_supplier():
	custom_fields = {
		'Supplier' : [
			dict(fieldname='msme_type', label='MSME Type', fieldtype='Select', options='\nMicro\nSmall\nMedium',
				 translatable=0, read_only=0 , insert_after = 'country'
			),
				dict(fieldname='msme_number', label='MSME Number', fieldtype='Data', translatable=0, read_only=0 , insert_after = 'msme_type'),
		],
	}
	if not frappe.db.exists('Custom Field', {"dt": 'Supplier', "fieldname":'msme_type'}) and not frappe.db.exists('Custom Field', {"dt": 'Supplier', "fieldname":'msme_number'}):
		create_custom_fields(custom_fields)
