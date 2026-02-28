# Copyright (c) 2024, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

states = ("Pending Approval", "Recommended", "First Approved", "Final Approved")
approvers = ("recommender", "first_approver", "final_approver")


class HKMVoucher(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF
        from hkm.erpnext___custom.doctype.hkm_voucher_detail.hkm_voucher_detail import (
            HKMVoucherDetail,
        )

        amended_from: DF.Link | None
        company: DF.Link
        department: DF.Link
        expense_head: DF.Link | None
        final_approver: DF.Link | None
        first_approver: DF.Link | None
        grand_total: DF.Currency
        items: DF.Table[HKMVoucherDetail]
        next_approver: DF.Link | None
        posting_date: DF.Date
        recommender: DF.Link | None
        status: DF.Literal[
            "Pending Approval", "Recommended", "First Approved", "Final Approved"
        ]
        user: DF.Link
        user_supplier_link: DF.Link
    # end: auto-generated types

    def on_submit(self):
        self.set_next_approver()

    def get_alm_level(self, amount_field="grand_total"):
        deciding_amount = getattr(self, amount_field)
        ## We are only using REVEX
        for l in frappe.db.sql(
            f"""
                    SELECT level.*
                    FROM `tabALM` alm
                    JOIN `tabALM Level` level
                        ON level.parent = alm.name
                    WHERE alm.document = "{self.doctype}"
                        AND alm.company = "{self.company}"
                        AND level.department = "{self.department}"
                    ORDER BY level.idx
                        """,
            as_dict=1,
        ):
            if eval(f"{deciding_amount} {l.amount_condition}"):
                return l
        return None

    def set_next_approver(self):
        user = None
        alm_level = self.get_alm_level()
        if not alm_level:
            frappe.throw("ALM is not set.")

        current_status = self.status

        for i, state in enumerate(states):
            if current_status == state:
                for approver in approvers[i : len(approvers)]:
                    approver_user = getattr(alm_level, approver)
                    if approver_user:
                        user = approver_user
                        break
                break
        if user is None:
            frappe.throw("Next authority is not Found. Please check ALM.")
        frappe.db.set_value(self.doctype, self.name, "next_approver", user)
        frappe.db.commit()  # v16: REVIEW - check if needed


def test():
    approve(doc="7450f31096-2")


@frappe.whitelist()
def approve(doc):
    user = frappe.session.user
    doc = frappe.get_doc("HKM Voucher", doc)

    if doc.docstatus != 1:
        frappe.throw("Document must be submitted first.")

    if doc.next_approver != user:
        frappe.throw("You are not allowed to approve.")

    alm_level = doc.get_alm_level()

    print(alm_level)
    if not alm_level:
        frappe.throw("ALM is not set.")

    next_state = None

    for i, approver in enumerate(approvers):
        print(approver)
        print(doc.next_approver)
        print(getattr(alm_level, approver))
        print(states[i + 1])
        if doc.next_approver == getattr(alm_level, approver) and (
            states[i + 1] != doc.status
        ):
            next_state = states[i + 1]
            break

    frappe.db.set_value(doc.doctype, doc.name, "status", next_state)
    frappe.db.commit()  # v16: REVIEW - check if needed
    doc.reload()
    doc.set_next_approver()
