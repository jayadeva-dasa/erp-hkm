# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

# import frappe
import calendar
from datetime import datetime

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class InternalAdjustment(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF
        from hkm.erpnext___custom.doctype.internal_adjustment_detail.internal_adjustment_detail import InternalAdjustmentDetail

        adjustment_for: DF.Literal["Income", "Expense"]
        amended_from: DF.Link | None
        entries: DF.Table[InternalAdjustmentDetail]
        internal_adjustment_creator: DF.Link | None
        posting_date: DF.Date
        remarks: DF.SmallText | None
        type: DF.Link
    # end: auto-generated types
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    def validate(self):
        self.validate_root_type()
        self.validate_debit_credit()
        self.validate_total()
        # self.validate_adjustment_amount()

    # def validate_adjustment_amount(self):
    #     def get_current_month_date_range(posting_date):
    #         if isinstance(posting_date, str):
    #             posting_date = datetime.strptime(posting_date, "%Y-%m-%d").date()

    #         start_date = posting_date.replace(day=1)
    #         last_day = calendar.monthrange(posting_date.year, posting_date.month)[1]
    #         end_date = posting_date.replace(day=last_day)

    #         return start_date, end_date

    #     start_date, end_date = get_current_month_date_range(self.posting_date)
    #     new_internal_adjustment_map = {}
    #     cost_heads = set()
    #     accounts = set()

    #     for i in self.entries:
    #         key = f"{i.account} - {i.cost_head}"
    #         new_internal_adjustment_map[key] = new_internal_adjustment_map.get(
    #             key, 0
    #         ) + (i.debit or 0 - i.credit or 0)
    #         cost_heads.add(i.cost_head)
    #         accounts.add(i.account)

    #     gl_query = """
	# 		SELECT 
	# 			gl.account,
	# 			gl.cost_head,
	# 			SUM(gl.debit - gl.credit) as amount
	# 		FROM `tabGL Entry` gl
	# 		JOIN `tabAccount` tac ON tac.name = gl.account
	# 		WHERE tac.report_type = 'Profit and Loss'
	# 			AND tac.root_type = %(root_type)s
	# 			AND gl.is_cancelled = 0
	# 			AND gl.account IN %(accounts)s
	# 			AND gl.cost_head IN %(cost_heads)s
	# 			AND gl.posting_date BETWEEN %(start_date)s AND %(end_date)s
	# 		GROUP BY gl.account, gl.cost_head
	# 	"""
    #     gl_result = frappe.db.sql(
    #         gl_query,
    #         {
    #             "root_type": self.adjustment_for,
    #             "start_date": start_date,
    #             "end_date": end_date,
    #             "accounts": tuple(accounts),
    #             "cost_heads": tuple(cost_heads),
    #         },
    #         as_dict=True,
    #     )

    #     gl_adjustment_map = {
    #         f"{r.account} - {r.cost_head}": r.amount for r in gl_result
    #     }

    #     internal_adjustment_query = """
	# 		SELECT 
	# 			iai.account,
	# 			iai.cost_head,
	# 			SUM(iai.debit - iai.credit) as amount
	# 		FROM `tabInternal Adjustment` ia
	# 		JOIN `tabInternal Adjustment Detail` iai ON iai.parent = ia.name
	# 		WHERE ia.docstatus = 1
	# 			AND ia.posting_date BETWEEN %(start_date)s AND %(end_date)s
	# 			AND ia.adjustment_for = %(root_type)s
	# 			AND iai.account IN %(accounts)s
	# 			AND iai.cost_head IN %(cost_heads)s
	# 		GROUP BY iai.account, iai.cost_head
	# 	"""
    #     internal_adjustment_result = frappe.db.sql(
    #         internal_adjustment_query,
    #         {
    #             "root_type": self.adjustment_for,
    #             "start_date": start_date,
    #             "end_date": end_date,
    #             "accounts": tuple(accounts),
    #             "cost_heads": tuple(cost_heads),
    #         },
    #         as_dict=True,
    #     )

    #     internal_adjustment_map = {
    #         f"{r.account} - {r.cost_head}": r.amount for r in internal_adjustment_result
    #     }

    #     for key in new_internal_adjustment_map:
    #         gl_amount = gl_adjustment_map.get(key, 0)
    #         internal_amount = internal_adjustment_map.get(key, 0)
    #         current_amount = new_internal_adjustment_map[key]

    #         net_total = gl_amount + internal_amount + current_amount

    #         if self.adjustment_for == "Expense":
    #             if net_total < 0:
    #                 frappe.throw(_("Adjustment Amount Not Allowed"))
    #         else:
    #             if net_total > 0:
    #                 frappe.throw(_("Adjustment Amount Not Allowed"))

    def validate_root_type(self):
        check_account = "Expense" if self.adjustment_for == "Income" else "Income"
        accounts = [e.account for e in self.entries]
        expense = frappe.get_all(
            "Account",
            filters={"name": ["in", accounts], "root_type": check_account},
            pluck="name",
            limit=1,
        )
        if expense:
            frappe.throw(
                f"{check_account} Account '{expense[0]}' is not allowed in a {self.adjustment_for} Adjustment."
            )
        return

    def validate_debit_credit(self):
        for e in self.entries:
            if e.debit and e.credit:
                frappe.throw("Debit and Credit cannot be both Allocated")

        return

    def validate_total(self):
        total_debit = sum([e.debit or 0 for e in self.entries])
        total_credit = sum([e.credit or 0 for e in self.entries])
        if flt(total_debit, 1) != flt(total_credit, 1):
            frappe.throw(
                f"Total Debit and Credit must be equal. Debit: {total_debit}, Credit: {total_credit}"
            )
        return
