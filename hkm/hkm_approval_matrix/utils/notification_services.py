"""
Notification services for HKM Approval Matrix.
This module handles all notification-related functionality including
WhatsApp messages, emails, and eligibility checks.
"""

import frappe
import requests
import json
from frappe.utils.data import cstr
from frappe.model.document import Document

from cryptography.fernet import Fernet


from urllib.parse import urlencode
from frappe.utils.data import get_url as get_url_frappe


from frappe.utils.verified_command import get_signed_params


def get_url(doctype, docname, action, user, confirm=False):
    """Generate encrypted URL for approval actions."""
    suffix = "confirm" if confirm else "apply"
    link = f"/api/method/hkm.api.v1.general.approval_matrix_{suffix}_action"
    params_dict = {
        "doctype": doctype,
        "docname": docname,
        "action": action,
        "user": user,
    }
    secret_key = get_secret_key()
    encrypted_data = (
        Fernet(secret_key).encrypt(urlencode(params_dict).encode()).decode()
    )

    # Pass the encrypted data as a 'data' parameter
    params = {"data": encrypted_data}
    return get_url_frappe(link + "?" + get_signed_params(params))


def get_secret_key():
    """Get or generate secret key for encryption."""
    key = frappe.get_single("HKM General Settings")
    if key.approval_email_fernet_key:
        return key.approval_email_fernet_key.encode()
    else:
        secret = Fernet.generate_key().decode()
        key.approval_email_fernet_key = secret
        key.save(ignore_permissions=1)
        return secret.encode()


def is_eligible_to_send_on_whatsapp(user, mobile_no):
    """Check if user is eligible to receive WhatsApp approval notifications."""
    # Check if user has WhatsApp approval enabled
    user_meta = frappe.get_meta("User")
    if user_meta.has_field("purchase_order_whatsapp_approval"):
        if not frappe.get_value("User", user, "purchase_order_whatsapp_approval"):
            return False

    # Check system settings and mobile number availability
    po_approval_settings = frappe.get_cached_doc("HKM General Settings")
    return bool(po_approval_settings.po_approval_on_whatsapp and mobile_no)


def get_short_link_name(long_link):
    """Create a short redirect link for approval URLs."""
    doc = frappe.get_doc(
        {"doctype": "HKM Redirect", "redirect_to": long_link, "ephemeral": 1}
    )
    doc.insert(ignore_permissions=True)
    return doc.name


def send_via_meta(docname, doc: Document, mobile_no, approval_link_name, rejection_link_name, settings, po_approval_settings, url, po_image_link):
    """Send WhatsApp approval notification via Meta (Facebook) API."""
    try:
        payload = json.dumps(
            {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": f"+91{mobile_no}",
                "type": "template",
                "template": {
                    "name": po_approval_settings.po_whatsapp_template,
                    "language": {"code": "en"},
                    "components": [
                        {
                            "type": "header",
                            "parameters": [
                                {"type": "image", "image": {"link": po_image_link}}
                            ],
                        },
                        {
                            "type": "body",
                            "parameters": [
                                {"type": "text", "text": doc.execution_department or "N/A"},
                                {"type": "text", "text": doc.name or "N/A"},
                                {"type": "text", "text": doc.supplier_name or "N/A"},
                                {
                                    "type": "text",
                                    "text": frappe.db.get_value(
                                        doc.doctype, docname, "approval_status"
                                    )
                                    or "N/A",
                                },
                                {
                                    "type": "text",
                                    "text": frappe.utils.fmt_money(
                                        doc.grand_total or 0,
                                        currency=doc.currency or "INR",
                                        precision=2,
                                    )
                                    or "0",
                                },
                            ],
                        },
                        {
                            "type": "button",
                            "index": "0",
                            "sub_type": "url",
                            "parameters": [
                                {"type": "text", "text": approval_link_name or "approve"},
                            ],
                        },
                        {
                            "type": "button",
                            "index": "1",
                            "sub_type": "url",
                            "parameters": [
                                {"type": "text", "text": rejection_link_name or "reject"},
                            ],
                        },
                    ],
                },
            }
        )
        headers = {
            "Content-Type": "application/json",
            "Authorization": f'Bearer {settings.get_password("token")}',
        }

        response = requests.request("POST", url, headers=headers, data=payload, timeout=30)
        
        if response.status_code != 200:
            frappe.log_error(
                title="Meta WhatsApp Purchase Order Error",
                message=f"Status: {response.status_code}\nResponse: {response.text}"
            )
        
        return response
    
    except Exception as e:
        frappe.log_error(
            title="Meta WhatsApp Purchase Order Exception",
            message=f"Error sending WhatsApp via Meta: {str(e)}\n{frappe.get_traceback()}"
        )
        return None


def send_via_smartPing(docname, doc: Document, mobile_no, approval_link_name, rejection_link_name, po_approval_settings, url, po_image_link):
    """Send WhatsApp approval notification via SmartPing API."""
    try:
        smartping_settings = frappe.get_cached_doc("SmartPing Settings")

        api_key = smartping_settings.get_password("api_key")
        user_name = smartping_settings.user_name
        campaign_name = po_approval_settings.po_whatsapp_template
        url = "https://backend.api-wa.co/campaign/smartpingbsp/api/v2"

        TEMPLATE_PARAMS = [
            cstr(doc.execution_department) or "N/A",
            cstr(doc.name) or "N/A",
            cstr(doc.supplier_name) or "N/A",
            # cstr(frappe.db.get_value(
            #     doc.doctype, docname, "approval_status"
            # )) or "N/A",
            cstr(frappe.utils.fmt_money(
                doc.grand_total or 0,
                currency=doc.currency or "INR",
                precision=2,
            )) or "0",
        ]

        payload = {
            "apiKey": api_key,
            "campaignName": "po__approval",
            "destination": mobile_no,
            "userName": user_name,
            "templateParams": TEMPLATE_PARAMS,
            "media": {
                "url": po_image_link,
                "filename": f"approval_{doc.name}.png"
            },
            "buttons": [
                {
                    "type": "button",
                    "sub_type": "URL",
                    "index": 0,
                    "parameters": [
                        {
                            "type": "text",
                            "text": approval_link_name
                        }
                    ]
                },
                {
                    "type": "button",
                    "sub_type": "URL",
                    "index": 1,
                    "parameters": [
                        {
                            "type": "text",
                            "text": rejection_link_name
                        }
                    ]
                }
            ],

        }
        headers = {"Content-Type": "application/json"}

        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        frappe.logger().debug(f"SmartPing WhatsApp Response: {response.text}")

        if response.status_code != 200:
            frappe.log_error(
                title="Smartping WhatsApp Purchase Order Error",
                message=f"Status: {response.status_code}\nResponse: {response.text}"
            )
        
        return response
    
    except Exception as e:
        frappe.log_error(
            title="Smartping WhatsApp Purchase Order Exception",
            message=f"Error sending WhatsApp via SmartPing: {str(e)}\n{frappe.get_traceback()}"
        )
        return None


def send_whatsapp_approval(
    doctype, docname, doc: Document, approving_authority, mobile_no
):
    """Send WhatsApp approval notification to the authority."""
    approval_link = get_url(
        doctype,
        docname,
        "Approve",
        approving_authority,
        confirm=True,
    )
    rejection_link = get_url(
        doctype,
        docname,
        "Reject",
        approving_authority,
        confirm=True,
    )
    approval_link_name = get_short_link_name(approval_link)
    rejection_link_name = get_short_link_name(rejection_link)

    settings = frappe.get_cached_doc("WhatsApp Settings")
    po_approval_settings = frappe.get_cached_doc("HKM General Settings")
    url = f"{settings.url}/{settings.version}/{settings.phone_id}/messages"

    site_name = cstr(frappe.local.site)

    po_image_link = f"https://{site_name}/api/method/hkm.hkm_approval_matrix.main.get_purchase_order_image?docname={docname}"

    if frappe.get_cached_doc("HKM General Settings").smartping_enabled:
        return send_via_smartPing(
            docname, doc, mobile_no, approval_link_name, rejection_link_name, po_approval_settings, url, po_image_link
        )

    return send_via_meta(
        docname, doc, mobile_no, approval_link_name, rejection_link_name, settings, po_approval_settings, url, po_image_link
    )


def send_approval_email(doctype, docname, doc: Document, approving_authority):
    """Send approval email notification to the authority."""
    currency = frappe.get_cached_value(
        "Company", doc.company, "default_currency")

    # doc_obj = frappe.get_doc(doctype, docname)

    template_data = {
        "doc": doc,
        "user": approving_authority,
        "currency": currency,
        "approval_link": get_url(doctype, docname, "Approve", approving_authority),
        "rejection_link": get_url(doctype, docname, "Reject", approving_authority),
        "document_link": frappe.utils.get_url_to_form(doctype, docname),
        "approving_authority": doc.get("approving_authorities"),
    }
    email_args = {
        "recipients": [approving_authority],
        "message": frappe.render_template(
            "hkm/hkm_approval_matrix/utils/template/email_template.html",
            template_data,
        ),
        "subject": f"#{doctype[:2]} :{docname} Approval",
        "reference_doctype": doctype,
        "reference_name": docname,
        "reply_to": (doc.owner if not doc.owner == "Administrator" else None),
        "delayed": False,
        "sender": doc.owner if not doc.owner == "Administrator" else None,
    }
    frappe.enqueue(frappe.sendmail, queue="default", **email_args)


def send_approval_notification(doctype, docname, doc=None):
    """Send approval notification to the next authority via WhatsApp or Email."""
    from .general import get_current_approving_authority

    # Get next approving authority and send notification

    approving_authority = get_current_approving_authority(doctype, docname)

    if approving_authority:
        doc = doc or frappe.get_doc(doctype, docname)
        mobile_no = frappe.get_value("User", approving_authority, "mobile_no")

        if is_eligible_to_send_on_whatsapp(approving_authority, mobile_no):
            send_whatsapp_approval(
                doctype, docname, doc, approving_authority, mobile_no
            )
        else:
            send_approval_email(doctype, docname, doc, approving_authority)


def send_rejected_email(doctype, docname, user):
    """Send rejection email to document creator and approved authorities."""
    po_creator = frappe.db.get_value(doctype, docname, "owner")
    url = frappe.utils.get_url_to_form(doctype, docname)

    # Email template for document creator
    message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; font-size: 14px; color: #333;">
            <p>{doctype} Rejected by {user}</p>
            <h3>Details:</h3>
            <a 
            href="{url}"
            style="
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 12px 24px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 14px;
                border-radius: 4px;
            ">
            Click to open Document
            </a>
            <p>Regards,<br>ERP System</p>
        </body>
    </html>
    """

    frappe.sendmail(
        recipients=[po_creator],
        subject=f"{doctype} Rejected",
        message=message,
    )

    # Notify previously approved authorities
    approved_authorities = frappe.get_all(
        "Approval Matrix Authority",
        filters={
            "parent": docname,
            "status": "Approved",
            "parenttype": doctype,
        },
        order_by="idx ASC",
        pluck="authority",
    )

    if approved_authorities:
        message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; font-size: 14px; color: #333;">
                <p>{doctype} that you have approved is rejected by {user}</p>
                <h3>Details:</h3>
                <a 
                href="{url}"
                style="
                    background-color: #4CAF50;
                    border: none;
                    color: white;
                    padding: 12px 24px;
                    text-align: center;
                    text-decoration: none;
                    display: inline-block;
                    font-size: 14px;
                    border-radius: 4px;
                ">
                Click to open Document
                </a>
                <p>Regards,<br>ERP System</p>
            </body>
        </html>
        """
        frappe.sendmail(
            recipients=approved_authorities,
            subject=f"{doctype} Rejected",
            message=message,
        )


def notify_next_authority(doc: Document):
    from .general import get_current_approving_authority

    """Notify next authority in the approval matrix."""

    old_doc = doc.get_doc_before_save()

    # Handle case when old_doc is None (new document or first save)
    if not old_doc:
        return

    old_auth = {row.name: row for row in old_doc.approving_authorities}
    for row in doc.approving_authorities:
        old_row = old_auth.get(row.name)
        # Handle case when old_row is None (new row added)
        old_status = getattr(old_row, "status", None) if old_row else None
        new_status = getattr(row, "status", None)

        if old_status != new_status:
            doctype = doc.doctype
            docname = doc.name

            if row.status == "Approved":
                send_approval_notification(
                    doctype,
                    docname,
                )
                assign_to_authority(
                    doctype, docname, get_current_approving_authority(
                        doctype, docname)
                )

            elif row.status == "Rejected":
                send_rejected_email(
                    doctype, docname, get_current_approving_authority(
                        doctype, docname)
                )


def assign_to_authority(doctype, docname, user):
    if frappe.db.exists(
        "ToDo",
        {"reference_type": doctype, "reference_name": docname, "allocated_to": user},
    ):
        frappe.log_error(
            "ToDo already exists for {doctype} {docname} for {user}".format(
                doctype=doctype, docname=docname, user=user
            )
        )
        return
    frappe.get_doc(
        {
            "doctype": "ToDo",
            "allocated_to": user,
            "reference_type": doctype,
            "reference_name": docname,
            "description": f"{doctype} {docname} is assigned to you for approval.",
            "priority": "Medium",
            "status": "Open",
            "date": frappe.utils.nowdate(),
            "assigned_by": frappe.session.user,
            "assignment_rule": "",
        }
    ).insert(ignore_permissions=True)
    frappe.db.commit()  # v16: REVIEW - check if needed
