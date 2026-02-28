# Copyright (c) 2022, Narahari Dasa and contributors
# For license information, please see license.txt

from frappe.model.naming import getseries
from frappe.utils.background_jobs import enqueue
from frappe.utils.data import (
    date_diff,
    flt,
    get_link_to_form,
    time_diff_in_hours,
    time_diff_in_seconds,
)
from hkm.erpnext___custom.extend.item import fetch_item_code
import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
import re

SYS_ADMIN = "nrhdasa@gmail.com"


class ItemCreationRequest(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        asset_category: DF.Link | None
        asset_item: DF.Check
        is_sales_item: DF.Check
        item_group: DF.Link
        item_name: DF.Data
        remarks: DF.Data | None
        status: DF.Literal["Pending", "Created", "Rejected"]
        stock_item: DF.Check
        tax_category: DF.Link | None
        unit_of_measure: DF.Link
        valuation_rate: DF.Float

    # end: auto-generated types
    def validate(self):
        pass
        # if self.selling_rate is not None and self.valuation_rate is not None and self.selling_rate < self.valuation_rate:
        # 	frappe.throw("Selling Rate can't be less than Valuation Rate.")
        # return

    # def before_save(self):
    # 	if self.is_sales_item:
    # 		self.calculate_selling_rate_without_tax_and_set_default_company()
    # def on_update(self):
    # 	self.calculate_selling_rate_without_tax()

    # def calculate_selling_rate_without_tax_and_set_default_company(self):
    # 	if self.tax_category is not None and self.tax_category != "":
    # 		# result = re.findall('[0-9]+', str(self.tax_category))
    # 		if self.tax_category:
    # 			tax_category_doc = frappe.get_doc("Item Tax Template",self.tax_category)
    # 			cumulative_tax = tax_category_doc.cumulative_tax
    # 			if cumulative_tax != 0:
    # 				self.selling_rate_without_tax = self.selling_rate/(1+(cumulative_tax/100))
    # 		else:
    # 			self.selling_rate_without_tax = self.selling_rate
    # 		self.default_company = tax_category_doc.company


@frappe.whitelist()
def quickly_create_item(request):
    icr_doc = frappe.get_doc("Item Creation Request", request)
    # frappe.errprint(icr_doc.as_dict())

    new_item_code = fetch_item_code(icr_doc.item_group)

    if not new_item_code:
        item_code_series = frappe.db.get_single_value(
            "HKM General Settings", "item_code_default_series"
        )
        if not item_code_series:
            frappe.throw(
                "Please set a series in either <b>Item Group</b> OR Common <b>HKM General Settings</b>"
            )
        new_item_code = (
            item_code_series + "-" + getseries(item_code_series, 4)
        )  # ✅ String

    item_dict = {
        "doctype": "Item",
        "item_group": icr_doc.item_group,
        "stock_uom": icr_doc.unit_of_measure,
        "item_name": icr_doc.item_name,
        "item_code": new_item_code,
        "item_creation_request": icr_doc.name,
        "is_stock_item": 0,
    }

    if icr_doc.asset_item:
        item_dict["is_fixed_asset"] = 1
        item_dict["asset_category"] = icr_doc.asset_category
        item_dict["auto_create_assets"] = 1
        item_dict["asset_naming_series"] = "ACC-ASS-.YYYY.-"
    elif icr_doc.stock_item:
        item_dict["is_stock_item"] = 1

    if icr_doc.is_sales_item:
        frappe.errprint("is_sales_item")
        item_dict["valuation_rate"] = icr_doc.valuation_rate
        item_dict["taxes"] = [{"item_tax_template": icr_doc.tax_category}]
    else:
        item_dict["is_sales_item"] = 0

    item_doc = frappe.get_doc(item_dict)

    item_doc.insert()

    frappe.msgprint(
        f"Item Code Created {get_link_to_form('Item', item_doc.name)}",
        indicator="green",
        alert=True,
    )

    enqueue(
        method=frappe.sendmail,
        queue="short",
        timeout=300,
        is_async=True,
        **{
            "recipients": [icr_doc.owner],
            "message": success_mail(icr_doc, item_doc),
            "subject": "Item {} Created".format(icr_doc.item_name),
            "reference_doctype": item_doc.doctype,
            "reference_name": item_doc.name,
            "reply_to": (
                item_doc.owner if item_doc.owner != "Administrator" else SYS_ADMIN
            ),
            "delayed": False,
            "sender": icr_doc.owner,
        },
    )

    icr_doc.status = "Created"
    icr_doc.save()


def success_mail(icr_doc, item_doc):
    time_taken, postfix = (
        time_diff_in_hours(item_doc.creation, icr_doc.creation),
        "hours",
    )
    if time_taken < 1:
        time_taken, postfix = (
            time_diff_in_seconds(item_doc.creation, icr_doc.creation) / 60,
            "minutes",
        )
    elif time_taken > 23:
        time_taken, postfix = date_diff(item_doc.creation, icr_doc.creation), "days"
    time_taken = flt(time_taken, 2)

    return frappe.render_template(
        "hkm/erpnext___custom/doctype/item_creation_request/success.html",
        {
            "item_name": item_doc.item_name,
            "item_code": item_doc.item_code,
            "item_url": frappe.utils.get_url_to_form("Item", item_doc.name),
            "time_taken": time_taken,
            "time_taken_postfix": postfix,
            "contact_person": item_doc.owner,
        },
    )
