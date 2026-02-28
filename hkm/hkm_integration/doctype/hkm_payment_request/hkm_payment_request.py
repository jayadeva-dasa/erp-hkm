# Copyright (c) 2024, Narahari Dasa and contributors
# For license information, please see license.txt

import json
import frappe
from frappe.model.document import Document
from frappe.model.naming import getseries, make_autoname

AUBANK = "AU Small Finance Bank"


class HKMPaymentRequest(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF
        from hkm.hkm_integration.doctype.hkm_payment_request_detail.hkm_payment_request_detail import HKMPaymentRequestDetail

        amended_from: DF.Link | None
        bank_account: DF.Link
        batch_number: DF.Data | None
        company: DF.Link
        items: DF.Table[HKMPaymentRequestDetail]
        request_creation: DF.Datetime | None
        request_id: DF.Data | None
        status: DF.Literal["", "Submitted", "Uploaded", "Approval Pending", "Paid", "Failed", "Cancelled"]
        total_amount: DF.Currency
    # end: auto-generated types

    def before_submit(self):
        self.request_creation = frappe.utils.now_datetime()

    def autoname(self):
        abbrevation = frappe.db.get_value("Company", self.company, "abbr")
        prefix = f"B{abbrevation}"
        self.name = prefix + getseries(prefix, 6)

    def validate(self):
        if (
            frappe.db.get_value("Bank Account", self.bank_account, "company")
            != self.company
        ):
            frappe.throw("Bank Account doesn't belong to the company.")

        # for item in self.items:
        #     if (
        #         item.supplier
        #         and frappe.db.count(
        #             "Bank Account",
        #             {"party_type": "Supplier", "party": item.supplier, "disabled": 0},
        #         )
        #         > 1
        #     ):
        #         frappe.throw(
        #             f"Multiple Bank Accounts found for the supplier {item.supplier}"
        #         )

        return

    def before_save(self):
        total = 0
        for item in self.items:
            total += item.amount
        self.total_amount = total
        return

    def before_cancel(self):
        if self.batch_number and self.request_id:
            frappe.throw(
                "Cannot cancel the payment request as it is already processed."
            )
        return


@frappe.whitelist()
def upload_payment(payment_request):
    payment_request_doc = frappe.get_doc("HKM Payment Request", payment_request)
    
    # Validation: Check if document is cancelled
    if payment_request_doc.docstatus == 2:
        frappe.throw("Cannot upload a cancelled payment request.")
    
    # Validation: Check if document is already uploaded
    if payment_request_doc.batch_number and payment_request_doc.request_id:
        frappe.throw("This payment request has already been uploaded to the bank.")
    
    # Validation: Check if document is submitted
    if payment_request_doc.docstatus != 1:
        frappe.throw("Please submit the payment request before uploading to bank.")
    
    # Validation: If this is an amended document, check if original was uploaded
    if payment_request_doc.amended_from:
        if frappe.db.exists("HKM Payment Request", payment_request_doc.amended_from):
            original_doc = frappe.get_doc("HKM Payment Request", payment_request_doc.amended_from)
            # Only prevent upload if original was uploaded (not just cancelled)
            if original_doc.batch_number and original_doc.request_id:
                frappe.throw(
                    f"The original payment request {payment_request_doc.amended_from} was already uploaded. "
                    "Cannot upload an amended version of an already uploaded document."
                )
    
    # Validation: Check if there are any amended versions of this document that were uploaded
    amended_docs = frappe.get_all(
        "HKM Payment Request",
        filters={
            "amended_from": payment_request_doc.name,
            "docstatus": 1,
        },
        fields=["name", "batch_number", "request_id"],
    )
    for amended_doc in amended_docs:
        if amended_doc.batch_number and amended_doc.request_id:
            frappe.throw(
                f"An amended version {amended_doc.name} of this payment request was already uploaded. "
                "Cannot upload the original document."
            )
    
    bank = frappe.db.get_value("Bank Account", payment_request_doc.bank_account, "bank")
    bank_config_found = False
    if bank == AUBANK:
        if not frappe.db.exists(
            "AU Bank Account", {"bank_account": payment_request_doc.bank_account}
        ):
            frappe.throw("The AU Bank doesn't have the configuration set in ERP.")
        bank_config_found = True
        au_bank_doc = frappe.get_doc(
            "AU Bank Account", {"bank_account": payment_request_doc.bank_account}
        )
        au_bank_doc.payout(payment_request_doc)

    if not bank_config_found:
        frappe.throw("No Bank Config available.")

def test_payment_enquiry():
    payment_request_doc = frappe.get_doc("HKM Payment Request", "BHKMJ000332")
    payment_request_doc.request_id = "BHKMJ000332"
    payment_request_doc.batch_number = "0213122510752"
    bank = frappe.db.get_value("Bank Account", payment_request_doc.bank_account, "bank")
    bank_config_found = False
    status_response = None

    if bank == AUBANK:
        if not frappe.db.exists(
            "AU Bank Account", {"bank_account": payment_request_doc.bank_account}
        ):
            frappe.throw("The AU Bank doesn't have the configuration set in ERP.")
        bank_config_found = True
        au_bank_doc = frappe.get_doc(
            "AU Bank Account", {"bank_account": payment_request_doc.bank_account}
        )
        status_response = au_bank_doc.payment_enquiry(payment_request_doc)

    if not bank_config_found:
        frappe.throw("No Bank Config available.")

    return status_response

@frappe.whitelist()
def get_status(payment_request):
    payment_request_doc = frappe.get_doc("HKM Payment Request", payment_request)
    bank = frappe.db.get_value("Bank Account", payment_request_doc.bank_account, "bank")
    bank_config_found = False
    status_response = None

    if bank == AUBANK:
        if not frappe.db.exists(
            "AU Bank Account", {"bank_account": payment_request_doc.bank_account}
        ):
            frappe.throw("The AU Bank doesn't have the configuration set in ERP.")
        bank_config_found = True
        au_bank_doc = frappe.get_doc(
            "AU Bank Account", {"bank_account": payment_request_doc.bank_account}
        )
        status_response = au_bank_doc.payment_enquiry(payment_request_doc)

    if not bank_config_found:
        frappe.throw("No Bank Config available.")

    return status_response


@frappe.whitelist()
def make_payment_request_from_pi(source_name, target_doc=None):
    from frappe.model.mapper import get_mapped_doc

    def set_missing_values(source, target):
        party_bank_account = (
            frappe.db.get_value(
                "Bank Account", {"party_type": "Supplier", "party": source.party}
            )
            or ""
        )
        target.append(
            "items",
            {
                "document_type": source.doctype,
                "document_name": source.name,
                "amount": source.grand_total,
                "supplier": source.supplier,
            },
        )

    doclist = get_mapped_doc(
        "Purchase Invoice",
        source_name,
        {
            "Purchase Invoice": {
                "doctype": "HKM Payment Request",
            }
        },
        target_doc,
        set_missing_values,
    )

    return doclist

@frappe.whitelist()
def update_payment_request_status():
    print("Updating payment request status")
    """Update status for all pending payment requests"""
    for i in frappe.db.sql(
        """
        SELECT name, batch_number, request_id, docstatus
        FROM `tabHKM Payment Request`
        WHERE docstatus = 1
        AND status NOT IN ("Paid", "Failed")
    """,
        as_dict=True,
    ):
        request_status = ""

        if i.docstatus == 2:
            request_status = "Cancelled"
        elif i.docstatus == 1:
            if not i.batch_number and not i.request_id:
                request_status = "Submitted"
            elif i.batch_number and i.request_id:
                request_status = "Uploaded"

                # {
                #     "TransactionEnquiryResponse": {
                #         "uniqueRequestId": "BRKM000061",
                #         "batchNo": "022511258519",
                #         "transactionRequestId": "BRKM000061",
                #         "noOfTransactions": 2,
                #         "transactionEnquiryDetails": [
                #             {
                #                 "payableCurrency": "INR",
                #                 "amount": "37045",
                #                 "errorMessage": "",
                #                 "errorCode": "",
                #                 "paymentMethodName": "NEFT",
                #                 "valueDate": "2025-11-25",
                #                 "transactionRefNo": "s15k880n0b",
                #                 "utr": "",
                #                 "beneficiaryName": "Solanki and Solanki Refrigeration",
                #                 "beneficiaryAccount": "094720110000238",
                #                 "remitterAccountNo": "1781220613042120",
                #                 "statusCode": "100",
                #                 "status": "OPEN",
                #             },
                #             {
                #                 "payableCurrency": "INR",
                #                 "amount": "37045",
                #                 "errorMessage": "",
                #                 "errorCode": "",
                #                 "paymentMethodName": "NEFT",
                #                 "valueDate": "2025-11-25",
                #                 "transactionRefNo": "s15lqrg4fk",
                #                 "utr": "",
                #                 "beneficiaryName": "Solanki and Solanki Refrigeration",
                #                 "beneficiaryAccount": "094720110000238",
                #                 "remitterAccountNo": "1781220613042120",
                #                 "statusCode": "100",
                #                 "status": "OPEN",
                #             },
                #         ],
                #         "responseMessage": "SUCCESS",
                #         "batchStatusCode": "00",
                #         "batchStatus": "SUCCESS",
                #         "responseCode": "00",
                #     }
                # }
                # Get status from bank API

                {
                    "TransactionEnquiryResponse": {
                        "uniqueRequestId": "BHKMJ000287",
                        "batchNo": "0225112511172",
                        "transactionRequestId": "BHKMJ000287",
                        "noOfTransactions": 0,
                        "errorMessage": "Beneficiary Account No should be alphanumeric (6000110591 ),Beneficiary Account No should be alphanumeric (6000110591 )",
                        "responseMessage": "SUCCESS",
                        "batchStatusCode": "99",
                        "batchStatus": "FAILED",
                        "responseCode": "00",
                    }
                }
                try:
                    status = get_status(i.name)
                    if status:
                        batch_status_code = None
                        response_data = json.loads(status)["TransactionEnquiryResponse"]
                        
                        # Check if transactionEnquiryDetails exists (successful batch)
                        if "transactionEnquiryDetails" in response_data:
                            transaction_details = response_data["transactionEnquiryDetails"]
                            if transaction_details and len(transaction_details) > 0:
                                batch_status_code = transaction_details[0]["statusCode"]
                        
                        # If batchStatusCode is not "00", use batch level status
                        if response_data.get("batchStatusCode") != "00":
                            batch_status_code = response_data.get("batchStatusCode")

                        # Set request status based on status code
                        if batch_status_code == "99":
                            request_status = "Failed"
                        elif batch_status_code == "100":
                            request_status = "Approval Pending"
                        elif batch_status_code == "00":
                            request_status = "Paid"
                        else:
                            request_status = "Uploaded"
                except Exception as e:
                    frappe.log_error(
                        title=f"Payment Status Update Error - {i.name}",
                        message=f"Error updating status for {i.name}: {str(e)}\nStatus Response: {status if 'status' in locals() else 'N/A'}"
                    )
                    # Continue to next record instead of breaking the entire process
                    continue

        if request_status:
            print(i.name, request_status)
            frappe.db.set_value("HKM Payment Request", i.name, "status", request_status)
    frappe.db.commit()  # v16: REVIEW - check if needed

    return
