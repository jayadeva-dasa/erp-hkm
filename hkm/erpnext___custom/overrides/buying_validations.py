import frappe
from frappe import _
from frappe.utils import get_link_to_form, get_url_to_form, getdate


def validate_work_order_item(self):
    if not self.meta.get_field("for_a_work_order") or not self.for_a_work_order:
        return
    invalid_work_order_items = []

    non_stock_items = frappe.get_list(
        "Item", pluck="name", filters={"disabled": 0, "is_stock_item": 0}
    )
    for d in self.get("items"):
        if d.item_code not in non_stock_items:
            invalid_work_order_items.append(d)

    for d in invalid_work_order_items:
        frappe.throw(
            _(
                "Row#{0}: Stock Item {1} is not allowed for Work Order.<br>Please select non stock item."
            ).format(
                d.idx,
                frappe.bold(d.item_name),
            ),
            title=_("Invalid Item"),
        )
    return


def check_items_are_not_from_template(self):
    for item in self.items:
        if frappe.get_value("Item", item.item_code, "has_variants") == 1:
            self.validate = False
            frappe.throw(
                "Item Code : {} is a Template. It can not be used in Transactions".format(
                    item.item_code
                )
            )
    return


def validate_one_time_vendor(self):
    settings = frappe.get_cached_doc("HKM General Settings")
    if not settings.one_time_restrictions_enabled:
        return
    is_supplier_one_time_vendor = frappe.db.get_value(
        "Supplier", self.supplier, "is_one_time_vendor"
    )
    if (
        is_supplier_one_time_vendor
        and self.grand_total > settings.one_time_vendor_limit
    ):
        frappe.throw(
            f"One Time Vendor can not have a transaction more than {settings.one_time_vendor_limit}"
        )
    return


def validate_buying_dates(doc=None, doctype=None, docname=None):
    if not doc:
        doc = frappe.get_doc(doctype, docname)
    if doc.doctype == "Purchase Order":
        validate_against_child_doctype(
            doc,
            "Material Request",
            "material_request",
            "transaction_date",
            "transaction_date",
        )
    if doc.doctype == "Purchase Receipt":
        validate_against_child_doctype(
            doc,
            "Purchase Order",
            "purchase_order",
            "posting_date",
            "transaction_date",
        )
    if doc.doctype == "Purchase Invoice":
        validate_against_child_doctype(
            doc,
            "Purchase Receipt",
            "purchase_receipt",
            "posting_date",
            "posting_date",
        )
        validate_against_child_doctype(
            doc, "Purchase Order", "purchase_order", "posting_date", "transaction_date"
        )
    return


def validate_against_child_doctype(
    doc, child_doctype, parent_child_field, parent_date_field, child_doc_date_field
):
    child_docs = list(
        set(
            [
                i.get(parent_child_field)
                for i in doc.get("items")
                if i.get(parent_child_field)
            ]
        )
    )

    for m in frappe.get_all(
        child_doctype,
        filters={"name": ("in", child_docs)},
        fields=["name", child_doc_date_field],
    ):
        child_doc_link = get_link_to_form(child_doctype, m.name)
        if m.get(child_doc_date_field) > getdate(doc.get(parent_date_field)):
            frappe.throw(
                f"{doc.doctype} Date should be greater than {child_doctype} Date.<br>"
                f"{child_doctype}: {child_doc_link} <br>"
                f"{child_doctype} Date: {m.get(child_doc_date_field)} <br>"
                f"{doc.doctype} Date: {doc.get(parent_date_field)}"
            )
    return
