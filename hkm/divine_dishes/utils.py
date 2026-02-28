import frappe


def user_wallet_balance(user):
    if user is None:
        user = frappe.session.user

    txs = frappe.get_all(
        "DD Wallet Tx",
        fields=["final_balance"],
        order_by="creation desc",
        filters={"user": user},
    )
    if len(txs) == 0:
        return 0
    return txs[0].final_balance


def validate_address(user=None):
    if not user:
        user = frappe.sessions.user
    addresses = frappe.get_all(
        "DD User Address",
        filters=[["user", "=", user], ["status", "=", "Approved"]],
        pluck="name",
    )
    if len(addresses) == 0:
        frappe.throw("At least one Address is required to be approved.")
    return
