import json
from hkm.divine_dishes.utils import validate_address
import frappe
import razorpay


@frappe.whitelist()
def create_razorpay_order(data):
    validate_address(frappe.session.user)
    data = json.loads(data)
    settings = frappe.get_single("Divine Dishes Settings")
    RAZORPAY_ID = settings.razorpay_id
    RAZORPAY_SECRET = settings.get_password("razorpay_secret")
    client = razorpay.Client(auth=(RAZORPAY_ID, RAZORPAY_SECRET))
    response = client.order.create(data)
    return response


@frappe.whitelist(allow_guest=True)
def webhook():
    settings = frappe.get_single("Divine Dishes Settings")

    RAZORPAY_ID = settings.razorpay_id
    RAZORPAY_SECRET = settings.get_password("razorpay_secret")
    WEBHOOK_SECRET = settings.get_password("webhook_secret")

    client = razorpay.Client(auth=(RAZORPAY_ID, RAZORPAY_SECRET))
    signature = frappe.request.headers["X-Razorpay-Signature"]
    payload = frappe.request.data.decode()
    try:
        client.utility.verify_webhook_signature(payload, signature, WEBHOOK_SECRET)
    except Exception as e:
        return "Error Occured"

    payload = json.loads(payload)

    if payload["event"] == "payment.captured":
        payment_payload = payload["payload"]["payment"]["entity"]

        if payment_payload["description"] == "Adding Credits to Wallet":
            add_wallet_credits(payment_payload)
        elif payment_payload["description"] == "Cart Purchase":
            update_dd_order(payment_payload)


def add_wallet_credits(payload: dict):
    document = frappe._dict(
        doctype="DD Wallet Tx",
        user=payload["email"],
        deposit=payload["amount"] / 100,
        payment_id=payload["id"],
        order_id=payload["order_id"],
        remarks=f"Credits added to Wallet.",
    )
    doc = frappe.get_doc(document)
    doc.insert(ignore_permissions=True)
    frappe.db.commit()  # v16: REVIEW - check if needed


def update_dd_order(payload: dict):
    frappe.db.sql(
        f"""
                    update `tabDD Order`
                    SET status = 'Paid', razorpay_payment_id = "{payload['id']}"
                    WHERE razorpay_order_id = "{payload['order_id']}"
                    """
    )
    frappe.db.commit()  # v16: REVIEW - check if needed


# {"entity":"event","account_id":"acc_ADiJYeIA9mhcig","event":"payment.captured","contains":["payment"],"payload":{"payment":{"entity":{"id":"pay_MY9l0Ms6TL9ilY","entity":"payment","amount":10000,"currency":"INR","status":"captured","order_id":"order_MY9kk8NL1HwA1r","invoice_id":null,"international":false,"method":"upi","amount_refunded":0,"refund_status":null,"captured":true,"description":"Adding Credits to Wallet","card_id":null,"bank":null,"wallet":null,"vpa":"success@razorpay","email":"2011uec1274@mnit.ac.in","contact":"+917357010770","notes":{"purpose":"Adding Credits to Wallet"},"fee":236,"tax":36,"error_code":null,"error_description":null,"error_source":null,"error_step":null,"error_reason":null,"acquirer_data":{"rrn":"746326587376","upi_transaction_id":"CE0288C6DDED746A38727E6964B3A438"},"created_at":1693808232,"upi":{"vpa":"success@razorpay"},"base_amount":10000}}},"created_at":1693808232}
