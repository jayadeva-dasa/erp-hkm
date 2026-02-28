# Copyright (c) 2024, Narahari Dasa and contributors
# For license information, please see license.txt

# import frappe
from erpnext.accounts.doctype import accounting_dimension
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
    get_accounting_dimensions,
)
import frappe
from frappe.model.document import Document
from frappe.utils import flt, fmt_money
from frappe.utils.nestedset import get_descendants_of


class HKMBudget(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        amount: DF.Currency
        cost_center: DF.Link | None
        fiscal_year: DF.Link
        project: DF.Link | None
    # end: auto-generated types
    pass

    def validate(self):
        dim_set = 0
        for dim in ["cost_center", "project"] + get_accounting_dimensions():
            if self.get(dim):
                dim_set += 1
        # if dim_set != 1:
        #     frappe.throw(f"Please select one Dimension. Not Less, Not More.")


# args contians GL Entry Data
def validate_expense_against_budget(args):
    args = frappe._dict(args)

    if not frappe.get_all("HKM Budget", limit=1):
        return

    if not frappe.get_cached_value("HKM Budget", {"fiscal_year": args.fiscal_year}):
        return

    if not args.get("debit") or args.get("is_cancelled"):
        return

    if not frappe.get_value("Account", args.get("account"), "root_type") == "Expense":
        return

    prepare_dimensions(args)
    if args.accounting_dimensions:
        budget_records = get_applicable_budget_records(args)

        if budget_records:
            validate_budget_records(args, budget_records)
    return


def get_applicable_budget_records(args):
    condition = ""
    for dimension in args.accounting_dimensions:
        if dimension.is_tree:
            lft, rgt = frappe.get_cached_value(
                dimension.document_type, args.get(dimension.fieldname), ["lft", "rgt"]
            )
            ## Getting parent budget of a child
            condition += f""" and exists(select name from `tab{dimension.document_type}`
                    where lft<={lft} and rgt>={rgt} and name = budget.{dimension.fieldname})"""
        else:
            condition += f" and budget.{dimension.fieldname}={frappe.db.escape(args.get(dimension.fieldname))}"

    return frappe.db.sql(
        f"""
        SELECT
            name, amount, fiscal_year
        FROM
            `tabHKM Budget` budget
        WHERE
            fiscal_year= '{args.fiscal_year}'
            {condition}
    """,
        as_dict=True,
    )


def prepare_dimensions(args):
    default_dimensions = [
        {
            "fieldname": "project",
            "document_type": "Project",
        },
        {
            "fieldname": "cost_center",
            "document_type": "Cost Center",
        },
    ]

    accounting_dimensions = default_dimensions + get_accounting_dimensions(
        as_list=False
    )

    abbr = frappe.get_cached_value("Company", args.company, "abbr")

    args.accounting_dimensions = []
    for d in accounting_dimensions:
        fieldname = d.get("fieldname")
        if args.get(fieldname):
            if fieldname == "cost_center" and args.get(fieldname) == f"Main - {abbr}":
                continue

            dimension = frappe._dict(
                {
                    "fieldname": fieldname,
                    "document_type": d.get("document_type"),
                    "is_tree": False,
                }
            )
            if frappe.get_cached_value("DocType", d.get("document_type"), "is_tree"):
                dimension.is_tree = True

            args.accounting_dimensions.append(dimension)


def get_dimension_condition(args):

    condition = ""

    for dimension in args.accounting_dimensions:
        fieldname = dimension.get("fieldname")
        print(fieldname)

        if args.get(fieldname):

            if frappe.get_cached_value(
                "DocType", dimension.get("document_type"), "is_tree"
            ):
                lft, rgt = frappe.db.get_value(
                    dimension.get("document_type"), args.get(fieldname), ["lft", "rgt"]
                )
                ## tmi stands for table Main Transaction
                condition += f""" 
                AND EXISTS(
                    SELECT name
                    FROM `tab{dimension.get("document_type")}`
                    WHERE 
                        lft>={lft} 
                        AND rgt<={rgt}
                        AND name= tmi.{fieldname}
                    )"""

            else:
                budget_against_val = args.get(fieldname)
                condition += f""" 
                        AND tmi.{fieldname} = '{budget_against_val}'"""

    return condition


def validate_budget_records(args, budget_records):
    for budget in budget_records:
        if flt(budget.amount):
            args.yr_start_date, args.yr_end_date = frappe.get_cached_value(
                "Fiscal Year", budget.fiscal_year, ["year_start_date", "year_end_date"]
            )
            args.dimension_condition = get_dimension_condition(args)
            unpaid_invoices_amount = get_unpaid_purchase_invoices_amount(args)
            unpaid_and_uninvoiced_po_amt = (
                get_unpaid_and_uninvoiced_purchase_orders_amount(args)
            )
            payment_entries_amount = get_payment_entries_amount(args)

            additional_expenses = get_additional_expenses_amount(args)
            # frappe.errprint(
            #     f"""
            #     additional_expenses : {additional_expenses}
            #     unpaid_invoices_amount : {unpaid_invoices_amount}
            #     unpaid_and_uninvoiced_po_amt : {unpaid_and_uninvoiced_po_amt}
            #     payment_entries_amount : {payment_entries_amount}
            #     """
            # )

            used_value = (
                unpaid_invoices_amount
                + unpaid_and_uninvoiced_po_amt
                + payment_entries_amount
                + additional_expenses
            )
            # frappe.errprint(
            #     f"""
            #     used_value : {used_value}
            #     """
            # )
            # frappe.errprint(f"ARGS : {args}")
            requested_value = args.get("debit")
            # frappe.errprint(
            #     f"""
            #     requested_value : {requested_value}
            #     """
            # )
            if budget.amount <= (used_value + requested_value):
                link = frappe.utils.get_link_to_form("HKM Budget", budget.name)
                frappe.throw(
                    msg=f"""
                        Budget : {link}<br>
                        Allowed : {frappe.bold(fmt_money(budget.amount, currency='₹'))}<br>
                        Used : {frappe.bold(fmt_money(used_value, currency='₹'))}<br>
                        ------------------------<br>
                        Payments Made : {fmt_money(payment_entries_amount, currency='₹')}<br>
                        Unpaid Invoices : {fmt_money(unpaid_invoices_amount, currency='₹')}<br>
                        Unpaid/Uninvoiced POs : {fmt_money(unpaid_and_uninvoiced_po_amt, currency='₹')}<br>
                        Additional Expenses : {fmt_money(additional_expenses, currency='₹')}
                        """,
                    title="Budget Limit Exceeded",
                )
    return


def get_payment_entries_amount(args):
    # frappe.errprint(
    #     f"""
    #     select SUM(paid_amount)
    #     from `tabPayment Entry` tmi
    #     where docstatus=1 {args.dimension_condition}
    # """
    # )
    frappe.errprint(args.dimension_condition)
    frappe.errprint(
        f"""
        select SUM(paid_amount)
        from `tabPayment Entry` tmi
        where docstatus=1 {args.dimension_condition}
    """,
    )
    return flt(
        frappe.db.sql(
            f"""
        select SUM(paid_amount)
        from `tabPayment Entry` tmi
        where docstatus=1 {args.dimension_condition}
    """,
        )[0][0]
    )


def get_unpaid_purchase_invoices_amount(args):
    return flt(
        frappe.db.sql(
            f"""
        SELECT SUM(unpaid_amount)
        FROM (
            SELECT 
                tmi.name,
                (tmi.grand_total - 
                    (IFNULL(SUM(tper.allocated_amount),0) + IFNULL(SUM(tjea.debit),0))  # v16: TODO - Use pypika Field objects for ifnull
                ) as unpaid_amount
            FROM `tabPurchase Invoice` tmi 
            LEFT JOIN `tabPayment Entry Reference` tper
                ON tper.reference_doctype = "Purchase Invoice" AND tper.reference_name = tmi.name
            LEFT JOIN `tabPayment Entry` tpe
                ON tpe.name = tper.parent
            LEFT JOIN `tabJournal Entry Account` tjea
                ON tjea.reference_type = "Purchase Invoice" AND tjea.reference_name = tmi.name
            LEFT JOIN `tabJournal Entry` tje
                ON tje.name = tjea.parent
            WHERE tmi.docstatus  = 1
                AND tmi.is_paid = 0
                AND (tpe.docstatus IS NULL OR tpe.docstatus = 1)
                AND (tje.docstatus IS NULL OR tje.docstatus = 1)
                AND tmi.name != '{args.voucher_no}'
                AND tmi.posting_date BETWEEN '{args.yr_start_date}' AND '{args.yr_end_date}'
                {args.dimension_condition}
            GROUP BY tmi.name) up
    """
        )[0][0]
    )


def get_unpaid_and_uninvoiced_purchase_orders_amount(args):
    return flt(
        frappe.db.sql(
            f"""
        SELECT SUM(unpaid_amount)
        FROM (
            SELECT tmi.name, 
                (   
                    (
                        IFNULL(SUM(tmii.amount), 0)  # v16: TODO - Use pypika Field objects for ifnull
                        + IFNULL(SUM(tmii.igst_amount), 0)  # v16: TODO - Use pypika Field objects for ifnull
                        + IFNULL(SUM(tmii.cgst_amount), 0)  # v16: TODO - Use pypika Field objects for ifnull
                        + IFNULL(SUM(tmii.sgst_amount), 0)      # v16: TODO - Use pypika Field objects for ifnull
                        ) 
                    - (
                        IFNULL(SUM(tper.allocated_amount),0)  # v16: TODO - Use pypika Field objects for ifnull
                        + IFNULL(SUM(tjea.debit),0)  # v16: TODO - Use pypika Field objects for ifnull
                        )
                    - (
                        IFNULL(SUM(tpii.amount),0)  # v16: TODO - Use pypika Field objects for ifnull
                        + IFNULL(SUM(tpii.igst_amount),0)  # v16: TODO - Use pypika Field objects for ifnull
                        + IFNULL(SUM(tpii.cgst_amount),0)  # v16: TODO - Use pypika Field objects for ifnull
                        + IFNULL(SUM(tpii.sgst_amount),0)   # v16: TODO - Use pypika Field objects for ifnull
                        )
                ) as unpaid_amount
            FROM `tabPurchase Order` tmi
            JOIN `tabPurchase Order Item` tmii
                ON tmii.name = tmi.parent
            LEFT JOIN `tabPayment Entry Reference` tper
                ON tper.reference_doctype = "Purchase Order" AND tper.reference_name = tmi.name
            LEFT JOIN `tabPayment Entry` tpe
                ON tpe.name = tper.parent
            LEFT JOIN `tabJournal Entry Account` tjea
                ON tjea.reference_type = "Purchase Order" AND tjea.reference_name = tmi.name
            LEFT JOIN `tabJournal Entry` tje
                ON tje.name = tjea.parent
            LEFT JOIN `tabPurchase Invoice Item` tpii 
                ON tpii.purchase_order = tmi.name
            LEFT JOIN `tabPurchase Invoice` tpi 
                ON tpi.name = tpii.parent 
            WHERE tmi.docstatus  = 1
                AND (tpe.docstatus IS NULL OR tpe.docstatus = 1)
                AND (tje.docstatus IS NULL OR tje.docstatus = 1)
                AND (tpi.docstatus IS NULL OR tpi.docstatus = 1)
                AND tmi.transaction_date BETWEEN '{args.yr_start_date}' AND '{args.yr_end_date}'
                {args.dimension_condition}
            GROUP BY tmi.name
            ) up
        """
        )[0][0]
    )


def get_additional_expenses_amount(args):
    exclude_voucher_types_str = ", ".join(["'%s'" % vt for vt in ["Purchase Invoice"]])
    return flt(
        frappe.db.sql(
            f"""
        SELECT SUM(tmi.debit) - SUM(tmi.credit)
        FROM `tabGL Entry` tmi
        JOIN `tabAccount` ta
            ON tmi.account = ta.name
        WHERE is_cancelled = 0
        AND ta.root_type = 'Expense'
        AND voucher_type NOT IN ({exclude_voucher_types_str})
        AND tmi.fiscal_year  = '{args.fiscal_year}'
        {args.dimension_condition}
    """
        )[0][0]
    )
