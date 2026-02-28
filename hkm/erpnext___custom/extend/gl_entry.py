from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
    get_accounting_dimensions,
)
from hkm.erpnext___custom.doctype.hkm_budget.hkm_budget import (
    validate_expense_against_budget,
)
import frappe
import re
from hkm.utils import is_null_or_blank


def validate(doc, method=None):
    args = doc.as_dict()
    validate_expense_against_budget(args)
    validate_cost_head(args)
    return


def validate_cost_head(args):
    if (
        "cost_head" in args
        and not is_null_or_blank(args.get("cost_head"))
        and  frappe.db.get_value("Cost Head", args.get("cost_head"), "Freeze")
    ):
        frappe.throw("Cost Head is frozen and cannot be used in transactions")
