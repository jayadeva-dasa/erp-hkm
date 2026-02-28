import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_request_session
import json

@frappe.whitelist(allow_guest=True)
def handle_webhook(*args, **kwargs):
    frappe.logger(__name__).debug("Recording Data")
    data = frappe.request.get_data(as_text=True)
    if isinstance(data, str):
        data = json.loads(data)
    
    event = data['event']

    if event == 'payment.authorized':
        payment_status = 1
        payment_id = data['payload']['payment']['entity']['id']
        amount = data['payload']['payment']['entity']['amount']
        currency = data['payload']['payment']['entity']['currency']
        frappe.logger(__name__).debug("Payment ID: {0} Amount: {1} Currency: {2}".format(payment_id,amount,currency))
        doc = frappe.get_doc({
            'doctype': 'FOLK Event Participant',
            'raw_data': "{}".format(data['payload']['payment'])
        })
        doc.insert(ignore_permissions=True)
        
    return 'OK'