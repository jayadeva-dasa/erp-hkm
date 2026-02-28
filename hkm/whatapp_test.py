import json

import requests

import frappe


def execute():
    settings = frappe.get_cached_doc("WhatsApp Settings")
    url = f"{settings.url}/{settings.version}/{settings.phone_id}/messages"
    message = """Hare Krishna

                    Please find attached payment advice for our recent payment to your account.

                    Please call at 9727930108 or mail at finanace@harekrishnamandir.org for any query."""
    payload = json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": f"+917357010770",
            "type": "template",
            "template": {
                "name": "payment_advice",
                "language": {"code": "en_US"},
                "components": [
                    {
                        "type": "header",
                        "parameters": [
                            {
                                "type": "document",
                                "document": {
                                    "filename": "MRRATH-CGK-KUL.pdf",
                                    "link": "https://erp.harekrishnamandir.org/file/d48af64fee/IMG_20240812_0015.pdf",
                                },
                            }
                        ],
                    },
                    # {
                    #     "type": "body",
                    #     "parameters": [
                    #         {"type": "text", "text": message},
                    #     ],
                    # },
                ],
            },
        }
    )
    headers = {
        "Content-Type": "application/json",
        "Authorization": f'Bearer {settings.get_password("token")}',
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)
