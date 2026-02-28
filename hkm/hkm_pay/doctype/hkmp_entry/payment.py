import re
import json

import frappe

from frappe.utils.password import get_decrypted_password


from hkm.hkm_integration.doctype.au_bank_integration.au_payment_api import (
    transfer_payment_via_au_bank,
    check_au_transaction_status,
)

from hkm.hkm_pay.constant import (
    AMOUNT,
    AVAILABLE_BALANCE,
    BANK,
    BANK_TRANSFER_SUPPORT,
    BENEFICIARY_NAME,
    COMPANY,
    DOCTYPE,
    FAILED,
    HKM_ACTIVE_COMPANY,
    HKMP_ENTRY,
    HKMP_TRANSFER_TYPE,
    HKMP_USER,
    MOBILE_NO,
    PIN,
    PROCESSING,
    REMARKS,
    SUCCESS,
    UPI,
    UPID,
    USER,
    UPI_ERROR_CODE
)
from hkm.hkm_integration.doctype.indusind_bank_integration.indusind_bank_integration import (
    transfer_payment_via_indusind_bank,
)


def is_null_or_blank(value):
    """
    Check if a string is either None, empty, or consists only of whitespace characters.

    Args:
        value (str): The string to check.

    Returns:
        bool: True if the string is None, empty, or blank; otherwise, False.
    """
    return value is None or (isinstance(value, str) and value.strip() == "")


# def get_payment_user(user):
#     """Get payment user from database."""
#     return frappe.db.get_value(HKMP_USER, {USER: user}, USER)


def process_bank_account(data, payment_entry):
    """Process bank account - create new or validate existing."""
    bank_account = frappe.db.get_value(
        "HKMP Bank Account",
        {
            "account_number": data.get("account_number"),
            "ifsc_code": data.get("ifsc_code"),
        },
        "name",
    )

    if not bank_account:

        # Create new bank account
        new_bank_account = frappe.get_doc(
            {
                "doctype": "HKMP Bank Account",
                "beneficiary_name": data.get("beneficiary_name"),
                "account_number": data.get("account_number"),
                "ifsc_code": data.get("ifsc_code"),
            }
        )
        new_bank_account.insert(ignore_permissions=True)

        payment_entry.bank_account = new_bank_account.name
        payment_entry.account_number = new_bank_account.account_number
        payment_entry.ifsc_code = new_bank_account.ifsc_code
    else:
        payment_entry.bank_account = bank_account
        payment_entry.account_number = data.get("account_number")
        payment_entry.ifsc_code = data.get("ifsc_code")


def update_user_balance(payment_user=None):

    if not payment_user:
        payment_user = "nmcd@hkmjaipur.org"
    """Deduct amount from user's available balance."""
    # frappe.log_error(message=f"update_user_balance called for user {payment_user}", title="HKMP Payment")
    # Optimize: Get advance_limit and calculate in one query instead of loading full doc
    user_data = frappe.db.get_value(
        HKMP_USER, payment_user, ["advance_limit", "name"], as_dict=True
    )

    if not user_data:
        frappe.log_error(message="User data not found", title="HKMP Payment")
        return

    # Optimize: Use single query with COALESCE to handle NULL
    pending_bills = frappe.db.sql(
        """
        SELECT COALESCE(SUM(amount), 0) as total
        FROM `tabHKMP Entry`    
        WHERE user = %s AND 
        status = 'Success' AND
        is_return = 0 AND
        bill_received = 0 AND
        docstatus = 1
        """,
        (payment_user,),
        as_dict=True,
    )

    pending_amount = pending_bills[0].total if pending_bills else 0
    available_amt = max(0, (user_data.advance_limit or 0) - pending_amount)

    # frappe.log_error(message=f"Available amount updated to {available_amt}", title="HKMP Payment")
    # frappe.log_error(message=f"pending amount {pending_amount}", title="HKMP Payment")

    # Optimize: Direct update without loading full document
    frappe.db.set_value(HKMP_USER, user_data.name, "available_amt", available_amt)

    frappe.db.commit()  # v16: REVIEW - check if needed

    from hkm.hkm_pay.tasks import update_bill_restriction_status
    update_bill_restriction_status(payment_user)


def validate_transfer_type_requirements(data, payment_entry=None):
    """Validate transfer type specific requirements."""
    # if not data.get(BENEFICIARY_NAME):
    #     frappe.throw("Beneficiary name is required")

    if data.get(HKMP_TRANSFER_TYPE) == UPI:
        validate_upi_requirements(data)
    else:
        validate_bank_requirements(data, payment_entry)


def validate_bank_requirements(data, payment_entry=None):
    """Validate bank specific requirements."""
    # Validate required fields in data
    if not data.get("account_number") or not data.get("ifsc_code"):
        frappe.throw("Account number and IFSC code are required for bank transfer")

    # Validate that bank account was properly set on payment_entry after processing
    if payment_entry and not payment_entry.bank_account:
        frappe.throw("Bank account not found or could not be created")


def validate_upi_requirements(data):
    """Validate UPI specific requirements."""
    # Validate mobile number if provided
    if data.get(MOBILE_NO):
        mobile = re.sub(r"\D", "", data.get(MOBILE_NO))[-10:]
        if len(mobile) != 10 or not mobile:
            frappe.throw("Invalid mobile number")

    # Validate UPI ID
    upi_id = data.get(UPID)
    if not upi_id:
        frappe.throw("UPI ID is required for UPI transfer")

def validate_transfer_type_support(doctype: str, transfer_type: str):
    """Validate whether a bank integration supports a transfer type."""

    bank_config = BANK_TRANSFER_SUPPORT.get(doctype)

    if not bank_config:
        frappe.throw(f"Unsupported bank integration: {doctype}")

    if not bank_config.get(transfer_type):
        frappe.throw(f"{doctype} does not support {transfer_type} transfer")



    


def validate_pin_for_transfer(pin):
    """Validate PIN for transfer."""
    if not pin:
        frappe.throw("PIN is required for transfer")

    if len(pin) != 4:
        frappe.throw("Invalid PIN")

    user_name = frappe.db.get_value(HKMP_USER, {USER: frappe.session.user}, "name")
    if not user_name:
        frappe.throw("User not found")
    if get_decrypted_password(HKMP_USER, user_name, "secret_pin") != pin:
        return frappe.throw("Invalid PIN")


def get_au_companies():
    au_companies = frappe.cache().hget("hkm_box", "au_active_companies") or []
    if not au_companies:
        au_companies = [
            c.strip() if c else ""
            for c in frappe.get_all(
                HKM_ACTIVE_COMPANY,
                filters={"parenttype": "AU Bank Integration"},
                fields=["company"],
                pluck="company",
            )
        ]
        frappe.cache().hset("hkm_box", "au_active_companies", au_companies)
    return au_companies


def get_indusind_companies():
    indusind_companies = (
        frappe.cache().hget("hkm_box", "indusind_active_companies") or []
    )
    if not indusind_companies:
        indusind_companies = [
            c.strip() if c else ""
            for c in frappe.get_all(
                HKM_ACTIVE_COMPANY,
                filters={"parenttype": "IndusInd Bank Integration"},
                fields=["company"],
                pluck="company",
            )
        ]
        frappe.cache().hset("hkm_box", "indusind_active_companies", indusind_companies)
    return indusind_companies


def process_hkmp_payment(data, user):

    user = frappe.session.user

    if user == "test@hkmjaipur.org":
        return frappe.throw("Test user")

    """
    Process HKMP payment with validation and bank transfer.

    Args:
        data (dict): Payment data containing transfer details
        user (str): User initiating the payment

    Returns:
        str: Payment status (SUCCESS or other status)
    """
    # Get payment user
    payment_user = user

    # Get HKMP Setting document
    setting_doc = frappe.get_cached_doc("HKMP Setting")
    if not setting_doc:
        frappe.throw("HKMP Setting document not found")

    # Get primary bank
    primary_bank = setting_doc.primary_bank
    if not primary_bank:
        frappe.throw("Primary bank not found")

    # Extract payment data

    validate_pin_for_transfer(data.get(PIN))
    transfer_type = data.get(HKMP_TRANSFER_TYPE)
    remarks = data.get(REMARKS)
    amount = data.get(AMOUNT)
    beneficiary_name = data.get(BENEFICIARY_NAME)
    mobile_number = data.get(MOBILE_NO)
    company = data.get(COMPANY)

    transaction_id = data.get("transaction_id")

    # Create HKMP Entry document
    payment_entry = frappe.get_doc(
        {
            DOCTYPE: HKMP_ENTRY,
            HKMP_TRANSFER_TYPE: transfer_type,
            COMPANY: company,
            USER: payment_user,
            REMARKS: remarks or "transfer",
            AMOUNT: amount,
            BENEFICIARY_NAME: beneficiary_name,
        }
    )

    if transfer_type == UPI:
        payment_entry.upi_id = data.get(UPID)
    else:
        process_bank_account(data, payment_entry)

    validate_transfer_type_requirements(data, payment_entry)

    # Don't set transaction_tracking_id here for IndusInd - will be handled in integration function
    # For AU Bank, transaction_id validation happens in AU integration function

    payment_entry.insert(ignore_permissions=True)

    # Get AU Bank Integration companies
    au_companies = get_au_companies()

    # Get IndusInd Bank Integration companies
    indusind_companies = get_indusind_companies()

    BANKS = {
        "AU Bank Integration": {
            "companies": au_companies,
            "handler": transfer_payment_via_au_bank_integration,
            "allow_transaction_id": True,
        },
        "IndusInd Bank Integration": {
            "companies": indusind_companies,
            "handler": transfer_payment_via_indusind_bank_integration,
            "allow_transaction_id": True,
        },
    }

    def execute_bank(bank_name):
        bank = BANKS[bank_name]
        if company not in bank["companies"]:
            return None

        if not bank["allow_transaction_id"] and transaction_id:
            frappe.throw("Dynamic Qr Code is not allowed for RKM AND TSF")

        if bank_name == "AU Bank Integration":
            return bank["handler"](
                payment_entry, transfer_type, payment_user, company, transaction_id
            )

        return bank["handler"](
            payment_entry, transfer_type, payment_user, transaction_id, company
        )


    result = execute_bank(primary_bank)
    if result:
        result_status, response_message = result
        return result_status, response_message

    for bank_name in BANKS:
        if bank_name != primary_bank:
            result = execute_bank(bank_name)
            if result:
                result_status, response_message = result
                return result_status, response_message

    # No bank matched
    frappe.log_error(
        title="Bank integration not found for company",
        message=(
            f"Company: {company}, "
            f"Primary Bank: {primary_bank}, "
            f"AU Companies: {au_companies}, "
            f"IndusInd Companies: {indusind_companies}"
        ),
    )
    return frappe.throw("No bank integration available for this company")


def transfer_payment_via_au_bank_integration(
    payment_entry, transfer_type, payment_user, company=None, user_transaction_id=None
):
    """
    Process AU Bank payment integration with validation and status checking.
    Follows the same pattern as IndusInd Bank integration.

    Args:
        payment_entry: HKMP Entry document
        transfer_type: Type of transfer (UPI, IMPS, etc.)
        payment_user: User making the payment
        company: Company name for AU Bank integration
        user_transaction_id: Optional user-provided transaction ID (for reference only)
    """

    response_message = None

    validate_transfer_type_support("AU Bank Integration", transfer_type)

    if not company:
        frappe.throw("Company is required for AU Bank transfer")

    import uuid
    import time

    # AU Bank requires a specific transaction ID format
    # Generate exactly 32 alphanumeric characters (digits + uppercase + lowercase)
    timestamp = str(int(time.time()))  # 10 digits
    unique_id = str(uuid.uuid4()).replace("-", "").upper()  # 32 hex chars (0-9, A-F)

    # Combine timestamp + unique_id and take first 32 characters
    # timestamp (10) + unique_id (32) = 42 total, we need 32
    combined = timestamp + unique_id
    alphanumeric_chars = combined[:32]  # Take first 32 characters

    # AU Bank transaction ID - this is required for API calls
    au_transaction_id = "AUS" + alphanumeric_chars
    payment_entry.transaction_tracking_id = au_transaction_id

    # Store user-provided transaction ID in remarks if provided (for reference)
    if user_transaction_id and user_transaction_id.strip():
        if payment_entry.remarks:
            payment_entry.remarks = (
                f"{payment_entry.remarks} | User Ref: {user_transaction_id.strip()}"
            )
        else:
            payment_entry.remarks = f"User Ref: {user_transaction_id.strip()}"

    # 1. Call transfer API to initiate payment
    response = transfer_payment_via_au_bank(payment_entry, company)

    # 2. Check if transfer API call succeeded (HTTP call succeeded, not payment success)
    # The actual payment status will be checked via transaction status API
    if not response or response.get("error"):
        # API call failed - mark entry and return
        error_msg = response.get("error") if response else "No response"
        frappe.log_error(
            title="Payment Transfer API Failed",
            message=f"Transfer API call failed for {payment_entry.name}: {error_msg}",
        )
        payment_entry.status = FAILED
        payment_entry.api_response = (
            json.dumps(response.get("api_response"))
            if response and response.get("api_response")
            else None
        )
        payment_entry.api_payload = (
            json.dumps(response.get("api_payload"))
            if response and response.get("api_payload")
            else None
        )
        payment_entry.save(ignore_permissions=True)
        payment_entry.flags.ignore_permissions = True
        payment_entry.submit()
        return FAILED , response_message 

    # 3. Check the initial API response for payment status (transaction status check not required)
    # The API response already contains the payment status
    # Optimize: api_response is already a dict from transfer_payment_via_au_bank, no need to parse
    api_response = response.get("api_response") or {}

    # 4. Store responses (only serialize once)
    payment_entry.api_response = json.dumps(api_response) if api_response else None
    payment_entry.api_payload = (
        json.dumps(response.get("api_payload")) if response.get("api_payload") else None
    )

    # 5. Determine payment status directly from API response based on response code
    # Response codes: "00" = Success, "11" = Pending, "99" = Failed
    payment_status = PROCESSING  # Default status

    if api_response:
        # Check vpaResponseStatus for response code (primary indicator)
        vpa_status = api_response.get("data", {}).get("vpaResponseStatus", {})
        response_code = vpa_status.get("responseCode")

        # Check transactionInfo.result.code (secondary indicator, only used if response_code is missing)
        transaction_info = api_response.get("data", {}).get("transactionInfo", {})
        result_code = transaction_info.get("result", {}).get("code")

        # Determine status based on response code
        # Priority: vpaResponseStatus.responseCode > transactionInfo.result.code
        # Only use result_code if response_code is None or empty
        if response_code:
            status_code = response_code
        elif result_code:
            status_code = result_code
        else:
            status_code = None

        if status_code == "00":
            # Success
            payment_status = SUCCESS
        elif status_code == "11":
            # Pending
            payment_status = PROCESSING
        elif status_code == "99":
            # Failed
            payment_status = FAILED
        else:
            # No clear status code - check overall response status as fallback
            response_status = api_response.get("status", "").lower()
            successful_response = api_response.get("successfulResponse", False)
            error = api_response.get("error")

            if response_status == "success" and successful_response and not error:
                # If responseCode is "11" (pending) but status_code wasn't set properly, check vpa_status message
                if (
                    vpa_status.get("message", "").upper() == "PENDING"
                    or response_code == "11"
                ):
                    payment_status = PROCESSING
                else:
                    # API says success but no clear code - treat as success
                    payment_status = SUCCESS
            elif error or (vpa_status.get("message", "").lower().find("failed") != -1):
                # Error present - treat as failed
                payment_status = FAILED
            else:
                # Unknown status - keep as processing
                payment_status = PROCESSING

    # 6. Set payment status based on determined status
    payment_entry.status = payment_status

    # Update user balance only on confirmed success
    # if payment_entry.status == SUCCESS:
    #     update_user_balance(payment_user)

    # 7. Store additional transaction details from API response
    payment_entry.debited_from = "AU Bank Integration"

    # Extract transaction details from API response
    transaction_info = api_response.get("data", {}).get("transactionInfo", {})
    attributes = transaction_info.get("attributes", {})

    # Get external reference number
    external_ref = api_response.get("data", {}).get("externalReferenceNumber")
    if external_ref:
        payment_entry.customer_ref_no = external_ref
        payment_entry.utr = external_ref

    # Optimize: Set flag before save, combine operations
    payment_entry.flags.ignore_permissions = True
    payment_entry.save(ignore_permissions=True)
    payment_entry.submit()

    # Commit once at the end
    frappe.db.commit()  # v16: REVIEW - check if needed

    # Example API Response:
    # {"status": "success", "data": {"vpaResponseStatus": {"responseCode": "99", "message": "FAILURE"}, "externalReferenceNumber": "601152403757", "upiId": null, "upiBankName": null, "neftEnabled": false, "rtgsEnabled": false, "upiFlow": null, "limitRestoredMessage": null, "transactionInfo": {"transactionid": "AUS1768141989C7CC118AF6C84366AB614A", "transactiondatetime": "2026-01-11 08:03:10 PM", "result": {"code": "99", "message": "FAILURE", "isactive": "false", "codedescription": "ZH | INVALID VPA"}, "attributes": {}}, "ChkValue": "Bvln6lzXjAJVhwkXAtLRhwjczB9lOhPWq6wB7+3UF1Q=", "txnStatus": null}, "error": null, "successfulResponse": false}

    if payment_entry.status == FAILED:
        response_message = api_response.get("data", {}).get("vpaResponseStatus", {}).get("codedescription")
    return payment_entry.status , response_message


def transfer_payment_via_indusind_bank_integration(
    payment_entry,
    transfer_type,
    payment_user,
    user_transaction_id=None,
    company=None,
):
    """
    Process IndusInd Bank payment integration with validation and status checking.

    Args:
        payment_entry: HKMP Entry document
        transfer_type: Type of transfer (UPI, IMPS, etc.)
        payment_user: User making the payment
        user_transaction_id: Optional user-provided transaction ID (used as order number if provided)
        company: Company name (optional for IndusInd)
    """

    response_message = None
    validate_transfer_type_support("IndusInd Bank Integration", transfer_type)

    # Determine the orderNo to use for IndusInd Bank transaction
    # Logic:
    # 1. If user provides transaction_id AND it doesn't exist in database → use it
    # 2. If not provided OR already exists → use Frappe document name
    indusind_order_no = payment_entry.name  # Default to document name

    if user_transaction_id and user_transaction_id.strip():
        user_txn_id = user_transaction_id.strip()

        # Check if this transaction_id already exists in database
        existing_entry = frappe.db.get_value(
            "HKMP Entry",
            {
                "transaction_tracking_id": user_txn_id,
                "company": company,
                "debited_from": "IndusInd Bank Integration",
            },
            "name",
        )

        if not existing_entry:
            # Transaction ID is unique - use it
            indusind_order_no = user_txn_id
        else:
            # Transaction ID already exists - use document name instead
            frappe.log_error(
                title="Duplicate Transaction Tracking ID",
                message=f"Transaction ID '{user_txn_id}' already exists in entry '{existing_entry}'. Using document name '{payment_entry.name}' instead.",
            )

    # Set transaction_tracking_id BEFORE calling API so IndusInd integration can use it
    payment_entry.transaction_tracking_id = indusind_order_no

    # 1. Call transfer API to initiate payment
    response = transfer_payment_via_indusind_bank(payment_entry)

    # 2. Check if transfer API call succeeded (HTTP call succeeded, not payment success)
    if not response or response.get("error"):
        # API call failed - mark entry and return
        error_msg = response.get("error") if response else "No response"
        frappe.log_error(
            title="Payment Transfer API Failed",
            message=f"Transfer API call failed for {payment_entry.name}: {error_msg}",
        )
        payment_entry.status = FAILED
        payment_entry.api_response = (
            json.dumps(response.get("api_response"))
            if response and response.get("api_response")
            else None
        )
        payment_entry.api_payload = (
            json.dumps(response.get("api_payload"))
            if response and response.get("api_payload")
            else None
        )
        payment_entry.save(ignore_permissions=True)
        payment_entry.flags.ignore_permissions = True
        payment_entry.submit()
        return FAILED , response_message

    # 3. Extract actual order number from API payload if available
    if response.get("api_payload"):
        actual_order_no = response.get("api_payload", {}).get("orderNo")
        if actual_order_no:
            payment_entry.transaction_tracking_id = actual_order_no

    # 4. Extract transaction status from decrypted response
    # IndusInd returns: response -> decrypted_response (this IS the transaction data directly)
    # Response structure: {status, statusDesc, txnId, custRefNo, orderNo, errorCode, Date, txnAmount, approvalNum, etc}
    api_response_data = response.get("decrypted_response", {})

    # 5. Store responses (only serialize once)
    payment_entry.api_response = (
        json.dumps(api_response_data) if api_response_data else None
    )
    payment_entry.api_payload = (
        json.dumps(response.get("api_payload")) if response.get("api_payload") else None
    )

    # 6. Determine payment status from API response
    # Status codes: "S" = Success, "F" = Failed, others = Processing
    status_code = api_response_data.get("status")

    if status_code == "S":
        payment_entry.status = SUCCESS
    elif status_code == "F":
        payment_entry.status = FAILED
    else:
        payment_entry.status = PROCESSING

    # 7. Update user balance only on confirmed success
    # if payment_entry.status == SUCCESS:
    #     update_user_balance(payment_user)

    # 8. Store transaction details from API response
    payment_entry.debited_from = "IndusInd Bank Integration"
    # txnId is the NPCI transaction ID (UPI UTR)
    payment_entry.utr = api_response_data.get("txnId")
    payment_entry.customer_ref_no = api_response_data.get("custRefNo")

    # 9. Save and submit payment entry
    payment_entry.flags.ignore_permissions = True
    payment_entry.save(ignore_permissions=True)
    payment_entry.submit()

    # 10. Commit once at the end
    frappe.db.commit()  # v16: REVIEW - check if needed

    # Example API Response:
    # {"status": "F", "statusDesc": "Payment Failed", "txnId": "INDa70b21e1921d4b0ca1d9b8c1739b9f53", "custRefNo": "100017066854", "orderNo": "028bpodk8t", "errorCode": "U29", "Date": "2026-01-11 05:13:16", "txnAmount": " 704.00", "approvalNum": "445948", "pyFvaddr": "amazon@yapl", "prfvaddr": "harekrishnajaipur@indus", "respCode": "00"}

    if payment_entry.status == FAILED and api_response_data.get("errorCode"):
        response_message = UPI_ERROR_CODE.get(api_response_data.get("errorCode"))


    return payment_entry.status , response_message


@frappe.whitelist()
def get_companies():
    doc = frappe.get_all(
        "HKM Active Company",
        fields=["company"],
    )
    return doc
