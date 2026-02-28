# Copyright (c) 2023, Narahari Dasa and contributors
# For license information, please see license.txt

from hkm.divine_dishes.utils import validate_address
import frappe
from frappe.model.document import Document
from frappe.utils.data import now


class DDOrder(Document):
    def validate(self):
        validate_address(self.user)

    def before_save(self):
        total_amount = 0
        if not self.date:
            self.date = now()
        for item in self.items:
            price = frappe.get_value("DD Item", item.item, "price")
            item.amount = price * item.qty
            total_amount += item.amount
        self.total_amount = total_amount

    def on_update(self):
        if self.status == "Delivered":
            settings_doc = frappe.get_cached_doc("Divine Dishes Settings")
            doc = frappe.get_doc(
                {
                    "doctype": "App Notification",
                    "app": settings_doc.firebase_app,
                    "notify": 1,
                    "user": self.user,
                    "subject": "Order Delivered!",
                    "message": f"Please check the Order for more details.",
                    "is_route": 1,
                    "route": f"/order/{self.name}",
                }
            )
            doc.insert(ignore_permissions=True)


@frappe.whitelist()
def mark_delivered(docname):
    user_roles = frappe.get_roles()
    if "DD Manager" not in user_roles:
        frappe.throw("You are not Allowed.")
    doc = frappe.get_doc("DD Order", docname)
    doc.status = "Delivered"
    doc.save(ignore_permissions=True)
