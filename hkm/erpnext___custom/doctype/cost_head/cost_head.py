# Copyright (c) 2024, Narahari Dasa and contributors
# For license information, please see license.txt

# import frappe
import frappe
from frappe.utils.nestedset import NestedSet


class CostHead(NestedSet):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF
        from hkm.erpnext___custom.doctype.cost_head_concerned_person.cost_head_concerned_person import CostHeadConcernedPerson
        from hkm.erpnext___custom.doctype.cost_head_expense_approver.cost_head_expense_approver import CostHeadExpenseApprover

        concerned_persons: DF.Table[CostHeadConcernedPerson]
        cost_head_name: DF.Data
        disabled: DF.Check
        expense_approver: DF.Table[CostHeadExpenseApprover]
        freeze: DF.Check
        is_group: DF.Check
        lft: DF.Int
        old_parent: DF.Link | None
        parent_cost_head: DF.Link | None
        rgt: DF.Int
    # end: auto-generated types
    pass


@frappe.whitelist()
def get_children(doctype, parent, is_root=False):

    filters = [["disabled", "=", "0"]]

    if parent and not is_root:
        # via expand child
        filters.append(["parent_cost_head", "=", parent])
    else:
        # v16: Converted ifnull() to OR condition pattern
        filters.append(["parent_cost_head", "in", ["", None]])

    types = frappe.get_list(
        doctype,
        fields=["name as value", "name as title", "is_group as expandable"],
        filters=filters,
        order_by="name",
    )

    return types


@frappe.whitelist()
def add_node():
    from frappe.desk.treeview import make_tree_args

    args = frappe.form_dict
    args = make_tree_args(**args)

    if args.parent_cost_head == "All Cost Heads":
        args.parent_cost_head = None

    frappe.get_doc(args).insert()

