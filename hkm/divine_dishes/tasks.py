import frappe
from datetime import datetime, timedelta

from hkm.divine_dishes.utils import user_wallet_balance


def every_day_evening():
    create_subscription_orders()


def create_subscription_orders():
    tomorrow_weekday = (datetime.now() + timedelta(days=1)).strftime("%A")

    subscriptions = frappe.get_all("DD Subscription", filters={"running": 1}, pluck="name")

    users = {}

    for s in subscriptions:
        subscription_doc = frappe.get_doc("DD Subscription", s)
        for schd in subscription_doc.schedule:
            if schd.week_day == tomorrow_weekday:
                if subscription_doc.user not in users:
                    users.setdefault(subscription_doc.user, [])
                schd_order_item = frappe._dict(item=subscription_doc.item, qty=schd.qty)
                users[subscription_doc.user].append(schd_order_item)

    for u in users:
        check_order(u, users[u])


def check_order(user, orders):
    # settings = frappe.get_cached_doc("E Commerce Settings")
    total_amount = 0
    for order in orders:
        dd_item = frappe.get_cached_doc("DD Item", order["item"])
        amount = dd_item.price * order["qty"]
        total_amount += amount
    settings_doc = frappe.get_cached_doc("Divine Dishes Settings")
    if user_wallet_balance(user) >= total_amount:
        if process_order(user, orders):
            make_wallet_tx(user, total_amount)
            doc = frappe.get_doc(
                {
                    "doctype": "App Notification",
                    "app": settings_doc.firebase_app,
                    "notify": 1,
                    "user": user,
                    "subject": "Subscription Order Created & Paid from Wallet",
                    "message": f"There is a deduction of {total_amount} from your Wallet to pay for Subscription Order."
                }
            )
            doc.insert(ignore_permissions=True)
    else:
        doc = frappe.get_doc(
            {
                "doctype": "App Notification",
                "app": settings_doc.firebase_app,
                "notify": 1,
                "user": user,
                "subject": "Insufficient Wallet Balance",
                "message": f"Your subscriptions couldn't convert into order due to insufficient funds in Wallet. Please recharge."
            }
        )
        doc.insert(ignore_permissions=True)
    
    frappe.db.commit()  # v16: OK - background task


def process_order(user, orders) -> bool:
    try:
        doc = frappe.get_doc(
            {
                "doctype": "DD Order",
                "user": user,
                "status": "Paid",
                "items": orders,
                "auto_generated": 1,
            }
        )
        doc.insert()
        return True
    except:
        return False


def make_wallet_tx(user, amount):
    doc = frappe.get_doc(
        {"doctype": "DD Wallet Tx", "withdrawl": amount, "user": user, "remarks": "Deducted to pay for Subscription."}
    )
    doc.insert()
