import frappe


def list_filter(user=None):
    user = user or frappe.session.user
    user_roles = frappe.get_roles(user)

    if frappe.session.user == "Administrator":
        return "( 1 )"

    if any(role in ["System Manager", "HKM Cashier"] for role in user_roles):
        return "( 1 )"

    allowed_docs = []
    direct_approval = []

    if "HKM Expense Voucher Approver" in user_roles:
        setting_doc = frappe.get_cached_doc("DED Settings")
        personal_cost_heads = [
            i.cost_head for i in setting_doc.personal_expenses_cost_heads
        ]

        direct_approval = frappe.get_all(
            "HKM Expense Voucher",
            filters={"approving_authority": user, "workflow_state": "Pending"},
            pluck="name",
        )

        approver_allowed = frappe.get_all(
            "Cost Head Expense Approver",
            filters={"user": user, "parent": ["not in", personal_cost_heads]},
            pluck="parent",
        )

        cost_heads = set(approver_allowed)

        for approver in approver_allowed:
            descendants = frappe.db.get_descendants("Cost Head", approver)
            cost_heads.update(descendants)

        cost_heads.difference_update(set(personal_cost_heads))

        if cost_heads:
            allowed_docs += frappe.get_all(
                "HKM Expense Voucher",
                filters={
                    "cost_head": ["in", list(cost_heads)],
                    "workflow_state": "Pending",
                },
                pluck="name",
            )

    if "DED User" in user_roles:
        allowed_docs += frappe.get_all(
            "HKM Expense Voucher",
            filters={"owner": user},
            pluck="name",
        )

    if allowed_docs or direct_approval:
        all_vouchers = set(allowed_docs + direct_approval)
        all_vouchers_str = ",".join(f"'{doc}'" for doc in all_vouchers)
        return f"(`name` in ({all_vouchers_str}))"

    return "( 0 )"


def has_single_access(doc, user=None):
    user = user or frappe.session.user
    user_roles = frappe.get_roles(user)
    has_full_access = any(
        role in ["System Manager", "Administrator", "HKM Cashier"]
        for role in user_roles
    )
    if has_full_access:
        return True
    if doc.owner == user:
        return True
    allowed_docs = []
    direct_approval = []
    if "HKM Expense Voucher Approver" in user_roles:
        setting_doc = frappe.get_cached_doc("DED Settings")
        personal_cost_heads = [
            i.cost_head for i in setting_doc.personal_expenses_cost_heads
        ]

        direct_approval = frappe.get_all(
            "HKM Expense Voucher",
            filters={"approving_authority": user, "workflow_state": "Pending"},
            pluck="name",
        )

        approver_allowed = frappe.get_all(
            "Cost Head Expense Approver",
            filters={"user": frappe.session.user},
            pluck="parent",
        )
        cost_heads = set(approver_allowed)

        for approver in approver_allowed:
            descendants = frappe.db.get_descendants("Cost Head", approver)
            cost_heads.update(descendants)

        cost_heads.difference_update(set(personal_cost_heads))

        if cost_heads:
            allowed_docs = frappe.get_all(
                "HKM Expense Voucher",
                filters={
                    "cost_head": ["in", list(cost_heads)],
                    "workflow_state": "Pending",
                    "name": doc.name,
                },
                pluck="name",
            )
    if allowed_docs or direct_approval:
        all_vouchers = set(allowed_docs + direct_approval)
        if doc.name in all_vouchers:
            return True
    return False
