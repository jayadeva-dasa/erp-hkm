# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

# import frappe
import json
import time
import uuid
from dhananjaya.api.v1.direct.main import upload_donation
from dhananjaya.dhananjaya.utils import is_null_or_blank
from hkm.hkm_integration.doctype.indusind_bank_integration.indusind_bank_integration import (
    generate_qr_code_string,
)
import frappe
from frappe.model.document import Document


class HKMAPICALLBACK(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        api_response: DF.JSON | None
        document_payload: DF.JSON | None
        integration_doctype: DF.Link
        order_number: DF.Data
        refrence_docname: DF.DynamicLink | None
        refrence_doctype: DF.Link
    # end: auto-generated types
    
    def before_save(self):
        old_doc = self.get_doc_before_save()
        if old_doc.api_response != self.api_response:
            if self.refrence_doctype == "Donation Receipt":
                self.create_donation_receipt()

    def create_donation_receipt(self):
        data = json.loads(self.document_payload)
        try:
            upload_donation(payload=data)
        except Exception as e:
            frappe.log_error(f"Error creating donation receipt: {e}")
            frappe.throw(f"Error creating donation receipt: {e}")





@frappe.whitelist()
def check_transaction_status_donation_receipt(order_number: str):
    callback_doc = frappe.get_doc("HKM API Callback", {"order_number": order_number})
    






@frappe.whitelist()
def generate_dynamic_qr_code_donation_receipt():
    data = json.loads(frappe.request.data)

    company = data.get("company")

    if data.get("company") is None:
        frappe.throw("Company is required")

    if company != "Hare Krishna Movement Jaipur":
        frappe.throw("Company is not allowed")

    payload = {
        "donation": {
            "donor_name": data.get("full_name"),
            "mobile": data.get("mobile_number"),
            "address": data.get("address"),
            "amount": data.get("amount"),
            "seva_type": data.get("seva_type"),
            "seva_subtype": data.get("seva_subtype"),
            "company": data.get("company"),
            "payment_method": "UPI",
        }
    }

    if not is_null_or_blank(data.get("pan")):
        payload["donation"]["pan_no"] = data.get("pan")

    # receipt_docname = upload_donation(payload=payload)

    timestamp = int(time.time())
    unique_id = str(uuid.uuid4()).replace("-", "")[:20].upper()
    order_number = f"INDB{timestamp}{unique_id}"

    setting_doc = frappe.get_cached_doc("IndusInd Bank Integration")
    setting_doc.flags.ignore_permissions = True
    qr_code_string = generate_qr_code_string(
        payee_vpa=setting_doc.merchant_vpa,
        payee_name=setting_doc.merchant_name,
        amount=data.get("amount"),
        transaction_reference=order_number,
        transaction_note="Donation Payment",
        merchant_code=setting_doc.mcc,
        merchant_id=setting_doc.merchant_id,
    )

    # api_response: DF.JSON | None
    #     document_payload: DF.JSON | None
    #     integration_doctype: DF.Link
    #     order_number: DF.Data
    #     refrence_docname: DF.DynamicLink | None
    #     refrence_doctype: DF.Link

    doc = frappe.new_doc("HKM API Callback")
    doc.order_number = order_number
    doc.integration_doctype = "IndusInd Bank Integration"

    doc.document_payload = json.dumps(payload)
    doc.insert(ignore_permissions=True)
    frappe.db.commit()  # v16: REVIEW - check if needed

    return qr_code_string
