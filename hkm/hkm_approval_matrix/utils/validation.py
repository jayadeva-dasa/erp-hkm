import frappe
from frappe import _
from frappe.model.document import Document
from .constants import IGNORED_FIELDS
from .general import get_current_approving_authority
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
    get_accounting_dimensions,
)
from .constants import CUSTOM_FIELDS


def get_value_fields(doc: Document):
    meta = frappe.get_meta(doc.doctype)
    table_fields = [
        df.fieldname
        for df in meta.fields
        if df.fieldtype == "Table"
        and df.fieldtype not in IGNORED_FIELDS
        and df.fieldname not in CUSTOM_FIELDS
    ]

    value_fields = [
        df.fieldname
        for df in meta.fields
        if df.fieldtype not in IGNORED_FIELDS
        and df.fieldtype != "Table"
        and df.fieldtype not in CUSTOM_FIELDS
    ]

    return table_fields, value_fields


def validate(doc: Document):

    if get_current_approving_authority(doc.doctype, doc.name) != frappe.session.user:
        table_fields, value_fields = get_value_fields(doc)
        validate_field_changes(doc, table_fields, value_fields)
    validate_doc_is_rejected(doc)
    validate_doc_is_approved_by_authority(doc)
    validate_approving_authority_changes(doc)


def validate_field_changes(doc: Document, table_fields, value_fields):
    dimensions = ["cost_center", "project"] + get_accounting_dimensions()
    for field in value_fields:
        if field in dimensions:
            continue
        if doc.has_value_changed(field):
            throw_locked_field_error(field)

    for field in table_fields:
        if not doc.is_child_table_same(field):
            throw_locked_field_error(field)


def validate_doc_is_rejected(doc: Document):

    if doc.approving_authorities:
        old_doc = doc.get_doc_before_save()
        if any(row.status == "Rejected" for row in old_doc.approving_authorities):
            frappe.throw(_("Document is rejected, not allowed to modify"))


def validate_doc_is_approved_by_authority(doc: Document):
    if doc.approving_authorities:
        old_doc = doc.get_doc_before_save()
        if any(
            row.status == "Approved" and row.authority == frappe.session.user
            for row in old_doc.approving_authorities
        ):
            frappe.throw(_("You have already approved this document"))


def throw_locked_field_error(field):
    frappe.throw(
        _("Document is locked, not allowed to modify field: {field}").format(
            field=field
        )
    )


def validate_approving_authority_changes(doc: Document):
    """Validate changes to approving authorities"""
    old_doc = doc.get_doc_before_save()

    old_auth = {row.authority: row for row in old_doc.approving_authorities}

    if len(doc.approving_authorities) > len(old_auth):
        frappe.throw(_("Not allowed to add new approving authority"))

    for row in doc.approving_authorities:
        old_row = old_auth.get(row.authority)
        if not old_row:
            frappe.throw(_("Modifying approving authorities is not allowed"))

        if old_row.status != row.status:
            if (
                get_current_approving_authority(doc.doctype, doc.name)
                != frappe.session.user
            ):
                frappe.throw(
                    _("You are not the Current Approving Authority for this document")
                )

            if row.authority != frappe.session.user:
                frappe.throw(
                    _(
                        "You are not allowed to change the status of authority {0}"
                    ).format(row.authority)
                )
