# Copyright (c) 2021, Tara Technologies
# For license information, please see license.txt

from __future__ import unicode_literals
import datetime

from pymysql import Date
from hkm.erpnext___custom.overrides.buying_validations import (
    validate_buying_dates,
    validate_one_time_vendor,
)
from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import PurchaseInvoice
import frappe
from frappe import _, throw
from frappe.model.docstatus import DocStatus
from frappe.utils import flt
from frappe.utils.data import getdate
from frappe.model.naming import getseries


class HKMPurchaseInvoice(PurchaseInvoice):
    def autoname(self):
        dateF = getdate(self.posting_date)
        company_abbr = frappe.get_cached_value("Company", self.company, "abbr")
        year = dateF.strftime("%y")
        month = dateF.strftime("%m")
        prefix = f"{company_abbr}-PI-{year}{month}-"
        if self.is_return:
            prefix = "D-" + prefix
        self.name = prefix + getseries(prefix, 5)

    def validate(self):
        super().validate()
        self.asset_pr_required()
        self.validate_expense_account()
        validate_one_time_vendor(self)
        validate_buying_dates(self)
        return

    def validate_expense_account(self):
        for item in self.get("items"):
            account_type = frappe.db.get_value(
                "Account", item.expense_account, "account_type"
            )
            if (not item.is_fixed_asset) and account_type == "Fixed Asset":
                frappe.throw("You can't use a Fixed Asset Account for expense booking.")
            # elif item.is_fixed_asset and account_type != "Fixed Asset":
            #     frappe.throw("Please choose a Fixed Asset Account for expense booking.")
        return

    def asset_pr_required(self):
        asset_items = self.get_asset_items()
        for d in self.get("items"):
            if not d.purchase_receipt and d.item_code in asset_items:
                msg = _("Purchase Receipt Required for Asset Item {}").format(
                    frappe.bold(d.item_code)
                )
                throw(msg, title=_("Mandatory Purchase Receipt"))
        return

    def get_asset_items(self):
        asset_items = []
        item_codes = list(set(item.item_code for item in self.get("items")))
        if item_codes:
            asset_items = frappe.db.get_values(
                "Item",
                {"name": ["in", item_codes], "is_fixed_asset": 1},
                pluck="name",
                cache=True,
            )

        return asset_items


@frappe.whitelist()
def get_documents_map_data(document):
    doc = frappe.get_doc("Purchase Invoice", document)
    purchase_receipts = []
    purchase_orders = []
    material_requests = []
    for item in doc.items:
        purchase_orders.append(item.purchase_order)
        purchase_receipts.append(item.purchase_receipt)
    purchase_orders = set(purchase_orders)
    purchase_receipts = set(purchase_receipts)
    for po in purchase_orders:
        if not po:
            continue
        requests = frappe.get_all(
            "Purchase Order Item", filters={"parent": po}, pluck="material_request"
        )
        material_requests.extend(requests)
    material_requests = set(material_requests)
    mrn_docs = []
    po_docs = []
    pr_docs = []
    for m in material_requests:
        if not m:
            continue
        attachments = frappe.get_all(
            "File",
            filters={"attached_to_name": m, "attached_to_doctype": "Material Request"},
            fields=["file_url"],
        )
        doc_dict = frappe.get_doc("Material Request", m).as_dict()
        doc_dict.attachments = attachments
        mrn_docs.append(doc_dict)
    for p in purchase_orders:
        if not p:
            continue
        attachments = frappe.get_all(
            "File",
            filters={"attached_to_name": p, "attached_to_doctype": "Purchase Order"},
            fields=["file_url", "file_name"],
        )
        doc_dict = frappe.get_doc("Purchase Order", p).as_dict()
        doc_dict.attachments = attachments
        po_docs.append(doc_dict)
    for p in purchase_receipts:
        if not p:
            continue
        attachments = frappe.get_all(
            "File",
            filters={"attached_to_name": p, "attached_to_doctype": "Purchase Receipt"},
            fields=["file_url", "file_name"],
        )
        doc_dict = frappe.get_doc("Purchase Receipt", p).as_dict()
        doc_dict.attachments = attachments
        pr_docs.append(doc_dict)

    data = frappe._dict(
        material_requests=mrn_docs,
        purchase_orders=po_docs,
        purchase_receipts=pr_docs,
    )
    return frappe.render_template("templates/purchase_invoice/documents_map.html", data)
