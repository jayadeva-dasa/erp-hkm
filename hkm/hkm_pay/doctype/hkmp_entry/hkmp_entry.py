# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

import json
from unittest import result

import requests
from frappe.utils.password import get_decrypted_password
from hkm.hkm_pay.doctype.hkmp_entry.payment import update_user_balance
from hkm.hkm_integration.doctype.indusind_bank_integration.indusind_bank_integration import (
    check_transaction_status,
)
from hkm.hkm_integration.doctype.au_bank_integration.au_payment_api import (
    check_au_transaction_status,
    decrypt_gcm,
    encrypt_gcm,
    get_au_bank_settings,
)
import frappe
import re
from hkm.hkm_pay.constant import (
    HKMP_USER,
    USER,
    SUCCESS,
    PROCESSING,
    PENDING,
    FAILED,
    AVAILABLE_BALANCE,
    UPI,
    UPID,
)
from frappe.model.document import Document


class HKMPEntry(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        account_number: DF.Data | None
        amended_from: DF.Link | None
        amount: DF.Currency
        api_payload: DF.JSON | None
        api_response: DF.JSON | None
        approval_status: DF.Literal["Not Sent for Approval",
                                    "Approval Pending", "Approved", "Rejected"]
        approving_authority: DF.Link | None
        bank_account: DF.Link | None
        beneficiary_name: DF.Data | None
        bill_received: DF.Check
        company: DF.Link
        customer_ref_no: DF.Data | None
        debited_from: DF.Link | None
        ifsc_code: DF.Data | None
        is_return: DF.Check
        mobile_number: DF.Int
        remarks: DF.Data
        status: DF.Literal["Pending", "Processing", "Success", "Failed"]
        transaction_tracking_id: DF.Data | None
        transfer_type: DF.Literal["UPI", "IMPS", "NEFT", "RTGS"]
        upi_id: DF.Data | None
        user: DF.Link
        utr: DF.Data | None
    # end: auto-generated types

    def before_insert(self):
        if self.bill_received or self.is_return:
            return frappe.throw(
                "Bill received or is return cannot be set at the time of creation"
            )
        if not self.company:
            self.company = "Hare Krishna Movement Jaipur"

        if not self.transaction_tracking_id:
            self.transaction_tracking_id = self.name
            
    def after_insert(self):
        if not self.beneficiary_name:
            frappe.enqueue(
                update_beneficiary_name,
                queue="short",
                entry=self.name,
                
            )

    def validate(self):
        """Validate all requirements."""

        old_doc = self.get_doc_before_save()
        if old_doc:
            return

        # Fetch all user fields once for validation
        self._user_data = frappe.db.get_value(
            HKMP_USER,
            {USER: self.user},
            ["per_transaction_limit", "available_daily_limit", "available_amt"],
            as_dict=True,
        )

        self.validate_user()
        self.validate_remarks()
        self.validate_amount()
        self.validate_per_transaction_limit()
        self.validate_available_balance()
        self.validate_concurrent_failed_transactions()
        self.validate_company()

        # self.validate_daily_limit()
        # self.validate_transfer_type_requirements()

    def validate_company(self):
        """Validate company is valid."""
        if self.company:
            parent = frappe.db.get_value(
                "HKMP User", {"user": self.user}, "name")
            if not frappe.db.exists(
                "HKM Active Company",
                {"parenttype": "HKMP User", "parent": parent, "company": self.company},
            ):
                return frappe.throw(
                    "You are not authorized to make payment to this company"
                )

    def validate_concurrent_failed_transactions(self):
        """Check if user has concurrent failed transactions."""
        now = frappe.utils.now()
        five_min_ago = frappe.utils.add_to_date(now, minutes=-5)

        failed_transactions = frappe.get_all(
            "HKMP Entry",
            filters={
                "user": self.user,
                "status": "Failed",
                "docstatus": 1,
                "creation": ["between", [five_min_ago, now]],
                "upi_id": self.upi_id,
            },
        )
        if len(failed_transactions) >= 3:
            frappe.throw(
                "You have concurrent failed transactions please try after 5 minutes or use different UPI ID"
            )

    def validate_per_transaction_limit(self):
        """Check if amount exceeds per transaction limit."""
        if self._user_data and self._user_data.per_transaction_limit < self.amount:
            frappe.throw("Amount cannot be greater than per transaction limit")

    def validate_daily_limit(self):
        """Check if amount exceeds daily limit."""
        daily_limit = max(
            0, (self._user_data.available_daily_limit or 0) if self._user_data else 0
        )
        if daily_limit == 0 or daily_limit < self.amount:
            frappe.throw("Amount cannot be greater than daily limit")

    def validate_available_balance(self):
        """Check if user has sufficient balance."""
        # Ensure balance is not negative
        available_balance = max(
            0, (self._user_data.available_amt or 0) if self._user_data else 0
        )

        # Check for sufficient balance
        if available_balance == 0 or available_balance < self.amount:
            frappe.throw("Insufficient balance")

    def validate_amount(self):
        """Validate amount is not zero."""
        if self.amount == 0:
            frappe.throw("Amount cannot be zero")

    def validate_remarks(self):
        """Validate remarks length."""
        if self.remarks and len(self.remarks) < 5:
            frappe.throw("Remarks cannot be less than 5 characters")

    def validate_user(self):
        """Check if user is authorized to make payment."""
        if (
            not frappe.db.exists(HKMP_USER, {USER: self.user})
            or "HKMP User" not in frappe.get_roles(self.user)
            or not frappe.db.get_value(HKMP_USER, {USER: self.user}, "enabled")
        ):
            frappe.throw("Not Authorized To Make HKMP Payment")

        setting_doc = frappe.get_cached_doc("HKMP Setting")

        if setting_doc.enable_period_restriction_for_bill_submission and frappe.db.get_value(HKMP_USER, {USER: self.user}, "bill_submission_restriction_enabled"):
            frappe.throw("Bills Pending are Required to be Submitted")

    def before_cancel(self):
        if self.status == SUCCESS:
            frappe.throw("Transaction already successful, cannot cancel")

        self.status = FAILED

    def on_update(self):
        # update_user_balance(self.user)



        frappe.enqueue(
            method=update_user_balance,
            payment_user=self.user,
        )
        # frappe.enqueue(
        #     method=update_bill_restriction_status,
        #     payment_user=self.user,
        # )
        # update_bill_restriction_status(self.user)

    def notify_user(self):
        setting_doc = frappe.get_cached_doc("HKMP Setting")
        if self.status == SUCCESS:
            frappe.get_doc(
                {
                    "doctype": "App Notification",
                    "app": setting_doc.firebase_admin_app,
                    "user": self.user,
                    "subject": "HKMP Payment Success",
                    "message": f"Your payment of {self.amount} has been successful.",
                }
            ).insert(ignore_permissions=True)
        else:
            frappe.get_doc(
                {
                    "doctype": "App Notification",
                    "app": setting_doc.firebase_admin_app,
                    "user": self.user,
                    "subject": "HKMP Payment Failed",
                    "message": f"Your payment of {self.amount} has failed.",
                }
            ).insert(ignore_permissions=True)

        frappe.db.commit()  # v16: REVIEW - check if needed
        

def update_beneficiary_name(entry):
    try:
        # If doc is passed as name string, normalize it
        doc = frappe.get_doc("HKMP Entry", entry)

        vpa_result = validate_vpa_id(doc.beneficiary_vpa)

        if not vpa_result:
            frappe.log_error(
                title="VPA Validation Failed",
                message=f"Empty response while validating VPA {doc.beneficiary_vpa} for user {doc.user}"
            )
            return

        result = json.loads(vpa_result) if isinstance(vpa_result, str) else vpa_result

        beneficiary_name = (
            result.get("data", {})
            .get("transactionInfo", {})
            .get("attributes", {})
            .get("accountname", "")
        )

        if not beneficiary_name:
            frappe.log_error(
                title="Invalid VPA Response",
                message=f"Account name not found in response for {doc.beneficiary_vpa}\nResponse: {result}"
            )
            return

        # doc.db_set("beneficiary_name", beneficiary_name)
        frappe.db.set_value("HKMP Entry", entry, "beneficiary_name", beneficiary_name)
        frappe.db.commit()  # v16: REVIEW - check if needed

    except Exception as e:
        frappe.log_error(
            title="VPA Validation Failed",
            message=f"Failed to validate VPA {doc.beneficiary_vpa}: {str(e)}\n{frappe.get_traceback()}"
        )

def update_transaction_status():
    """Update transaction status for all pending/processing entries.
    Supports both IndusInd Bank and AU Bank integrations.
    """
    import json

    # Check for both "Pending" and "Processing" status
    entries = frappe.get_all(
        "HKMP Entry",
        filters={"status": ["in", [PENDING, PROCESSING]]},
        fields=[
            "name",
            "api_payload",
            "api_response",
            "status",
            "amount",
            "user",
            "debited_from",
            "company",
            "transaction_tracking_id",
        ],
    )

    for entry_data in entries:
        try:
            entry_doc = frappe.get_doc("HKMP Entry", entry_data.name)

            # Skip if no api_payload (payment not initiated)
            if not entry_doc.api_payload:
                frappe.log_error(
                    title="Transaction Status Update - Skipped (No API Payload)",
                    message=f"Entry {entry_doc.name} has no api_payload, skipping status check.",
                )
                continue

            # Skip if no transaction_tracking_id (cannot check status)
            if not entry_doc.transaction_tracking_id:
                frappe.log_error(
                    title="Transaction Status Update - Skipped (No Tracking ID)",
                    message=f"Entry {entry_doc.name} has no transaction_tracking_id, skipping status check.",
                )
                continue

            # Determine which bank integration based on debited_from
            debited_from = entry_doc.debited_from or ""
            is_au_bank = "AU Bank Integration" in debited_from
            is_indusind_bank = "IndusInd Bank Integration" in debited_from

            if is_au_bank:
                # Handle AU Bank status check
                _update_au_bank_status(entry_doc)
            elif is_indusind_bank:
                # Handle IndusInd Bank status check
                _update_indusind_bank_status(entry_doc)
            else:
                # Try to determine from company or api_payload structure
                if entry_doc.company:
                    # Check if company belongs to AU Bank
                    from hkm.hkm_pay.constant import HKM_ACTIVE_COMPANY

                    au_companies = [
                        c.strip() if c else ""
                        for c in frappe.get_all(
                            HKM_ACTIVE_COMPANY,
                            filters={"parenttype": "AU Bank Integration"},
                            fields=["company"],
                            pluck="company",
                        )
                    ]
                    if entry_doc.company.strip() in au_companies:
                        _update_au_bank_status(entry_doc)
                    else:
                        # Default to IndusInd
                        _update_indusind_bank_status(entry_doc)
                else:
                    # Default to IndusInd if cannot determine
                    _update_indusind_bank_status(entry_doc)

        except Exception as e:
            frappe.log_error(
                title="Transaction Status Update Error",
                message=f"Error updating status for {entry_data.name}: {str(e)}\n{frappe.get_traceback()}",
            )
            continue

    # Commit all updates after processing all entries
    frappe.db.commit()  # v16: REVIEW - check if needed


def _update_indusind_bank_status(entry_doc):
    """Update transaction status for IndusInd Bank entries."""
    import json

    try:
        # Parse api_payload to get order number
        # api_payload = json.loads(entry_doc.api_payload)
        order_no = entry_doc.transaction_tracking_id

        if not order_no:
            frappe.log_error(
                title="Missing Order Number",
                message=f"No order number found in api_payload for {entry_doc.name}",
            )
            return

        # Check transaction status
        status_response = check_transaction_status(
            org_psp_ref_no=order_no, company=entry_doc.company
        )

        # Skip if status check failed
        if not status_response or not status_response.get("success"):
            frappe.log_error(
                title="Status Check Failed",
                message=f"Cannot check status for {entry_doc.name}: {status_response.get('error') if status_response else 'No response'}",
            )
            return

        # Extract transaction status
        transaction_status = status_response.get("decrypted_response", {}).get(
            "apiResp", {}
        )
        payment_status = transaction_status.get("status")

        # Determine new status
        old_status = entry_doc.status
        if payment_status == "S":
            new_status = SUCCESS
        elif payment_status == "F":
            new_status = FAILED
        else:
            new_status = PROCESSING

        # Update api_response with transaction status
        existing_response = (
            json.loads(entry_doc.api_response) if entry_doc.api_response else {}
        )
        updated_response = {**existing_response, **transaction_status}

        entry_doc.api_response = json.dumps(updated_response)

        if entry_doc.utr != transaction_status.get("npciTransId"):
            entry_doc.utr = transaction_status.get("npciTransId")

        if old_status != new_status:
            entry_doc.status = new_status
            entry_doc.notify_user()

        entry_doc.flags.ignore_permissions = True
        entry_doc.save(ignore_permissions=True)

    except Exception as e:
        frappe.log_error(
            title="IndusInd Bank Status Update Error",
            message=f"Error updating IndusInd status for {entry_doc.name}: {str(e)}\n{frappe.get_traceback()}",
        )


def test_update_au_bank_status():

    entry_doc = frappe.get_doc("HKMP Entry", "EPYSSQREP093191")

    _update_au_bank_status(entry_doc)


def _update_au_bank_status(entry_doc):
    """Update transaction status for AU Bank entries."""
    import json

    try:
        if not entry_doc.company:
            frappe.log_error(
                title="Missing Company",
                message=f"Company is required for AU Bank status check for {entry_doc.name}",
            )
            return

        # Extract transaction ID from api_response or api_payload
        transaction_id = entry_doc.transaction_tracking_id

        # Check transaction status
        status_response = check_au_transaction_status(
            transaction_id=transaction_id, company=entry_doc.company
        )

        # Skip if status check failed
        if not status_response or not status_response.get("success"):
            frappe.log_error(
                title="AU Bank Status Check Failed",
                message=f"Cannot check status for {entry_doc.name}: {status_response.get('error') if status_response else 'No response'}",
            )
            return

        # Extract transaction status and nested data structures
        transaction_status = status_response.get("transaction_status", {})
        status_data = status_response.get("data", {})
        inner_data = (
            status_data.get("data", {}) if isinstance(
                status_data, dict) else {}
        )

        # If transaction_status is empty, extract directly from nested structure
        if not transaction_status and inner_data:
            transaction_info = inner_data.get("transactionInfo", {})
            if transaction_info:
                transaction_status = transaction_info

        # Determine new status based on AU Bank response
        old_status = entry_doc.status

        # Extract response codes and messages from nested structure
        # Priority: vpaResponseStatus > result > attributes
        vpa_status = inner_data.get("vpaResponseStatus", {})
        vpa_response_code = str(
            vpa_status.get("responseCode", "")
            or status_response.get("vpa_response_code", "")
            or ""
        ).strip()
        vpa_message = (
            str(
                vpa_status.get("message", "")
                or status_response.get("vpa_message", "")
                or ""
            )
            .strip()
            .upper()
        )

        result_section = transaction_status.get("result", {})
        result_code = str(
            result_section.get("code", "")
            or status_response.get("result_code", "")
            or ""
        ).strip()
        result_message = (
            str(
                result_section.get("message", "")
                or status_response.get("result_message", "")
                or ""
            )
            .strip()
            .upper()
        )
        codedescription = (
            str(
                result_section.get("codedescription", "")
                or status_response.get("codedescription", "")
                or ""
            )
            .strip()
            .upper()
        )

        attributes = transaction_status.get("attributes", {})
        attributes_status = str(attributes.get(
            "status", "") or "").strip().upper()
        attributes_code = str(attributes.get("code", "") or "").strip()

        # Determine status based on response codes and messages
        # Priority order: vpaResponseStatus > result > attributes
        # Response code patterns:
        # - "00" = Success
        # - "99" = Failed (unless codedescription indicates pending)
        # - "11" = Pending

        new_status = None

        # Check vpaResponseStatus first (primary indicator)
        if vpa_response_code == "00":
            new_status = SUCCESS
        elif vpa_response_code == "11":
            new_status = PROCESSING
        elif vpa_response_code == "99":
            # Check if it's actually pending based on codedescription
            if "11" in codedescription and "PENDING" in codedescription:
                new_status = PROCESSING
            elif "FAILURE" in vpa_message or "FAILURE" in result_message:
                new_status = FAILED
            else:
                # Default to failed if code is 99 and no pending indicator
                new_status = FAILED
        # Check result section if vpaResponseStatus not available
        elif result_code == "00":
            new_status = SUCCESS
        elif result_code == "11":
            new_status = PROCESSING
        elif result_code == "99":
            # Check if it's actually pending (codedescription contains "11 | Pending")
            if "11" in codedescription and "PENDING" in codedescription:
                new_status = PROCESSING
            elif "FAILURE" in result_message:
                new_status = FAILED
            else:
                # Default to failed if code is 99
                new_status = FAILED
        # Check if message indicates pending
        elif "PENDING" in result_message or "PENDING" in vpa_message:
            new_status = PROCESSING
        # Check attributes
        elif attributes_status == "SUCCESS" or attributes_code == "00":
            new_status = SUCCESS
        elif attributes_code == "11":
            new_status = PROCESSING
        elif attributes_code == "99":
            new_status = FAILED
        else:
            # Default to processing if cannot determine
            new_status = PROCESSING

        # Log status determination only if status actually changed
        if old_status != new_status:
            frappe.log_error(
                title=f"AU Bank Status Update - {old_status} → {new_status}",
                message=f"Entry {entry_doc.name} status changed from {old_status} to {new_status}. Indicators: vpa_response_code={vpa_response_code}, vpa_message={vpa_message}, result_code={result_code}, result_message={result_message}, codedescription={codedescription}, attributes_status={attributes_status}, attributes_code={attributes_code}",
            )

        updated_response = {
            "transaction_status": transaction_status,
            "status_check_response": status_response.get("data", {}),
        }

        entry_doc.api_response = json.dumps(updated_response)

        # Update UTR and customer_ref_no from AU Bank response
        # Get externalReferenceNumber from status response
        external_ref = inner_data.get(
            "externalReferenceNumber", ""
        ) or status_response.get("externalReferenceNumber", "")

        # Update UTR from transaction ID or RefId
        utr_value = transaction_status.get(
            "transactionid") or attributes.get("RefId")
        if utr_value and entry_doc.utr != utr_value:
            entry_doc.utr = utr_value

        # Update customer_ref_no - priority: externalReferenceNumber > custrefnumber > RefId
        customer_ref = (
            external_ref or attributes.get(
                "custrefnumber") or attributes.get("RefId")
        )
        if customer_ref and entry_doc.customer_ref_no != customer_ref:
            entry_doc.customer_ref_no = customer_ref

        if old_status != new_status:
            entry_doc.status = new_status
            entry_doc.notify_user()

        entry_doc.flags.ignore_permissions = True
        entry_doc.save(ignore_permissions=True)

    except Exception as e:
        frappe.log_error(
            title="AU Bank Status Update Error",
            message=f"Error updating AU Bank status for {entry_doc.name}: {str(e)}\n{frappe.get_traceback()}",
        )


def update_daily_limit():
    """Update daily limit for all users."""
    users = frappe.get_all(
        "HKMP User",
        pluck="name",
    )
    for user in users:
        user_doc = frappe.get_doc("HKMP User", user)
        user_doc.available_daily_limit = user_doc.daily_limit
        user_doc.save(ignore_permissions=True)
    frappe.db.commit()  # v16: REVIEW - check if needed


@frappe.whitelist()
def check_transaction_status_hkmp_entry(entry_name):
    """Check transaction status for a specific entry.

    Args:
        entry_name: Name of the HKMP Entry document

    Returns:
        dict: Status check response with success flag and message/data
    """
    try:
        entry_doc = frappe.get_doc("HKMP Entry", entry_name)

        # Check if entry has api_payload (payment initiated)
        if not entry_doc.api_payload:
            return {
                "success": False,
                "error": "Payment not initiated. No API payload found.",
                "message": "This entry does not have an API payload, so status cannot be checked.",
            }

        # Check if entry has transaction_tracking_id
        if not entry_doc.transaction_tracking_id:
            return {
                "success": False,
                "error": "Missing transaction tracking ID.",
                "message": "This entry does not have a transaction tracking ID, so status cannot be checked.",
            }

        # Store old status for comparison
        old_status = entry_doc.status

        # Determine which bank integration based on debited_from
        debited_from = entry_doc.debited_from or ""
        is_au_bank = "AU Bank Integration" in debited_from
        is_indusind_bank = "IndusInd Bank Integration" in debited_from

        if is_au_bank:
            # Handle AU Bank status check
            _update_au_bank_status(entry_doc)
        elif is_indusind_bank:
            # Handle IndusInd Bank status check
            _update_indusind_bank_status(entry_doc)
        else:
            # Try to determine from company or api_payload structure
            if entry_doc.company:
                # Check if company belongs to AU Bank
                from hkm.hkm_pay.constant import HKM_ACTIVE_COMPANY

                au_companies = [
                    c.strip() if c else ""
                    for c in frappe.get_all(
                        HKM_ACTIVE_COMPANY,
                        filters={"parenttype": "AU Bank Integration"},
                        fields=["company"],
                        pluck="company",
                    )
                ]
                if entry_doc.company.strip() in au_companies:
                    _update_au_bank_status(entry_doc)
                else:
                    # Default to IndusInd
                    _update_indusind_bank_status(entry_doc)
            else:
                # Default to IndusInd if cannot determine
                _update_indusind_bank_status(entry_doc)

        # Reload document to get updated status
        entry_doc.reload()
        new_status = entry_doc.status

        # Prepare response
        response_data = {
            "success": True,
            "old_status": old_status,
            "new_status": new_status,
            "status_changed": old_status != new_status,
            "transaction_tracking_id": entry_doc.transaction_tracking_id,
            "utr": entry_doc.utr,
            "customer_ref_no": entry_doc.customer_ref_no,
        }

        # Include API response if available
        if entry_doc.api_response:
            try:
                response_data["api_response"] = json.loads(
                    entry_doc.api_response)
            except:
                response_data["api_response"] = entry_doc.api_response

        return response_data

    except Exception as e:
        frappe.log_error(
            title="Check Transaction Status Error",
            message=f"Error checking status for {entry_name}: {str(e)}\n{frappe.get_traceback()}",
        )
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to check transaction status: {str(e)}",
        }


@frappe.whitelist()
def validate_vpa_id(vpa_id):
    """Validate VPA ID is valid."""
    setting = frappe.get_cached_doc("AU Bank Integration")
    integration_doc = setting.npci_integration[0]
    if integration_doc:
        company = integration_doc.company
        settings = get_au_bank_settings(company)
        access_token = settings["access_token"]
        payload = {
            "vpa": vpa_id,
            "isVpa": True,
            "type": "INET",
        }
        json_payload = json.dumps(payload)
        encrypted_payload = encrypt_gcm(
            json_payload, settings["encryption_key"], settings["salt_key"]
        )
        request_body = {"encvalue": encrypted_payload}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }

        response = requests.post(
            settings["verify_vpa_url"], headers=headers, json=request_body, timeout=30
        )
        if response.status_code == 200:
            try:
                if response.text.strip():
                    data = response.json()
                    if "encvalue" in data:
                        decrypted_response = decrypt_gcm(
                            data["encvalue"],
                            settings["encryption_key"],
                            settings["salt_key"],
                        )
                        return decrypted_response
                    else:
                        return data
            except Exception as e:
                frappe.log_error(
                    title="Validate VPA ID Error",
                    message=f"Error validating VPA ID: {str(e)}\n{frappe.get_traceback()}",
                )
                return f"Error validating VPA ID: {str(e)}"
        else:
            return f"Error validating VPA ID: {response.text}"


def update_hkmp_payee_directory():
    """Update HKMP Payee Directory."""

    users = frappe.get_all("HKMP User", pluck="name")
    total_users = len(users)
    processed_count = 0
    error_count = 0

    frappe.logger().info(
        f"Starting HKMP Payee Directory update for {total_users} users")

    for user in users:
        try:
            # Get entries that need to be updated
            last_paid_entries = frappe.db.sql(
                """
                SELECT
                t.user               AS hkmp_user,
                t.upi_id             AS beneficiary_vpa,
                t.amount             AS last_paid_amount,
                t.creation           AS last_payment_date
            FROM `tabHKMP Entry` t
            INNER JOIN (
                SELECT
                    user,
                    upi_id,
                    MAX(CONCAT(creation, name)) AS max_row
                FROM `tabHKMP Entry`
                WHERE status = 'Success'
                AND docstatus = 1
                AND transfer_type = 'UPI'
                AND user = %(user)s
                GROUP BY user, upi_id
            ) latest
            ON latest.user = t.user
            AND latest.upi_id = t.upi_id
            AND CONCAT(t.creation, t.name) = latest.max_row

            LEFT JOIN `tabHKMP Payee Directory` d
            ON d.hkmp_user = t.user
            AND d.beneficiary_vpa = t.upi_id

            WHERE
                d.name IS NULL                     -- NEW payee
            OR d.paid_amount <> t.amount          -- amount changed
            OR d.payment_date <> t.creation;      -- date changed

        """,
                {
                    "user": user,
                },
                as_dict=True,
            )

            if not last_paid_entries:
                continue

            for entry in last_paid_entries:
                try:
                    # Validate VPA ID with timeout handling

                    existing_record = frappe.db.get_value(
                        "HKMP Payee Directory",
                        {"hkmp_user": user, "beneficiary_vpa": entry.beneficiary_vpa},
                        "name"
                    )

                    if existing_record:
                        # Update existing record
                        frappe.db.set_value(
                            "HKMP Payee Directory",
                            existing_record,
                            {
                                "paid_amount": entry.last_paid_amount,
                                "payment_date": entry.last_payment_date,
                            },
                        )
                        continue

                    vpa_result = validate_vpa_id(entry.beneficiary_vpa)

                    if not vpa_result:
                        frappe.log_error(
                            title="VPA Validation Failed",
                            message=f"Failed to validate VPA {entry.beneficiary_vpa} for user {user}"
                        )
                        continue

                    result = json.loads(vpa_result) if isinstance(
                        vpa_result, str) else vpa_result

                    beneficiary_name = (
                        result.get("data", {})
                        .get("transactionInfo", {})
                        .get("attributes", {})
                        .get("accountname", "")
                    )
                    beneficiary_vpa = (
                        result.get("data", {})
                        .get("transactionInfo", {})
                        .get("attributes", {})
                        # Fallback to entry VPA if not found
                        .get("VPA", entry.beneficiary_vpa)
                    )

                    if not beneficiary_vpa:
                        frappe.log_error(
                            title="Invalid VPA Response",
                            message=f"No VPA found in response for {entry.beneficiary_vpa}"
                        )
                        continue

                    # Check if record exists

                        # Create new record
                    frappe.get_doc(
                        {
                            "doctype": "HKMP Payee Directory",
                            "hkmp_user": user,
                            "beneficiary": beneficiary_name,
                            "beneficiary_vpa": beneficiary_vpa,
                            "paid_amount": entry.last_paid_amount,
                            "payment_date": entry.last_payment_date,
                        }
                    ).insert(ignore_permissions=True)

                    # Commit after each successful update to avoid long-running transactions
                    frappe.db.commit()  # v16: REVIEW - check if needed

                except Exception as entry_error:
                    frappe.log_error(
                        title="HKMP Payee Directory Entry Update Error",
                        message=f"Error processing entry for user {user}, VPA {entry.beneficiary_vpa}: {str(entry_error)}\n{frappe.get_traceback()}"
                    )
                    error_count += 1
                    continue

            processed_count += 1
            frappe.logger().info(
                f"Processed user {processed_count}/{total_users}: {user}")

        except Exception as user_error:
            frappe.log_error(
                title="HKMP Payee Directory User Processing Error",
                message=f"Error processing user {user}: {str(user_error)}\n{frappe.get_traceback()}"
            )
            frappe.db.rollback()
            error_count += 1
            continue

    # Final commit
    frappe.db.commit()  # v16: REVIEW - check if needed

    summary = f"HKMP Payee Directory update completed. Processed: {processed_count}/{total_users} users, Errors: {error_count}"
    frappe.logger().info(summary)

    return summary
