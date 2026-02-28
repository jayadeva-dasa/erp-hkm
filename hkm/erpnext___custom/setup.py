from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
    make_dimension_in_accounting_doctypes,
)
import frappe, click

from frappe.custom.doctype.custom_field import custom_field
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.desk.page.setup_wizard.setup_wizard import make_records

from hkm.erpnext___custom.constants.custom_fields import CUSTOM_FIELDS
from hkm.erpnext___custom.constants.custom_roles import CUSTOM_ROLES
from hkm.erpnext___custom.constants.docperms import DOC_PERMS

APPROVING_AUTHORITY = "approving_authorities"


def after_install():
    for doctype in CUSTOM_FIELDS:
        if isinstance(CUSTOM_FIELDS[doctype], list):
            for ind, d in enumerate(CUSTOM_FIELDS[doctype]):
                CUSTOM_FIELDS[doctype][ind]["is_system_generated"] = 1
        else:
            CUSTOM_FIELDS[doctype]["is_system_generated"] = 1
    create_custom_fields(CUSTOM_FIELDS, update=True)
    create_accounting_dimension_fields()
    create_approval_matrix_custom_fields()
    # make_custom_records()


def make_custom_records():
    click.secho("Installing Custom Roles", fg="yellow")
    role_records = get_roles()
    make_records(role_records)
    click.secho("Setting Custom Permission on DocTypes", fg="yellow")
    make_records(DOC_PERMS)


def get_docperms():
    records = []
    for docperm in DOC_PERMS:
        docperm.setdefault("doctype", "Role")
        records.append(docperm)
    return records


def get_roles():
    records = []
    for r in CUSTOM_ROLES:
        r.setdefault("doctype", "Role")
        records.append(r)
    return records


def before_uninstall():
    delete_custom_fields(CUSTOM_FIELDS)


def delete_custom_fields(custom_fields):
    """
    :param custom_fields: a dict like `{'Sales Invoice': [{fieldname: 'test', ...}]}`
    """

    for doctypes, fields in custom_fields.items():
        if isinstance(fields, dict):
            # only one field
            fields = [fields]

        if isinstance(doctypes, str):
            # only one doctype
            doctypes = (doctypes,)

        for doctype in doctypes:
            print(fields)
            frappe.db.delete(
                "Custom Field",
                {
                    "fieldname": ("in", [field["fieldname"] for field in fields]),
                    "dt": doctype,
                },
            )

            frappe.clear_cache(doctype=doctype)


def create_accounting_dimension_fields():
    click.secho("Installing Accounting Dimensions", fg="yellow")
    doctypes = frappe.get_hooks(
        "accounting_dimension_doctypes",
        app_name="hkm",
    )

    dimensions = frappe.get_all("Accounting Dimension", pluck="name")
    for dimension in dimensions:
        doc = frappe.get_doc("Accounting Dimension", dimension)
        make_dimension_in_accounting_doctypes(doc, doctypes)


def create_approval_matrix_custom_fields():
    doctypes = frappe.get_hooks(
        "approval_matrix_doctypes",
        app_name="hkm",
    )
    custom_fields = {}

    for doctype in list(set(doctypes)):
        fieldnames = [f.fieldname for f in frappe.get_meta(doctype).fields]
        # if (
        #     "approving_authorities_section"
        #     and "approving_authorities"
        #     and "locked" in fieldnames
        # ):
        #     continue
        custom_fields[doctype] = [
            {
                "fieldname": "approving_authorities_section",
                "label": "Approving Authorities",
                "fieldtype": "Tab Break",
                "tab_break": 1,
                "insert_after": get_last_fieldname(doctype),
            },
            {
                "fieldname": "approving_authorities",
                "label": "Approving Authority",
                "fieldtype": "Table",
                "options": "Approval Matrix Authority",
                "insert_after": "approving_authorities_section",
                "read_only": 0,
            },
            {
                "fieldname": "approval_initiator",
                "label": "Approval Initiator",
                "fieldtype": "Link",
                "insert_after": "approving_authorities_section",
                "read_only": 1,
                "options": "User",
            },
            {
                "fieldname": "locked",
                "label": "Locked",
                "fieldtype": "Check",
                "insert_after": "approval_initiator",
                "default": 0,
                "read_only": 1,
            },
            {
                "fieldname": "approval_status",
                "label": "Approval Status",
                "fieldtype": "Data",
                "insert_after": "locked",
                "read_only": 1,
            },
            {
                "fieldname": "current_approving_authority",
                "label": "Current Approving Authority",
                "fieldtype": "Data",
                "insert_after": "approval_status",
                "read_only": 1,
            },
            {
                "fieldname": "status_indicator",
                "label": "Status Indicator",
                "fieldtype": "Select",
                "insert_after": "approval_status",
                "read_only": 1,
                "options": "Check Pending\nApproved\nCancelled\nRejected\nChecked\nFinal Approval Pending\nApproval Started\n",
            },
        ]

    create_custom_fields(custom_fields, update=True)


def get_last_fieldname(doctype_name):
    doc = frappe.get_doc("DocType", doctype_name)
    if not doc.fields:
        return None
    # Sort by idx to get the UI order
    sorted_fields = sorted(doc.fields, key=lambda f: f.idx)
    last_field = sorted_fields[-1]
    return last_field.fieldname
