from hkm.hkm_integration.doctype.indusind_bank_integration.indusind_bank_integration import decrypt_response
import frappe
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import base64
import json


@frappe.whitelist(allow_guest=True)
def indusind_bank_callback():
    # payload = json.loads(frappe.request.get_data().decode("utf-8"))

    # merchant_id = payload.get("pgMerchantId")

    # setting_doc = frappe.get_cached_doc("IndusInd Bank Integration")


    # decrypted_response =  decrypt_response(setting_doc.get_password("encryption_key"), payload.get("resp"))

    # # {"apiResp":{"pspRefNo":"ORD202512290001","upiTransRefNo":0,"npciTransId":"SBIf7871ae7ad1a4c44b308f5902e5e6952","custRefNo":"536365359602","amount":"1.00","txnAuthDate":"2025:12:29 11:19:20","responseCode":"00","approvalNumber":"378886","status":"SUCCESS","addInfo":{"addInfo1":"9983132074","addInfo2":"2401259662050612","addInfo3":"Priyanshu","addInfo4":"AUBL0002596"},"payerVPA":"arorapriyanshu33-1@oksbi","payeeVPA":"harekrishnajaipur@indus","orderNo":"ORD202512290001","currentStatusDesc":"Transaction success","txnNote":"Donation Payment","txnType":"PAY","refUrl":"https://www.sbi.co.in","txnDate":"2025:12:29 11:19:20","payerAccType":"SAVINGS"}}

    # if decrypted_response.get("apiResp").get("pspRefNo"):

    #     order_number = decrypted_response.get("apiResp").get("pspRefNo")
    #     callback_doc = frappe.get_doc("HKM API Callback" , {"order_number": order_number})
    #     callback_doc.api_response = json.dumps(decrypted_response)
    #     callback_doc.insert(ignore_permissions=True)
    #     frappe.db.commit()

    payload = frappe.request.get_data().decode("utf-8")




    
    if not payload:
        payload = frappe.form_dict or None
        source = "form_dict" if payload else "empty"
    else:
        source = "request_data"

    if isinstance(payload, str):
        try:
            payload_dict = json.loads(payload)
        except json.JSONDecodeError:
            payload_dict = payload
    else:
        payload_dict = payload

    doc = frappe.new_doc("HKM API Call")
    doc.api_data = make_serializable(
        {
            "source": source,
            "raw_payload": payload_dict,
        }
    )
    doc.insert(ignore_permissions=True)
    frappe.db.commit()  # v16: REVIEW - check if needed

    return {"status": "success", "message": "Payload received successfully"}


# @frappe.whitelist(allow_guest=True)
# def icici_bank_callback():

#     payload = frappe.request.get_data().decode("utf-8")
    
#     if not payload:
#         payload = frappe.form_dict or None
#         source = "form_dict" if payload else "empty"
#     else:
#         source = "request_data"

#     if isinstance(payload, str):
#         try:
#             payload_dict = json.loads(payload)
#         except json.JSONDecodeError:
#             payload_dict = payload
#     else:
#         payload_dict = payload

#     decrypted_data = decrypt_response(payload_dict)

#     doc = frappe.new_doc("HKM API Call")
#     doc.api_data = make_serializable(
#         {
#             "source": source,
#             "raw_payload": payload_dict,
#             "decrypted_data": decrypted_data,
#         }
#     )
#     doc.insert(ignore_permissions=True)
#     frappe.db.commit()

#     return {"status": "success", "message": "Payload received successfully"}


# def decrypt_response(encrypted_response):
#     """
#     Decrypt the response from ICICI Bank
#     """
#     try:
#         private_key = get_private_key()
#         if not private_key:
#             return None

#         # Base64 decode first
#         encrypted_data = base64.b64decode(encrypted_response)

#         # Decrypt using private key
#         decrypted_data = private_key.decrypt(encrypted_data, padding.PKCS1v15())

#         # Convert to string and parse JSON
#         response_json = json.loads(decrypted_data.decode("utf-8"))
#         return response_json

#     except Exception as e:
#         print(f"Error decrypting response: {e}")
#         return None


# def get_private_key():
#     """
#     Load private key for decrypting responses
#     """
#     try:
#         # For testing, using the Let's Encrypt private key
#         # In production, you should use your merchant-specific private key
#         with open("/etc/letsencrypt/live/hkmjerp.in/privkey.pem", "r") as file:
#             private_key_content = file.read()

#         private_key = serialization.load_pem_private_key(
#             private_key_content.encode("utf-8"),
#             password=None,
#             backend=default_backend(),
#         )
#         return private_key

#     except Exception as e:
#         print(f"Error loading private key: {e}")
#         return None


def make_serializable(obj):
    """Recursively convert frappe._dict to plain dict so it's JSON-serializable"""
    from frappe import _dict  # import _dict locally

    if isinstance(obj, _dict):
        obj = dict(obj)
    if isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [make_serializable(i) for i in obj]
    return obj
