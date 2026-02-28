#
from __future__ import unicode_literals
from frappe import _


def get_data():
    return {
        "heatmap": False,
        "fieldname": "cost_head",
        "transactions": [
            {
                "label": _("Links"),
                "items": ["Donation Receipt", "Journal Entry"],
            },
            {
                "label": _("Purchase"),
                "items": [
                    "Purchase Order",
                    "Purchase Invoice",
                ],
            },
            {
                "label": _("Sales"),
                "items": ["Sales Order", "POS Invoice"],
            },
            # {"label": _("Festival Benefits"), "items": ["Donor Festival Benefit"]},
            # {"label": _("Reminders"), "items": ["DJ Reminder"]},
        ],
    }
