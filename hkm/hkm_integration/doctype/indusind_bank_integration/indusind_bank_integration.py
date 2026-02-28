# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt
from urllib.parse import quote
from typing import Dict, Any, Optional
import json
import base64
import requests
from typing import Dict, Any

import frappe
from frappe.model.document import Document
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from frappe.utils.password import get_decrypted_password
from hkm.hkm_pay.constant import UPI, PROCESSING, PENDING


class IndusIndBankIntegration(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF
        from hkm.erpnext___custom.doctype.hkm_active_company.hkm_active_company import (
            HKMActiveCompany,
        )
        from hkm.hkm_integration.doctype.indusind_bank_integration_detail.indusind_bank_integration_detail import (
            IndusIndBankIntegrationDetail,
        )

        active_company: DF.Table[HKMActiveCompany]
        encryption_key: DF.Password
        ibl_client_id: DF.Data
        ibl_client_password: DF.Password
        mcc: DF.Data
        merchant_id: DF.Data
        merchant_name: DF.Data
        merchant_vpa: DF.Data
        npci_integration: DF.Table[IndusIndBankIntegrationDetail]
        payment_url: DF.Data
        transaction_status_url: DF.Data
    # end: auto-generated types

    def get_secret_key(self):
        pass

    def on_update(self):
        old_doc = self.get_doc_before_save()
        if not old_doc:
            return
        
        frappe.cache().hdel("hkm_box", "indusind_active_companies")
        frappe.cache().hdel("hkm_box", "indusind_npci_integration")

        




def get_password_safe(docname, encrypted_value, fieldname):
    try:
        return get_decrypted_password(
            doctype="IndusInd Bank Integration Detail",
            name=docname,
            fieldname=fieldname,
            raise_exception=False,
        )
    except Exception:
        return None



def _get_indusind_cached_row(company):
    cache = frappe.cache()
    cache_key = f"indusind_npci_integration_{company}"

    cached = cache.hget("hkm_box", cache_key)
    if cached is not None:
        return cached

    settings_doc = frappe.get_cached_doc("IndusInd Bank Integration")
    settings_doc.flags.ignore_permissions = True

    for row in settings_doc.npci_integration:
        if row.company != company:
            continue

        safe_data = frappe._dict(
            row_name=row.name,
            ibl_client_id=row.ibl_client_id,
            ibl_client_password=row.ibl_client_password,
            mcc=row.mcc,
            merchant_id=row.merchant_id,
            merchant_name=row.merchant_name,
            merchant_vpa=row.merchant_vpa,
            payment_url=row.payment_url,
            transaction_status_url=row.transaction_status_url,
            encryption_key=row.encryption_key,
        )

        cache.hset("hkm_box", cache_key, safe_data)
        return safe_data

    return None





def get_indusind_bank_integration_settings(company: str = None):
    data = _get_indusind_cached_row(company)
    if not data:
        return None

    data = frappe._dict(data)

    data.update({
        "encryption_key": get_password_safe(
            data.row_name, data.encryption_key, "encryption_key"
        ),
        "ibl_client_password": get_password_safe(
            data.row_name, data.ibl_client_password, "ibl_client_password"
        ),
    })

    return data



def transfer_payment_via_indusind_bank(entry_doc: Document):
    """Transfer payment via IndusInd Bank - supports UPI and Bank Transfer."""
    # setting_doc = frappe.get_cached_doc("IndusInd Bank Integration")
    # setting_doc.flags.ignore_permissions = True

    if entry_doc.transfer_type == UPI:
        return initiate_m2p_upi_payment(
            beneficiary_vpa=entry_doc.upi_id,
            beneficiary_name=entry_doc.beneficiary_name,
            amount=entry_doc.amount,
            txn_note=entry_doc.remarks,
            order_number=entry_doc.transaction_tracking_id,
            setting_doc=get_indusind_bank_integration_settings(entry_doc.company),
        )
    else:
        return initiate_m2p_bank_transfer_payment(
            beneficiary_name=entry_doc.beneficiary_name,
            beneficiary_account_number=entry_doc.account_number,
            beneficiary_ifsc_code=entry_doc.ifsc_code,
            amount=entry_doc.amount,
            txn_note=entry_doc.remarks,
            order_number=entry_doc.transaction_tracking_id,
            setting_doc=get_indusind_bank_integration_settings(entry_doc.company),
        )


def check_transaction_status(
    org_txn_id: str = None,
    org_psp_ref_no: str = None,
    on_behalf_of: str = "PAYER",
    device_id: str = "354303082131095",
    mobile_no: str = "917777080853",
    org_txn_date: str = None,
    sim_id: str = "8991000900877608334",
    psp_ref_no: str = None,
    time_stamp: str = None,
    setting_doc: Document = None,
    company: str = None,
) -> Dict[str, Any]:
    """
    Check transaction status using either orgPspRefNo or org_txn_id.

    Returns:
        Dict with success status and transaction status details
    """

    setting_doc = get_indusind_bank_integration_settings(company)


    
    import time
    from datetime import datetime

    if on_behalf_of not in ["PAYEE", "PAYER"]:
        return {"success": False, "error": f"on_behalf_of must be 'PAYEE' or 'PAYER'"}

    if not org_psp_ref_no and not org_txn_id:
        return {
            "success": False,
            "error": "Either org_psp_ref_no or org_txn_id required",
        }

    # Use the order number as pspRefNo if not provided (this is the correct way per API docs)
    if not psp_ref_no:
        psp_ref_no = org_psp_ref_no

    if not time_stamp:
        time_stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    payload = {
        "requestInfo": {
            "pgMerchantId": setting_doc.merchant_id,
            "pspRefNo": psp_ref_no,
            "time_stamp": time_stamp,
        },
        "deviceInfo": {
            "deviceId": device_id[:50],
            "mobileNo": mobile_no[:12],
        },
        "onBehalf_Of": on_behalf_of,
        "action_type": "TRANSACTION_STATUS",
    }

    if sim_id:
        payload["deviceInfo"]["simId"] = sim_id[:20]

    # Only add org_txn_id (don't use orgPspRefNo field based on working example)
    if org_txn_id:
        payload["org_txn_id"] = org_txn_id[:35]
    if org_txn_date:
        payload["org_txn_date"] = org_txn_date

    try:
        # Always use get_password() for password fields
        encryption_key = setting_doc.encryption_key
        if not encryption_key:
            raise ValueError(
                "Encryption key is not set in IndusInd Bank Integration settings"
            )

        encrypted = encrypt_request(encryption_key, payload)
        request_body = {
            "requestMsg": encrypted,
            "pgMerchantId": setting_doc.merchant_id,
        }
        headers = {
            "Content-Type": "application/json",
            "IBL-Client-Id": setting_doc.ibl_client_id,
            "IBL-Client-Secret": setting_doc.ibl_client_password,
        }

        response = requests.post(
            setting_doc.transaction_status_url, json=request_body, headers=headers
        )

        result = {
            "success": response.status_code == 200,
            "status_code": response.status_code,
        }

        if response.status_code == 200:
            response_data = response.json()
            result["raw_response"] = response_data

            if "resp" in response_data:
                resp_value = response_data["resp"]
                if len(resp_value) > 32 and all(
                    c in "0123456789ABCDEFabcdef" for c in resp_value
                ):
                    decrypted_resp = decrypt_response(encryption_key, resp_value)
                    result["decrypted_response"] = decrypted_resp
                    if "apiResp" in decrypted_resp:
                        result["transaction_status"] = decrypted_resp["apiResp"]

            if "apiResp" in response_data:
                result["transaction_status"] = response_data["apiResp"]

            if "requestInfo" in response_data and "status" in response_data:
                result["transaction_status"] = response_data
        else:
            result["error"] = response.text

    except Exception as e:
        result = {"success": False, "error": str(e)}

    return result


# ========================================
# M2P PAY API (Merchant to Person)
# ========================================


def _make_m2p_payment_request(
    payload: Dict[str, Any], setting_doc: Document
) -> Dict[str, Any]:
    """Common function to handle M2P payment requests and responses."""
    result = {
        "success": False,
        "orderNo": payload.get("orderNo"),
        "api_payload": payload,
    }

    try:
        # Always use get_password() for password fields
        encryption_key = setting_doc.encryption_key
        if not encryption_key:
            raise ValueError(
                "Encryption key is not set in IndusInd Bank Integration settings"
            )

        encrypted = encrypt_request(encryption_key, payload)
        request_body = {
            "pgMerchantId": setting_doc.merchant_id,
            "requestMsg": encrypted,
        }
        headers = {
            "Content-Type": "application/json",
            "IBL-Client-Id": setting_doc.ibl_client_id,
            "IBL-Client-Secret": setting_doc.ibl_client_password,
        }

        response = requests.post(
            setting_doc.payment_url, json=request_body, headers=headers, timeout=30
        )

        if response.status_code == 200:
            response_data = response.json()
            result["raw_response"] = response_data

            if "resp" in response_data:
                resp_value = response_data["resp"]
                # Check if resp is encrypted (hex string > 32 chars)
                if len(resp_value) > 32 and all(
                    c in "0123456789ABCDEFabcdef" for c in resp_value
                ):
                    decrypted_response = decrypt_response(encryption_key, resp_value)

                    result["success"] = True
                    result["decrypted_response"] = decrypted_response

                    if "apiResp" in decrypted_response:
                        api_resp = decrypted_response["apiResp"]
                        result["api_response"] = api_resp
                        result["txnId"] = payload.get("orderNo")
                        result["orderNo"] = api_resp.get(
                            "orderNo", payload.get("orderNo")
                        )
                else:
                    result["error"] = (
                        "Response 'resp' field is not in expected encrypted format"
                    )
            else:
                result["error"] = f"Unexpected response format: {response_data}"
        else:
            result["error"] = f"HTTP {response.status_code}: {response.text}"

    except Exception as e:
        result["error"] = str(e)
        frappe.log_error(title="IndusInd Bank Payment Error", message=str(e))

    return result


def initiate_m2p_upi_payment(
    beneficiary_vpa: str,
    beneficiary_name: str,
    amount: str,
    order_number: str = None,
    txn_note: str = "Payment",
    setting_doc: Document = None,
) -> Dict[str, Any]:
    """Initiate M2P UPI payment."""
    import uuid
    import time

    if not order_number:
        timestamp = int(time.time())
        unique_id = str(uuid.uuid4()).replace("-", "")[:20].upper()
        order_number = f"INDB{timestamp}{unique_id}"

    payload = {
        "pgMerchantId": setting_doc.merchant_id,
        "orderNo": order_number,  # Fixed: was "order_number", should be "orderNo"
        "txnNote": txn_note,
        "txnAmount": amount,
        "pyfvaddr": beneficiary_vpa,
        "pyName": beneficiary_name,
    }
    return _make_m2p_payment_request(payload, setting_doc)


def initiate_m2p_bank_transfer_payment(
    beneficiary_name: str,
    beneficiary_account_number: str,
    beneficiary_ifsc_code: str,
    amount: str,
    order_number: str = None,
    txn_note: str = "Payment",
    setting_doc: Document = None,
) -> Dict[str, Any]:
    """Initiate M2P Bank Transfer payment."""
    import uuid
    import time

    if not order_number:
        timestamp = int(time.time())
        unique_id = str(uuid.uuid4()).replace("-", "")[:20].upper()
        order_number = f"INDB{timestamp}{unique_id}"

    payload = {
        "pgMerchantId": setting_doc.merchant_id,
        "orderNo": order_number,  # Fixed: was "order_number", should be "orderNo"
        "txnNote": txn_note,
        "txnAmount": amount,
        "pyName": beneficiary_name,
        "payeeVPAType": "ACCOUNT",
        "payeeAccNo": beneficiary_account_number,
        "payeeIfsc": beneficiary_ifsc_code,
    }
    return _make_m2p_payment_request(payload, setting_doc)


# ========================================
# ENCRYPTION/DECRYPTION UTILITIES
# ========================================


def encrypt_request(merchant_key: str, payload: Dict[str, Any]) -> str:
    """Encrypt request payload using AES-128-ECB with PKCS7 padding."""
    try:
        key_bytes = bytes.fromhex(merchant_key)
        json_payload = json.dumps(payload, separators=(",", ":"))

        plain_bytes = json_payload.encode("utf-8")
        padded_data = pad(plain_bytes, AES.block_size)
        cipher = AES.new(key_bytes, AES.MODE_ECB)
        encrypted_bytes = cipher.encrypt(padded_data)
        return encrypted_bytes.hex().upper()
    except Exception as e:
        raise ValueError(f"Encryption failed: {str(e)}") from e


def decrypt_response(merchant_key: str, encrypted_resp: str) -> Dict[str, Any]:
    """Decrypt response message using AES-128-ECB with PKCS7 padding."""
    try:
        key_bytes = bytes.fromhex(merchant_key)
        try:
            encrypted_bytes = bytes.fromhex(encrypted_resp)
        except ValueError:
            encrypted_bytes = base64.b64decode(encrypted_resp)
        cipher = AES.new(key_bytes, AES.MODE_ECB)
        decrypted_bytes = cipher.decrypt(encrypted_bytes)
        unpadded_data = unpad(decrypted_bytes, AES.block_size)
        json_string = unpadded_data.decode("utf-8")

        return json.loads(json_string)
    except Exception as e:
        raise ValueError(f"Decryption failed: {str(e)}") from e


def generate_qr_code_string(
    payee_vpa: str,
    payee_name: str,
    amount: float,
    transaction_reference: str,
    transaction_note: str,
    merchant_code: str,
    merchant_id: str,
):

    upi_link = generate_upi_payment_link(
        payee_vpa=payee_vpa,
        payee_name=payee_name,
        amount=amount,
        transaction_reference=transaction_reference,
        transaction_note=transaction_note,
        merchant_code=merchant_code,
        merchant_id=merchant_id,
    )
    return upi_link


def generate_upi_payment_link(
    payee_vpa: str,
    payee_name: str,
    amount: Optional[float] = None,
    transaction_reference: str = None,
    transaction_note: str = None,
    merchant_code: str = None,
    transaction_id: str = None,
    minimum_amount: Optional[float] = None,
    currency: str = "INR",
    url: str = None,
    mode: str = "02",  # 02 = QR Code
    orgid: str = "000000",  # 000000 for merchant initiated
    merchant_id: str = None,
    store_id: str = None,
    terminal_id: str = None,
) -> str:
    """
    Generate UPI payment link as per NPCI UPI Linking Specifications 1.6.

    Args:
        payee_vpa: Payee Virtual Payment Address (Mandatory)
        payee_name: Payee name (Mandatory)
        amount: Transaction amount in decimal format (Mandatory for dynamic QR)
        transaction_reference: Transaction reference ID - order number, bill ID, etc. (Mandatory for merchant)
        transaction_note: Short description of transaction
        merchant_code: Payee merchant code (MCC)
        transaction_id: PSP generated transaction ID
        minimum_amount: Minimum amount to be paid if different from transaction amount
        currency: Currency code (default: INR)
        url: URL for bill/invoice details
        mode: Transaction mode (00=Default, 01=QR, 02=Secure QR, 04=Intent, 05=Secure Intent, etc.)
        orgid: Organization ID (000000 for merchant initiated, PSP orgid for PSP app initiated)
        merchant_id: Merchant ID (max 20 characters)
        store_id: Store ID (max 20 characters)
        terminal_id: Terminal ID (max 20 characters)

    Returns:
        UPI payment link string
    """
    # Build the UPI link
    params = []

    # Mandatory parameters
    params.append(f"pa={payee_vpa}")
    params.append(f"pn={quote(payee_name)}")

    # Optional parameters
    if merchant_code:
        params.append(f"mc={merchant_code}")

    if transaction_id:
        params.append(f"tid={transaction_id}")

    if transaction_reference:
        params.append(f"tr={transaction_reference}")

    if transaction_note:
        params.append(f"tn={quote(transaction_note)}")

    # Amount - Mandatory for dynamic QR
    if amount is not None:
        params.append(f"am={amount:.2f}")

    if minimum_amount is not None:
        params.append(f"mam={minimum_amount:.2f}")
    else:
        params.append("mam=null")

    if currency:
        params.append(f"cu={currency}")

    if url:
        params.append(f"url={url}")

    # Mode and orgid are mandatory
    params.append(f"mode={mode}")
    params.append(f"orgid={orgid}")

    # Merchant identifiers
    if merchant_id:
        params.append(f"mid={merchant_id}")

    if store_id:
        params.append(f"msid={store_id}")

    if terminal_id:
        params.append(f"mtid={terminal_id}")

    # Construct the final UPI link
    upi_link = "upi://pay?" + "&".join(params)

    return upi_link
