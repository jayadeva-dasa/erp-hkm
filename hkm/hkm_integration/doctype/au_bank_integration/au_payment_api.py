import requests
import json
import base64
from hkm.hkm_pay.constant import HKMP_ENTRY
import frappe
from Crypto.Cipher import AES
from frappe.utils.password import get_decrypted_password
from frappe.model.document import Document
from typing import Dict, Any

# payload sample = {'type': 'INET', 'amount': '1.00', 'payeeName': 'Sri Radha Krishna Mandir Foundation', 'payeeVpa': 'arorapriyanshu33-1@oksbi', 'payeeMcc': '5511', 'payerName': 'Sri Radha Krishna Mandir Foundation', 'payerVpa': 'srkmjaipur@aubank', 'remarks': 'HKM Production', 'transactionType': 'Pay', 'initiationMode': '01', 'clTransactionId': 'AUS1765446489TS71fb3b33dd734ca58387', 'transactionMode': 'VPA', 'payerAccount': '1781220613042120'}

# payment_reponse_sample = {"status":"success","data":{"vpaResponseStatus":{"responseCode":"00","message":"Success"},"externalReferenceNumber":"534540165523","upiId":null,"upiBankName":null,"neftEnabled":false,"rtgsEnabled":false,"upiFlow":null,"limitRestoredMessage":null,"transactionInfo":{"transactionid":"AUS1765446489TS71fb3b33dd734ca58387","transactiondatetime":"2025-12-11 03:18:10 PM","result":{"code":"00","message":"SUCCESS","isactive":"true"},"attributes":{"transactiontype":"Pay","initiationmode":"01","payervpa":"srkmjaipur@aubank","payeraccount":"1781220613042120","payeename":"Sri Radha Krishna Mandir Foundation","payeevpa":"arorapriyanshu33-1@oksbi","payeemcc":"5511","amount":"1.00","remarks":"HKM Production","transdatetime":"2025-12-11 03:18:10 PM"}},"ChkValue":"uRwcK2qP77cwJwKRSpqTwpc8RKNpwAIa9nV9d0nWhnU=","txnStatus":null},"error":null,"successfulResponse":true}


# Transaction status response sample ={"status_code": 200, "success": true, "error": null, "data": {"status": "success", "data": {"vpaResponseStatus": {"responseCode": "00", "message": "Success"}, "externalReferenceNumber": null, "upiId": null, "upiBankName": null, "neftEnabled": false, "rtgsEnabled": false, "upiFlow": null, "limitRestoredMessage": null, "transactionInfo": {"transactionid": "AUS20251211TS5741TEB101487D40E247CF", "transactiondatetime": "2025-12-11 03:22:01 PM", "result": {"code": "00", "message": "SUCCESS", "isactive": "true", "codedescription": ""}, "attributes": {"transactionid": "AUS1765446489TS71fb3b33dd734ca58387", "transactiontype": "PAY", "initiationmode": "", "payername": "", "payervpa": "", "payervpaid": "srkmjaipur@aubank", "payeraccountid": "", "payeraccount": "", "payerifsc": "AUBL0000001", "payermcc": "", "payeename": "", "payeevpaid": "", "payeeaccountid": "", "payeevpa": "", "payeeaccount": "", "payeeifsc": "", "payeemmid": "", "payeemobilenumber": "2109694141", "payeemcc": "", "amount": "1.00", "remarks": "HKM Production", "payrefurl": "www.aubank.co.in", "code": "00", "direction": "outward", "status": "SUCCESS", "custrefnumber": "534540165523", "RefId": "Ref534540165523"}}, "ChkValue": "sn4nE3FNP8kBF5vV6IHyiVb2u4/6F+sctOrSsUqsyBo=", "txnStatus": null}, "error": null, "successfulResponse": true}}


def refresh_oauth_token():
    setting = frappe.get_cached_doc("AU Bank Integration")
    for i in setting.npci_integration:
        i.access_token = get_oauth_token(
            get_decrypted_password("AU Bank Integration Detail", i.name, "client_id"),
            get_decrypted_password(
                "AU Bank Integration Detail", i.name, "client_secret"
            ),
            i.auth_url,
        )
        if not i.access_token:
            frappe.log_error(
                title="OAuth token generation failed",
                message=f"OAuth token generation failed:",
            )
            i.access_token = None
            continue
    setting.save(ignore_permissions=True)
    frappe.db.commit()  # v16: REVIEW - check if needed


def encrypt_gcm(message, key, salt_key):
    """
    AES GCM encryption exactly matching Java implementation
    Java uses US_ASCII for keys and UTF_8 for message
    """
    try:
        # Java uses getBytes(StandardCharsets.US_ASCII) for keys
        # So keys are treated as ASCII strings, not base64 decoded
        key_bytes = key.encode("ascii")
        iv_bytes = salt_key.encode("ascii")

        # Convert message to UTF-8 bytes (as per Java code)
        plain_bytes = message.encode("utf-8")

        # Create AES GCM cipher with 128-bit tag (as per Java GCMParameterSpec)
        cipher = AES.new(key_bytes, AES.MODE_GCM, nonce=iv_bytes)

        # Encrypt and get auth tag
        encrypted_bytes, auth_tag = cipher.encrypt_and_digest(plain_bytes)

        # Java doFinal() includes the auth tag in GCM mode
        encrypted_with_tag = encrypted_bytes + auth_tag

        # Encode to base64 (as per Java Base64.getEncoder().encodeToString())
        encrypted_b64 = base64.b64encode(encrypted_with_tag).decode("utf-8")

        return encrypted_b64

    except Exception as e:
        print("Encryption error: {}".format(str(e)))
        return ""


def decrypt_gcm(encrypted_message, key, salt_key):
    """
    AES GCM decryption exactly matching Java implementation
    """
    try:
        # Java uses getBytes(StandardCharsets.US_ASCII) for keys
        key_bytes = key.encode("ascii")
        iv_bytes = salt_key.encode("ascii")

        # Decode the encrypted message from base64
        encrypted_data = base64.b64decode(encrypted_message)

        # Split encrypted data and auth tag (last 16 bytes are auth tag)
        encrypted_bytes = encrypted_data[:-16]
        auth_tag = encrypted_data[-16:]

        # Create AES GCM cipher
        cipher = AES.new(key_bytes, AES.MODE_GCM, nonce=iv_bytes)

        # Decrypt and verify auth tag
        plain_bytes = cipher.decrypt_and_verify(encrypted_bytes, auth_tag)

        # Convert back to string and trim (as per Java code)
        original_text = plain_bytes.decode("utf-8").strip()

        return original_text

    except Exception as e:
        print("Decryption error: {}".format(str(e)))
        return ""


def get_oauth_token(client_id, client_secret, auth_url):
    """
    Generate OAuth 2.0 access token using client credentials
    Returns: access_token string or None if failed
    """
    try:
        auth = (client_id, client_secret)
        headers = {"Content-Type": "application/json"}

        response = requests.post(auth_url, auth=auth, headers=headers)

        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            return access_token
        else:
            frappe.log_error(
                title="OAuth token generation failed",
                message=f"OAuth token generation failed: response: {response.json()}",
            )
            return None

    except Exception as e:
        frappe.log_error(
            title="OAuth token generation exception",
            message=f"OAuth token generation exception: {str(e)}",
        )
        return None


def get_au_bank_settings(company: str) -> Dict[str, Any]:
    """Get AU Bank settings for a company with secure caching.

    Security: Only non-sensitive fields are cached. Sensitive credentials
    (passwords, tokens, keys) are always fetched from encrypted storage.
    """
    # Use cache key based on company for non-sensitive data only
    cache_key = f"au_bank_settings_{company}"

    # Try to get non-sensitive cached data first
    cached_non_sensitive = frappe.cache().get_value(cache_key)

    # Always fetch document and sensitive fields from database (never cache)
    settings_doc = frappe.get_doc("AU Bank Integration Detail", {"company": company})

    # Get access_token, handle case where it doesn't exist
    try:
        access_token = settings_doc.get_password("access_token")
    except Exception:
        access_token = None

    if not access_token:
        # Get client credentials safely (always from database, never cached)
        try:
            client_id = get_decrypted_password(
                "AU Bank Integration Detail",
                settings_doc.name,
                "client_id",
                raise_exception=False,
            )
            client_secret = get_decrypted_password(
                "AU Bank Integration Detail",
                settings_doc.name,
                "client_secret",
                raise_exception=False,
            )
        except Exception:
            frappe.log_error(
                title="Failed to get client credentials",
                message=f"Failed to get client credentials for company: {company}, document: {settings_doc.name}",
            )
            client_id = None
            client_secret = None

        if client_id and client_secret:
            access_token = get_oauth_token(
                client_id,
                client_secret,
                settings_doc.auth_url,
            )
            if access_token:
                settings_doc.set("access_token", access_token)
                settings_doc.save(ignore_permissions=True)
                frappe.db.commit()  # v16: REVIEW - check if needed
                # Invalidate cache when access_token is updated
                frappe.cache().delete_value(cache_key)
        else:
            frappe.log_error(
                title="Missing client credentials",
                message=f"Client ID or Client Secret not found for company: {company}, document: {settings_doc.name}",
            )

    # Get sensitive password fields safely (always from database, never cached)
    def get_password_safe(fieldname):
        try:
            return settings_doc.get_password(fieldname)
        except Exception:
            try:
                return get_decrypted_password(
                    "AU Bank Integration Detail",
                    settings_doc.name,
                    fieldname,
                    raise_exception=False,
                )
            except Exception:
                return None

    # If we have cached non-sensitive data, use it; otherwise build it
    if cached_non_sensitive is not None:
        # Use cached non-sensitive data
        oauth_url = cached_non_sensitive.get("oauth_url")
        verify_vpa_url = cached_non_sensitive.get("verify_vpa_url")
        upi_payout_url = cached_non_sensitive.get("upi_payout_url")
        transaction_status_url = cached_non_sensitive.get("transaction_status_url")
        account_number = cached_non_sensitive.get("account_number")
        merchant_name = cached_non_sensitive.get("merchant_name")
        merchant_vpa = cached_non_sensitive.get("merchant_vpa")
    else:
        # Cache miss - fetch non-sensitive fields from document
        oauth_url = settings_doc.auth_url
        verify_vpa_url = settings_doc.verify_vpa_url
        upi_payout_url = settings_doc.upi_payout_url
        transaction_status_url = settings_doc.transaction_status_url
        account_number = settings_doc.account_number
        merchant_name = settings_doc.merchant__name
        merchant_vpa = settings_doc.vpa

        # Cache only non-sensitive fields for 5 minutes (300 seconds)
        non_sensitive_cache = {
            "oauth_url": oauth_url,
            "verify_vpa_url": verify_vpa_url,
            "upi_payout_url": upi_payout_url,
            "transaction_status_url": transaction_status_url,
            "account_number": account_number,
            "merchant_name": merchant_name,
            "merchant_vpa": merchant_vpa,
        }
        frappe.cache().set_value(cache_key, non_sensitive_cache, expires_in_sec=300)

    # Always fetch sensitive fields from database (never from cache)
    settings_result = {
        "settings_doc": settings_doc,
        "oauth_url": oauth_url,
        "verify_vpa_url": verify_vpa_url,
        "upi_payout_url": upi_payout_url,
        "transaction_status_url": transaction_status_url,
        "account_number": account_number,
        "merchant_name": merchant_name,
        "merchant_vpa": merchant_vpa,
        # Sensitive fields - always fetched from encrypted storage, never cached
        "client_id": get_password_safe("client_id"),
        "client_secret": get_password_safe("client_secret"),
        "encryption_key": get_password_safe("secret_key"),
        "salt_key": get_password_safe("iv"),
        "access_token": access_token,
    }

    return settings_result


def clear_au_bank_settings_cache(company: str = None):
    """Clear cache for AU Bank settings.

    Args:
        company: Company name. If None, clears cache for all companies.
    """
    if company:
        cache_key = f"au_bank_settings_{company}"
        frappe.cache().delete_value(cache_key)
    else:
        # Clear all AU Bank settings cache
        frappe.cache().delete_keys("au_bank_settings_*")


def transfer_payment_via_au_bank(
    entry_doc: Document, company: str = None
) -> Dict[str, Any]:
    """
    Transfer payment via AU Bank - supports UPI transfer.

    Args:
        entry_doc: HKMP Entry document
        company: Company name (required for AU Bank)

    Returns:
        Dict with success status, api_payload, api_response, and error if any
    """
    if not company:
        frappe.throw("Company is required for AU Bank transfer")

    from hkm.hkm_pay.constant import UPI

    if entry_doc.transfer_type != UPI:
        frappe.throw("AU Bank currently supports only UPI transfers")

    # Get settings
    settings = get_au_bank_settings(company)
    if not settings.get("access_token"):
        return {
            "success": False,
            "error": "Failed to get OAuth access token",
            "api_payload": None,
            "api_response": None,
        }

    # Prepare payload
    payload = {
        "type": "INET",
        "amount": str(entry_doc.amount),
        "payeeName": entry_doc.beneficiary_name,
        "payeeVpa": entry_doc.upi_id,
        "payeeMcc": "5511",
        "payerName": settings["merchant_name"],
        "payerVpa": settings["merchant_vpa"],
        "remarks": entry_doc.remarks or "HKM Production",
        "transactionType": "Pay",
        "initiationMode": "01",
        "clTransactionId": entry_doc.transaction_tracking_id,
        "transactionMode": "VPA",
        "payerAccount": settings["account_number"],
    }

    result = {
        "success": False,
        "api_payload": payload,
        "api_response": None,
        "transaction_id": entry_doc.transaction_tracking_id,
    }

    try:
        # Encrypt payload
        json_payload = json.dumps(payload)
        encrypted_payload = encrypt_gcm(
            json_payload, settings["encryption_key"], settings["salt_key"]
        )

        if not encrypted_payload:
            result["error"] = "Encryption failed"
            return result

        # Prepare request
        request_body = {"encvalue": encrypted_payload}
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {settings['access_token']}",
            "User-Agent": "HKM-Frappe-Client/1.0",
        }

        # Make API call
        response = requests.post(
            settings["upi_payout_url"], headers=headers, json=request_body, timeout=30
        )

        if response.status_code == 200:
            try:
                if response.text.strip():
                    data = response.json()
                    if "encvalue" in data:
                        # Decrypt response
                        decrypted_response_str = decrypt_gcm(
                            data["encvalue"],
                            settings["encryption_key"],
                            settings["salt_key"],
                        )
                        if decrypted_response_str:
                            try:
                                decrypted_response = json.loads(decrypted_response_str)
                                result["api_response"] = decrypted_response

                                # Check payment status based on response code
                                # Response codes: "00" = Success, "11" = Pending, "99" = Failed
                                
                                # Check vpaResponseStatus for response code (primary indicator)
                                vpa_status = decrypted_response.get("data", {}).get(
                                    "vpaResponseStatus", {}
                                )
                                response_code = vpa_status.get("responseCode", "")

                                # Also check transactionInfo.result.code (secondary indicator)
                                transaction_info = decrypted_response.get(
                                    "data", {}
                                ).get("transactionInfo", {})
                                result_code = transaction_info.get(
                                    "result", {}
                                ).get("code", "")

                                # Determine status based on response code
                                # Priority: vpaResponseStatus.responseCode > transactionInfo.result.code
                                status_code = response_code or result_code

                                if status_code == "00":
                                    # Success
                                    result["success"] = True
                                    result["status"] = "success"
                                elif status_code == "11":
                                    # Pending
                                    result["success"] = False
                                    result["status"] = "pending"
                                    result["error"] = vpa_status.get("message", "Payment pending")
                                elif status_code == "99":
                                    # Failed
                                    result["success"] = False
                                    result["status"] = "failed"
                                    result["error"] = vpa_status.get("message", "Payment failed")
                                else:
                                    # Unknown status - check overall response status as fallback
                                    response_status = decrypted_response.get(
                                        "status", ""
                                    ).lower()
                                    successful_response = decrypted_response.get(
                                        "successfulResponse", False
                                    )
                                    error = decrypted_response.get("error")

                                    if (
                                        response_status == "success"
                                        and successful_response
                                        and not error
                                    ):
                                        # API says success but no clear code - treat as success
                                        result["success"] = True
                                        result["status"] = "success"
                                    elif error or (vpa_status.get("message", "").lower().find("failed") != -1):
                                        # Error present - treat as failed
                                        result["success"] = False
                                        result["status"] = "failed"
                                        result["error"] = error or vpa_status.get(
                                            "message", "Payment failed"
                                        )
                                    else:
                                        # Unknown status - treat as pending
                                        result["success"] = False
                                        result["status"] = "pending"
                                        result["error"] = vpa_status.get(
                                            "message", "Payment status unknown"
                                        ) or transaction_info.get("result", {}).get(
                                            "message", "Payment status unknown"
                                        )

                                # Extract transaction ID from response if available
                                # Structure: data.transactionInfo.transactionid
                                transaction_info = decrypted_response.get(
                                    "data", {}
                                ).get("transactionInfo", {})
                                if transaction_info and transaction_info.get(
                                    "transactionid"
                                ):
                                    result["transaction_id"] = transaction_info.get(
                                        "transactionid"
                                    )

                                # Also extract externalReferenceNumber if available
                                external_ref = decrypted_response.get("data", {}).get(
                                    "externalReferenceNumber"
                                )
                                if external_ref:
                                    result["external_reference_number"] = external_ref

                            except json.JSONDecodeError:
                                result["api_response"] = {"raw": decrypted_response_str}
                                result["success"] = False
                                result["error"] = "Invalid JSON in decrypted response"
                        else:
                            result["error"] = "Decryption failed"
                    else:
                        result["api_response"] = data
                        result["success"] = True
                else:
                    result["error"] = "Empty response from server"
            except json.JSONDecodeError as je:
                result["error"] = f"Invalid JSON response: {str(je)}"
                result["response_text"] = response.text
        else:
            try:
                error_data = response.json()
                result["error"] = (
                    f"HTTP {response.status_code}: {json.dumps(error_data)}"
                )
            except:
                result["error"] = f"HTTP {response.status_code}: {response.text}"

    except Exception as e:
        result["error"] = str(e)
        frappe.log_error(title="AU Bank Payment Error", message=str(e))

    return result


def check_au_transaction_status(
    transaction_id: str,
    company: str,
    vpa: str = None,
    request_type: str = "Pay",
    type_field: str = "INET",
) -> Dict[str, Any]:
    """
    Check transaction status for AU Bank payment.
    Matches the implementation in payment_production.py

    Args:
        transaction_id: Transaction ID (clTransactionId) to check (mandatory, max 35 chars)
        company: Company name
        vpa: VPA ID (mandatory, max 50 chars). If not provided, uses merchant VPA from settings
        request_type: Request type (mandatory, max 20 chars, default: "Pay")
        type_field: Type field (mandatory, max 5 chars, default: "INET")

    Returns:
        Dict with success status, status_code, data, and transaction status details
    """
    if not company:
        return {"success": False, "error": "Company is required", "status_code": 400}

    if not transaction_id:
        return {
            "success": False,
            "error": "Transaction ID is required",
            "status_code": 400,
        }

    # Get settings
    settings = get_au_bank_settings(company)
    if not settings.get("access_token"):
        # Try to get OAuth token
        access_token = get_oauth_token(
            settings["client_id"],
            settings["client_secret"],
            settings["oauth_url"],
        )
        if access_token:
            settings["access_token"] = access_token
        else:
            return {
                "success": False,
                "error": "Failed to get OAuth access token",
                "status_code": 401,
            }

    # Use merchant VPA if vpa not provided
    if not vpa:
        vpa = settings["merchant_vpa"]

    if not vpa:
        return {
            "success": False,
            "error": "VPA is required",
            "status_code": 400,
        }

    result = {
        "success": False,
        "status_code": None,
        "error": None,
        "data": None,
    }

    try:
        # Prepare payload for status check - matching payment_production.py structure
        payload = {
            "vpa": vpa[:50],  # max 50 chars
            "transactionId": transaction_id[:35],  # max 35 chars
            "requestType": request_type[:20],  # max 20 chars
            "type": type_field[:5],  # max 5 chars
        }

        # Encrypt payload
        json_payload = json.dumps(payload)
        encrypted_payload = encrypt_gcm(
            json_payload, settings["encryption_key"], settings["salt_key"]
        )

        if not encrypted_payload:
            result["error"] = "Encryption failed"
            result["status_code"] = 500
            return result

        # Prepare request
        request_body = {"encvalue": encrypted_payload}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings['access_token']}",
        }

        # Make API call
        response = requests.post(
            settings["transaction_status_url"],
            headers=headers,
            json=request_body,
            timeout=30,
        )

        result["status_code"] = response.status_code

        if response.status_code == 200:
            # Decrypt response - matching payment_production.py
            response_data = response.json()
            if "encvalue" in response_data:
                decrypted_response = decrypt_gcm(
                    response_data["encvalue"],
                    settings["encryption_key"],
                    settings["salt_key"],
                )
                result["data"] = (
                    json.loads(decrypted_response)
                    if decrypted_response
                    else response_data
                )
                result["success"] = True

                # Extract transaction status from nested structure
                # Transaction status response sample shows:
                # {"status_code": 200, "success": true, "data": {"status": "success", "data": {"transactionInfo": {...}}}}
                if isinstance(result["data"], dict):
                    inner_data = result["data"].get("data", {})
                    data_status = (
                        result["data"].get("status", "").lower()
                    )  # status is at data.status, not data.data.status
                    transaction_info = inner_data.get(
                        "transactionInfo", {}
                    )  # transactionInfo is at data.data.transactionInfo

                    # Extract vpaResponseStatus first (primary indicator)
                    # It's at data.data.vpaResponseStatus
                    vpa_status = inner_data.get("vpaResponseStatus", {})
                    if vpa_status:
                        result["vpa_response_code"] = vpa_status.get("responseCode", "")
                        result["vpa_message"] = vpa_status.get("message", "")

                    if transaction_info:
                        result["transaction_status"] = transaction_info

                        # Extract status from attributes
                        attributes = transaction_info.get("attributes", {})
                        result["status"] = attributes.get("status", "").upper()

                        # Extract code from attributes or result
                        result["code"] = attributes.get(
                            "code", ""
                        ) or transaction_info.get("result", {}).get("code", "")

                        # Extract reference numbers
                        # externalReferenceNumber is the primary customer reference number
                        result["externalReferenceNumber"] = inner_data.get(
                            "externalReferenceNumber", ""
                        )
                        result["custrefnumber"] = attributes.get("custrefnumber", "")
                        result["ref_id"] = attributes.get("RefId", "")

                        # Check result section
                        result_section = transaction_info.get("result", {})
                        if result_section:
                            result["result_code"] = result_section.get("code", "")
                            result["result_message"] = result_section.get("message", "")
                            result["codedescription"] = result_section.get(
                                "codedescription", ""
                            )
            else:
                result["data"] = response_data
                result["success"] = True

        elif response.status_code == 400:
            result["error"] = "Bad request"
            result["data"] = response.text

        elif response.status_code == 401:
            result["error"] = "Invalid authentication credentials"
            result["data"] = response.text

        elif response.status_code == 404:
            result["error"] = "Not Found"
            result["data"] = response.text

        elif response.status_code == 500:
            result["error"] = "Internal Server Error - Something went wrong"
            result["data"] = response.text

        elif response.status_code == 503:
            result["error"] = "Service Unavailable"
            result["data"] = response.text

        elif response.status_code == 504:
            result["error"] = "Gateway timeout"
            result["data"] = response.text

        else:
            result["error"] = f"Unexpected status code: {response.status_code}"
            result["data"] = response.text

    except requests.exceptions.Timeout:
        return {
            "status_code": 504,
            "error": "Gateway timeout",
            "success": False,
            "data": None,
        }
    except Exception as e:
        result["success"] = False
        result["error"] = f"Exception: {str(e)}"
        result["status_code"] = 500
        frappe.log_error(title="AU Bank Status Check Error", message=str(e))

    return result
