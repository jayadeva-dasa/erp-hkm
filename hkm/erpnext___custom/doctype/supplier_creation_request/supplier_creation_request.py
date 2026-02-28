# Copyright (c) 2022, Narahari Dasa and contributors
# For license information, please see license.txt

from erpnext.selling.doctype.customer.customer import parse_full_name
import frappe
from frappe import _
from frappe.contacts.doctype.address.address import get_address_display
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils.background_jobs import enqueue
from frappe.utils.data import (
    date_diff,
    flt,
    get_link_to_form,
    time_diff_in_hours,
    time_diff_in_seconds,
)

SYS_ADMIN = "nrhdasa@gmail.com"


class SupplierCreationRequest(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        aadhar_no: DF.Data | None
        address_line_1: DF.Data
        address_line_2: DF.Data | None
        bank: DF.Link
        bank_account_name: DF.Data
        bank_account_number: DF.Data
        bank_branch_code: DF.Data
        city: DF.Data
        country: DF.Link
        email: DF.Data | None
        gst_category: DF.Literal[
            "Registered Regular", "Registered Composition", "Unregistered", "SEZ", 
            "Overseas", "Deemed Export", "UIN Holders", "Tax Deductor", 
            "Tax Collector", "Input Service Distributor"
        ]
        gstin: DF.Data | None
        mobile_number: DF.Data
        msme_number: DF.Data | None
        msme_type: DF.Literal["", "Micro", "Small", "Medium"]
        pan: DF.Data | None
        pincode: DF.Data
        state: DF.Literal[
            "", "Andaman and Nicobar Islands", "Andhra Pradesh", "Arunachal Pradesh", 
            "Assam", "Bihar", "Chandigarh", "Chhattisgarh", 
            "Dadra and Nagar Haveli and Daman and Diu", "Delhi", "Goa", "Gujarat", 
            "Haryana", "Himachal Pradesh", "Jammu and Kashmir", "Jharkhand", "Karnataka", 
            "Kerala", "Ladakh", "Lakshadweep Islands", "Madhya Pradesh", "Maharashtra", 
            "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Other Territory", 
            "Pondicherry", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", 
            "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal"
        ]
        status: DF.Literal["Pending", "Created", "Rejected"]
        supplier_group: DF.Link
        supplier_name: DF.Data
        supplier_type: DF.Literal["Company", "Individual", "Partnership"]
    # end: auto-generated types
    pass


@frappe.whitelist()
def quickly_create_supplier(request):
    scr_doc = frappe.get_doc("Supplier Creation Request", request)

    supplier_dict = {
        "doctype": "Supplier",
        "supplier_name": scr_doc.supplier_name,
        "supplier_group": scr_doc.supplier_group,
        "supplier_type": scr_doc.supplier_type,
        "pan": scr_doc.pan,
        "gstin": scr_doc.gstin,
        "gst_category": scr_doc.gst_category,
        "supplier_creation_request": scr_doc.name,
    }

    meta = frappe.get_meta("Supplier")
    if meta.has_field("custom_aadhar_no"):
        supplier_dict["custom_aadhar_no"] = scr_doc.aadhar_no

    if meta.has_field("msme_type") and scr_doc.msme_type:
        supplier_dict["msme_type"] = scr_doc.msme_type
    if meta.has_field("msme_number") and scr_doc.msme_number:
        supplier_dict["msme_number"] = scr_doc.msme_number
    
    # Set concerned person to the creator of the Supplier Creation Request
    if meta.has_field("custom_concerned_person"):
        supplier_dict["custom_concerned_person"] = scr_doc.owner        

    supplier_doc = frappe.get_doc(supplier_dict)
    supplier_doc.insert()

    address = make_address(scr_doc, supplier_doc)
    address_display = get_address_display(address.name)
    supplier_doc.db_set("supplier_primary_address", address.name)
    supplier_doc.db_set("primary_address", address_display)

    contact = make_contact(scr_doc, supplier_doc)
    if contact:
        supplier_doc.db_set("supplier_primary_contact", contact.name)
        supplier_doc.db_set("mobile_no", contact.mobile_no)
        supplier_doc.db_set("email_id", contact.email_id)

    if scr_doc.bank:
        frappe.get_doc(
            {
                "doctype": "Bank Account",
                "bank": scr_doc.bank,
                "account_name": scr_doc.bank_account_name,
                "party_type": "Supplier",
                "party": supplier_doc.name,
                "branch_code": scr_doc.bank_branch_code,
                "bank_account_no": scr_doc.bank_account_number,
            }
        ).insert(ignore_links=True)

    enqueue(
        method=frappe.sendmail,
        queue="short",
        timeout=300,
        is_async=True,
        **{
            "recipients": [scr_doc.owner],
            "message": get_success_mail(scr_doc, supplier_doc),
            "subject": "Supplier {} Created".format(scr_doc.supplier_name),
            "reference_doctype": supplier_doc.doctype,
            "reference_name": supplier_doc.name,
            "reply_to": (
                supplier_doc.owner
                if supplier_doc.owner != "Administrator"
                else SYS_ADMIN
            ),
        },
    )

    frappe.msgprint(
        f"Supplier Created {get_link_to_form('Supplier', supplier_doc.name)}",
        indicator="green",
        alert=True,
    )

    scr_doc.status = "Created"
    scr_doc.save()


def make_address(scr_doc, supplier_doc):
    reqd_fields = []
    for field in ["city", "country"]:
        if not scr_doc.get(field):
            reqd_fields.append("<li>" + field.title() + "</li>")

    if reqd_fields:
        msg = _("Following fields are mandatory to create address:")
        frappe.throw(
            "{0} <br><br> <ul>{1}</ul>".format(msg, "\n".join(reqd_fields)),
            title=_("Missing Values Required"),
        )

    address = frappe.get_doc(
        {
            "doctype": "Address",
            "address_title": supplier_doc.get("name"),
            "address_line1": scr_doc.get("address_line_1"),
            "address_line2": scr_doc.get("address_line_2"),
            "city": scr_doc.get("city"),
            "state": scr_doc.get("state"),
            "pincode": scr_doc.get("pincode"),
            "country": scr_doc.get("country"),
            "gst_category": supplier_doc.get("gst_category"),
            "gstin": scr_doc.get("gstin"),
            "links": [
                {
                    "link_doctype": supplier_doc.get("doctype"),
                    "link_name": supplier_doc.get("name"),
                }
            ],
        }
    ).insert()

    return address


def make_contact(scr_doc, supplier_doc):
    if not scr_doc.mobile_number:
        return None

    contact_dict = {
        "doctype": "Contact",
        "is_primary_contact": 1,
        "is_billing_contact": 1,
        "links": [
            {"link_doctype": supplier_doc.doctype, "link_name": supplier_doc.name}
        ],
    }

    if scr_doc.supplier_type == "Individual":
        first, middle, last = parse_full_name(scr_doc.supplier_name)
        contact_dict.update(
            {
                "first_name": first,
                "middle_name": middle,
                "last_name": last,
            }
        )
    else:
        contact_dict.update(
            {
                "company_name": scr_doc.supplier_name,
            }
        )

    contact = frappe.get_doc(contact_dict)

    if scr_doc.get("email"):
        contact.add_email(scr_doc.get("email"), is_primary=True)
    if scr_doc.get("mobile_number"):
        contact.add_phone(scr_doc.get("mobile_number"), is_primary_mobile_no=True)

    contact.insert()

    return contact


def get_success_mail(scr_doc, supplier_doc):
    time_taken, postfix = (
        time_diff_in_hours(supplier_doc.creation, scr_doc.creation),
        "hours",
    )
    if time_taken < 1:
        time_taken, postfix = (
            time_diff_in_seconds(supplier_doc.creation, scr_doc.creation) / 60,
            "minutes",
        )
    elif time_taken > 23:
        time_taken, postfix = date_diff(supplier_doc.creation, scr_doc.creation), "days"
    time_taken = flt(time_taken, 2)

    return frappe.render_template(
        "hkm/erpnext___custom/doctype/supplier_creation_request/success.html",
        {
            "supplier_name": supplier_doc.supplier_name,
            "supplier_url": frappe.utils.get_url_to_form("Supplier", supplier_doc.name),
            "time_taken": time_taken,
            "time_taken_postfix": postfix,
            "contact_person": supplier_doc.owner,
        },
    )
