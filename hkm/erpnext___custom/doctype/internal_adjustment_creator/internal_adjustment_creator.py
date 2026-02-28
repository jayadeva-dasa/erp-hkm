# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt
from frappe import _
import json

from frappe.model.document import Document


class InternalAdjustmentCreator(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from hkm.erpnext___custom.doctype.internal_adjustment_creator_account.internal_adjustment_creator_account import InternalAdjustmentCreatorAccount
		from hkm.erpnext___custom.doctype.internal_adjustment_creator_cost_head.internal_adjustment_creator_cost_head import InternalAdjustmentCreatorCostHead

		accounts: DF.Table[InternalAdjustmentCreatorAccount]
		execution_department: DF.Table[InternalAdjustmentCreatorCostHead]
		from_date: DF.Date
		posting_date: DF.Date
		service_department: DF.Table[InternalAdjustmentCreatorCostHead]
		specific_accounts: DF.Check
		to_date: DF.Date
	# end: auto-generated types
	pass








@frappe.whitelist()
def create_internal_adjustment(**args):
    return CreateInternalAdjustment(args).create_document()





def adjustment_entry():
    doc = frappe.get_doc("Internal Adjustment Creator", "24vtelf6og").as_dict()

    args = {
        "service_cost_heads": doc.get("service_department"),
        "execution_cost_heads": doc.get("execution_department"),
        "specific_accounts": doc.get("specific_accounts"),
        "accounts": doc.get("accounts"),
        "from_date": str(doc.get("from_date")),
        "to_date": str(doc.get("to_date")),
    }

    json_args = json.dumps(args)
    create_internal_adjustment(args=json_args)


class CreateInternalAdjustment:
    def __init__(self, args):
        self.service_cost_heads = frappe.parse_json(args.get("service_cost_heads"))
        self.execution_cost_heads = frappe.parse_json(args.get("execution_cost_heads"))
        self.from_date = args.get("from_date")
        self.to_date = args.get("to_date")
        self.posting_date = args.get("posting_date")
        self.all_entries = []
        self.name = args.get("name")
        # frappe.errprint(self.name)

        self.specific_accounts = (
            frappe.parse_json(args.get("specific_accounts"))
            if args.get("specific_accounts")
            else None
        )
        self.accounts = (
            frappe.parse_json(args.get("accounts")) if args.get("accounts") else None
        )

        for head in self.execution_cost_heads:
            head["share"] = flt(head.get("share", 0), 2)

        self.validate()
        self._fetch_existing_adjustments()
        self._build_entries()

    def validate(self):
        if not (
            self.posting_date
            and self.service_cost_heads
            and self.execution_cost_heads
            and self.from_date
            and self.to_date
        ):
            frappe.throw(
                _(
                    "Posting Date, Service/Execution Cost Heads, From Date, and To Date are required."
                )
            )

        self._validate_group_cost_heads(self.service_cost_heads)
        self._validate_group_cost_heads(self.execution_cost_heads)
        self._validate_duplicate_cost_heads()
        self._validate_accounts_root_type()

        total_share = flt(
            sum(flt(i.get("share", 0), 2) for i in self.execution_cost_heads), 2
        )
        if total_share == 0:
            frappe.throw(_("Total share cannot be zero."))
        if total_share > 100:
            frappe.throw(_("Total share cannot be greater than 100."))

    def _validate_group_cost_heads(self, cost_heads):
        names = [i.get("cost_head") for i in cost_heads if i.get("cost_head")]
        if not names:
            return
        result = frappe.db.get_list(
            "Cost Head", filters={"name": ["in", names], "is_group": 1}, pluck="name"
        )
        if result:
            frappe.throw(
                _("Cost Head {0} is a group head and not allowed.").format(result[0])
            )

    def _validate_duplicate_cost_heads(self):
        service = {i.get("cost_head") for i in self.service_cost_heads}
        execution = {i.get("cost_head") for i in self.execution_cost_heads}
        common = service & execution
        if common:
            frappe.throw(_("Duplicate Cost Head found: {0}").format(", ".join(common)))

    def _validate_accounts_root_type(self):
        if not (self.specific_accounts and self.accounts):
            return
        account_names = [i.get("account") for i in self.accounts if i.get("account")]
        if not account_names:
            return
        result = frappe.db.get_list(
            "Account",
            filters={"name": ["in", account_names], "root_type": ["!=", "Expense"]},
            pluck="name",
        )
        if result:
            frappe.throw(_("Account {0} is not an expense account.").format(result[0]))

    def _fetch_gl_data(self):
        cost_heads = [i["cost_head"] for i in self.service_cost_heads]
        filters = [
            "gl.is_cancelled = 0",
            "tac.root_type = 'Expense'",
            "gl.cost_head IN %(cost_heads)s",
        ]
        params = {
            "cost_heads": cost_heads,
            "from_date": self.from_date,
            "to_date": self.to_date,
        }

        if self.from_date:
            filters.append("gl.posting_date BETWEEN %(from_date)s AND %(to_date)s")
        if self.specific_accounts and self.accounts:
            filters.append("gl.account IN %(accounts)s")
            params["accounts"] = [a["account"] for a in self.accounts]

        query = f"""
            SELECT gl.cost_head, gl.account, ROUND(SUM(gl.debit - gl.credit), 2) AS amount
            FROM `tabGL Entry` gl
            JOIN `tabAccount` tac ON tac.name = gl.account
            WHERE {" AND ".join(filters)}
            GROUP BY gl.cost_head, gl.account
        """

        results = frappe.db.sql(query, params, as_dict=True)
        if not results:
            frappe.throw(_("No GL entries found for the given filters."))
        return results

    def _fetch_existing_adjustments(self):
        query = f"""
                SELECT iai.cost_head, 
                iai.account, 
                    ROUND(SUM(iai.debit - iai.credit), 2) AS adjusted_amount
                FROM `tabInternal Adjustment` ia
                JOIN `tabInternal Adjustment Detail` iai ON iai.parent = ia.name
                WHERE ia.adjustment_for = 'Expense'
                  AND ia.posting_date BETWEEN %(from_date)s AND %(to_date)s
                  AND ia.docstatus = 1
                  AND iai.cost_head IN %(cost_heads)s
                GROUP BY iai.cost_head, iai.account
            """
        self.adjusted_entries = (
            frappe.db.sql(
                query,
                {
                    "from_date": self.from_date,
                    "to_date": self.to_date,
                    "cost_heads": [i["cost_head"] for i in self.service_cost_heads],
                },
                as_dict=True,
            )
            or []
        )

    def _build_entries(self):
        gl_data = self._fetch_gl_data()
        gl_map = {}
        gl_map = {
            f"{row['cost_head']}-{row['account']}": frappe._dict(
                {
                    "cost_head": row["cost_head"],
                    "account": row["account"],
                    "amount": flt(row["amount"], 2),  
                }
            )
            for row in gl_data
        }
        
        

        adjusted_map = {
            f"{r['cost_head']}-{r['account']}": flt(r["adjusted_amount"], 2)
            for r in getattr(self, "adjusted_entries", [])
        }

        for key, adjusted_amount in adjusted_map.items():
            if key in gl_map:
                gl_map[key]["amount"] = flt(gl_map[key]["amount"] + adjusted_amount, 2)
            else:
                ## negative adjusted amount
                if adjusted_amount <= 0:
                    continue
                cost_head, account = key.split("-", 1)
                gl_map[key] = frappe._dict(
                    {
                        "cost_head": cost_head,
                        "account": account,
                        "amount": adjusted_amount,
                    }
                )


        



        total_share = flt(sum(flt(e["share"], 2) for e in self.execution_cost_heads), 2)
        for key, entry in gl_map.items():
            amount = flt(entry["amount"], 2)
            credit_amt = flt(amount * total_share / 100, 2)
            
            
            ## negative credit amount
            if credit_amt <= 0:
                continue
            self.all_entries.append(
                frappe._dict(
                    account=entry["account"],
                    cost_head=entry["cost_head"],
                    credit=credit_amt,
                    debit=0,
                )
            )

            valid_exec_heads = [e for e in self.execution_cost_heads if e.get("share")]
            distributed = 0
            for idx, exec in enumerate(valid_exec_heads):
                if idx == len(valid_exec_heads) - 1:
                    debit_amt = flt(credit_amt - distributed, 2)
                else:
                    debit_amt = flt(credit_amt * flt(exec["share"], 2) / 100, 2)
                    distributed = flt(distributed + debit_amt, 2)

                self.all_entries.append(
                    frappe._dict(
                        account=entry["account"],
                        cost_head=exec["cost_head"],
                        debit=debit_amt,
                        credit=0,
                    )
                )
                
        # ## missing adjustment the key that are in adjusted_map but not in gl_map
        # missing_adjustments = {
        #     key: adjusted_amount
        #     for key, adjusted_amount in adjusted_map.items()
        #     if key not in gl_map
        # }


        # for key, adjusted_amount in missing_adjustments.items():
        #     if adjusted_amount <= 0:
        #         continue  

        #     cost_head, account = key.split("-", 1)
        #     credit_amt = flt(adjusted_amount * total_share / 100, 2)

        #     # Credit entry
        #     self.all_entries.append(
        #         frappe._dict(
        #             account=account,
        #             cost_head=cost_head,
        #             credit=credit_amt,
        #             debit=0,
        #         )
        #     )

        #     # Debit entries to execution heads
        #     distributed = 0
        #     for idx, exec in enumerate(valid_exec_heads):
        #         if idx == len(valid_exec_heads) - 1:
        #             debit_amt = flt(credit_amt - distributed, 2)
        #         else:
        #             debit_amt = flt(credit_amt * flt(exec["share"], 2) / 100, 2)
        #             distributed = flt(distributed + debit_amt, 2)

        #         self.all_entries.append(
        #             frappe._dict(
        #                 account=account,
        #                 cost_head=exec["cost_head"],
        #                 debit=debit_amt,
        #                 credit=0,
        #             )
        #         )
            

    def create_document(self):
        doc = frappe.new_doc("Internal Adjustment")
        doc.adjustment_for = "Expense"
        doc.posting_date = self.posting_date
        doc.type = "Departmental Load"
        doc.internal_adjustment_creator = self.name
        for entry in self.all_entries:
            doc.append("entries", entry)

        doc.insert(ignore_permissions=True)
        doc.submit()
        return doc.name

