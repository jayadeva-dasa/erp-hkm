# Copyright (c) 2022, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import frappe.cache_manager
from frappe.utils import date_diff, getdate, formatdate
from frappe import _


class FreezeTransactionSettings(Document):
    def validate(self):
        self.validate_duplicate()
        self.validate_date()

    def on_update(self):
        self.delete_company_frozen_document_key()

    def on_trash(self):
        self.delete_company_frozen_document_key()

    def delete_company_frozen_document_key(self):
        frappe.cache().hdel("company_frozen_document", self.company)

    def validate_duplicate(self):
        documents = []
        for d in self.get("forzen_documents"):
            if d.document_type in documents:
                frappe.throw(
                    "Row#{0} Duplicate record not allowed for {1}".format(
                        d.idx, d.document_type
                    )
                )

            documents.append(d.document_type)

    def validate_date(self):
        if (
            self.freeze_from
            and self.freeze_upto
            and date_diff(self.freeze_from, self.freeze_upto) >= 0
        ):
            frappe.throw("Invalid dates")
        for d in self.get("forzen_documents"):
            if (
                d.frozen_from
                and d.frozen_upto
                and date_diff(d.frozen_from, d.frozen_upto) >= 0
            ):
                frappe.throw("Row#{0} Invalid dates".format(d.idx))
            elif not d.frozen_from and not d.frozen_upto:
                frappe.throw(
                    "Row#{0} Please enter date to freeze transaction.".format(d.idx)
                )


@frappe.whitelist()
def get_company_frozen_document(company):
    company_frozen_document = (
        frappe.cache().hget("company_frozen_document", company) or frappe._dict()
    )
    if not company_frozen_document:
        if frappe.db.exists("Freeze Transaction Settings", {"company": company}):
            doc = frappe.get_cached_doc(
                "Freeze Transaction Settings", {"company": company}
            )
            for d in doc.get("forzen_documents"):
                modifier = [d.primary_modifier]
                if d.secondary_modifier:
                    modifier.append(d.secondary_modifier)
                company_frozen_document.setdefault(
                    d.document_type,
                    frappe._dict(
                        frozen_from=d.frozen_from,
                        frozen_upto=d.frozen_upto,
                        modifier=modifier,
                    ),
                )

        frappe.cache().hset("company_frozen_document", company, company_frozen_document)

    return company_frozen_document


def get_freeze_transaction_for_doctype(company, doctype):
    return get_company_frozen_document(company).get(doctype, {})


def validate_transaction_against_frozen_date(doc, method=None):
    def validate_transaction_date(transaction_date, frozen_from=None, frozen_upto=None):
        if frozen_from and frozen_upto:
            return (
                not getdate(frozen_from)
                < getdate(transaction_date)
                < getdate(frozen_upto)
            )
        if (
            frozen_upto
            and date_diff(getdate(frozen_upto), getdate(transaction_date)) >= 0
        ):
            return False
        if (
            frozen_from
            and date_diff(getdate(transaction_date), getdate(frozen_from)) >= 0
        ):
            return False

        return True

    transaction_date = (
        doc.get("transaction_date")
        or doc.get("posting_date")
        or doc.get("receipt_date")
    )
    company = doc.get("company")
    if transaction_date and company:
        company_frozen_document = get_freeze_transaction_for_doctype(
            company, doc.doctype
        )
        if company_frozen_document:
            frozen_from = company_frozen_document.get("frozen_from")
            frozen_upto = company_frozen_document.get("frozen_upto")
            is_valid_date = validate_transaction_date(
                transaction_date, frozen_from, frozen_upto
            )
            frozen_tran_modifier = company_frozen_document.get("modifier") or []
            frozen_tran_modifier.append("Administrator")
            if not is_valid_date and frappe.session.user not in frozen_tran_modifier:
                message = "Transaction frozen "
                if frozen_from and frozen_upto:
                    message += "between {0} and {1}.".format(
                        formatdate(frozen_from), formatdate(frozen_upto)
                    )
                elif frozen_from:
                    message += "from {0}.".format(formatdate(frozen_from))
                elif frozen_upto:
                    message += "upto {0}.".format(formatdate(frozen_upto))
                if not getattr(doc.flags, "ignore_frozen_transaction", False):
                    frappe.throw(
                        _(
                            "<b class='text-danger'>{0}<br>You are not authorized to add/cancel <b>{1}</b> of {2}."
                        ).format(message, doc.doctype, formatdate(transaction_date))
                    )
