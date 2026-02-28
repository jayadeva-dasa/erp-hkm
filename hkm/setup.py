from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
    make_dimension_in_accounting_doctypes,
)
import frappe, click
from frappe.desk.page.setup_wizard.setup_wizard import make_records
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.model import document
from frappe.custom.doctype.custom_field.custom_field import create_custom_field


def after_install():
    print("hare krishna")
    frappe.clear_cache()
    create_accounting_dimension_fields()


def create_accounting_dimension_fields():
    doctypes = frappe.get_hooks(
        "accounting_dimension_doctypes",
        app_name="hkm",
    )

    dimensions = frappe.get_all("Accounting Dimension", pluck="name")
    print(doctypes)
    print(dimensions)
    for dimension in dimensions:
        doc = frappe.get_doc("Accounting Dimension", dimension)
        make_dimension_in_accounting_doctypes(doc, doctypes)


def make_custom_fields(update=True):
    pass


def get_custom_fields():
    pass
