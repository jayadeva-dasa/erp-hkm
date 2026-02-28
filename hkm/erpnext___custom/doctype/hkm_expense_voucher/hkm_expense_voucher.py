# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt
from erpnext.accounts.utils import (
    get_fiscal_years,
)

from frappe.utils import (
    flt,
    formatdate,
)
from erpnext.accounts.utils import (
    get_account_currency,
)
import erpnext

from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
    get_accounting_dimensions,
)
from erpnext.utilities.regional import temporary_flag

# import frappe
from frappe.model.document import Document
from erpnext.accounts.party import get_party_account
import frappe
from erpnext.accounts.general_ledger import make_gl_entries

from frappe import _


class HKMExpenseVoucher(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        amended_from: DF.Link | None
        amount: DF.Int
        approving_authority: DF.Link | None
        cash_account: DF.Link | None
        category: DF.Link
        company: DF.Link
        cost_center: DF.Link | None
        cost_head: DF.Link
        devotee: DF.Link
        expense_account: DF.Link | None
        internal_supplier: DF.Link | None
        paid_in: DF.Literal["Cash"]
        posting_date: DF.Date | None
        remarks: DF.Data
        vendor: DF.Data | None
        voucher_type: DF.Literal["Personal"]

    # end: auto-generated types
    def before_insert(self):
        self.internal_supplier = frappe.db.get_value(
            "DED Devotee", self.devotee, "default_supplier_account"
        )

        # approving_authority = self.get_approver_authority(
        #     self.cost_head, self.voucher_type
        # )

        # if not approving_authority:
        #     return frappe.throw("No approving authority found for this voucher type")

        approving_authority = "rdpd@hkmjaipur.org"

        if self.voucher_type == "Personal":
            self.approving_authority = approving_authority

        if not self.internal_supplier:
            return frappe.throw("No internal supplier found for this devotee")

        cash_account = frappe.db.get_value(
            "Company", self.company, "default_cash_account"
        )
        if not cash_account:
            return frappe.throw("No cash account found for this company")
        self.cash_account = cash_account

        expense_account = (
            frappe.get_all(
                "HKM Expense Voucher Type Account",
                filters={"parent": self.category, "company": self.company},
                pluck="default_account",
                limit=1,
            )[0]
            or None
        )
        if not expense_account:
            return frappe.throw("No expense account found for this voucher type")
        self.expense_account = expense_account

        self.cost_center = frappe.db.get_value("Company", self.company, "cost_center")

    def get_approver_authority(self, cost_head, voucher_type):
        if voucher_type == "Personal":
            devotee = frappe.db.get_value(
                "DED Devotee",
                filters={"erp_user": frappe.session.user},
                pluck="parent_ded_devotee",
            )
            while devotee:
                parent_approver = frappe.db.get_value(
                    "DED Devotee", devotee, "designation"
                )
                if parent_approver:
                    return frappe.db.get_value("DED Devotee", devotee, "erp_user")

                devotee = frappe.db.get_value(
                    "DED Devotee", devotee, "parent_ded_devotee"
                )
            return None
        else:
            while cost_head:
                approver = frappe.get_all(
                    "Cost Head Expense Approver",
                    filters={"parent": cost_head},
                    pluck="user",
                )
                if approver:
                    return approver
                cost_head = frappe.db.get_value(
                    "Cost Head", cost_head, "parent_cost_head"
                )
            return None

    def on_update(self):
        old_doc = self.get_doc_before_save()
        if not old_doc:
            return
        if old_doc.workflow_state == self.workflow_state:
            return
        if self.workflow_state == "Approved" and self.voucher_type != "Personal":
            self.approving_authority = frappe.session.user
            self.save()

    def validate(self):
        self.validate_amount()
        self.validate_approving_authority()
        self.validate_party_account()
        if self.expense_account:
            self.validate_cash_account()
            self.validate_expense_account()
        self.validate_voucher_type()
        # self.validate_company()

    # def validate_company(self):
    #     if self.company not in frappe.get_all(
    #         "HKM Active Company",
    #         fields=["company"],
    #     ):
    #         return frappe.throw("Company not allowed")

    def validate_voucher_type(self):
        setting_doc = frappe.get_cached_doc("DED Settings")
        personal_expenses_cost_heads = [
            i.cost_head for i in setting_doc.personal_expenses_cost_heads
        ]
        if self.voucher_type == "Personal":
            if not personal_expenses_cost_heads:
                return frappe.throw("No personal expenses cost heads found")
            if self.cost_head not in personal_expenses_cost_heads:
                return frappe.throw("Cost head not allowed for personal voucher type")

            # settings = frappe.get_cached_doc("DED Levels")

            # if self.company != settings.company:
            #     return frappe.throw("Company not allowed for personal voucher type")

        if self.voucher_type == "Departmental":
            if self.cost_head in personal_expenses_cost_heads:
                return frappe.throw(
                    "Cost head not allowed for departmental voucher type"
                )

    def validate_party_account(self):
        if not get_party_account("Supplier", self.internal_supplier, self.company):
            return frappe.throw("No party account found for this supplier")

    def validate_expense_account(self):
        if not self.expense_account:
            return frappe.throw("No expense account found for this voucher type")

        if (
            frappe.db.get_value("Account", self.expense_account, "company")
            != self.company
        ):
            return frappe.throw("Expense account does not belong to this company")

    def validate_cash_account(self):
        if not self.cash_account:
            return frappe.throw("No cash account found for this company")

        if frappe.db.get_value("Account", self.cash_account, "company") != self.company:
            return frappe.throw("Cash account does not belong to this company")

    def validate_approving_authority(self):
        old_doc = self.get_doc_before_save()
        if not old_doc:
            return
        if old_doc.workflow_state == self.workflow_state:
            return
        if self.workflow_state == "Approved":
            roles = frappe.get_roles(frappe.session.user)
            if "HKM Expense Voucher Approver" not in roles:
                frappe.throw("You are not allowed to approve this voucher")

            setting_doc = frappe.get_cached_doc("DED Settings")
            personal_cost_heads = [
                i.cost_head for i in setting_doc.personal_expenses_cost_heads
            ]

            if (
                self.voucher_type == "Personal"
                and self.cost_head in personal_cost_heads
            ):
                if self.approving_authority != frappe.session.user:
                    return frappe.throw("You are not allowed to approve this voucher")
            else:
                approver_allowed = frappe.get_all(
                    "Cost Head Expense Approver",
                    filters={"user": frappe.session.user},
                    pluck="parent",
                )
                cost_head = []
                for approver in approver_allowed:
                    cost_head += frappe.db.get_descendants("Cost Head", approver)
                cost_head += approver_allowed
                cost_head = list(set(cost_head))
                if self.cost_head not in cost_head:
                    frappe.throw("You are not allowed to approve this voucher")
            return

    def validate_amount(self):
        if self.amount <= 0:
            frappe.throw("Amount must be greater than 0")
        if self.amount > 9000:
            frappe.throw("Amount must be less than 9000")

    def on_cancel(self):
        self.ignore_linked_doctypes = ["GL Entry", "Payment Ledger Entry"]
        if frappe.db.exists("GL Entry", {"voucher_no": self.name}):
            make_gl_entries(self.get_gl_entries(), cancel=True)
        self.db_set("workflow_state", "Cancelled")

    def on_submit(self):
        ## if workflow state is released then make gl entries
        if self.workflow_state == "Released":
            entries = self.get_gl_entries()
            make_gl_entries(entries, cancel=False, merge_entries=False)
            if not self.posting_date:
                self.db_set("posting_date", frappe.utils.nowdate())

    def get_gl_entries(self):
        self.company_currency = frappe.get_cached_value(
            "Company", self.company, "default_currency"
        )
        expense_account = self.expense_account

        cash_account = self.cash_account

        creditor_account = get_party_account(
            "Supplier", self.internal_supplier, self.company
        )

        cost_center = self.cost_center

        common_attrs = {
            "posting_date": (
                frappe.utils.nowdate() if not self.posting_date else self.posting_date
            ),
            "cost_head": self.cost_head,
            "cost_center": cost_center,
            "remarks": self.remarks,
        }

        if self.voucher_type == "Personal":
            common_attrs["volunteer_head"] = frappe.db.get_value(
                "HKM Expense Voucher Type", self.category, "volunteer_head"
            )
            common_attrs["volunteer"] = self.devotee

        gl_base_entries = [
            ### expense account Debit Entry ###
            {
                **common_attrs,
                "account": expense_account,
                "against": self.internal_supplier,
                "debit": self.amount,
            },
            ### creditor account Credit Entry ###
            {
                **common_attrs,
                "account": creditor_account,
                "against": expense_account,
                "party_type": "Supplier",
                "party": self.internal_supplier,
                "credit": self.amount,
            },
            ### creditor account Debit Entry ###
            {
                **common_attrs,
                "account": creditor_account,
                "against": cash_account,
                "party_type": "Supplier",
                "party": self.internal_supplier,
                "debit": self.amount,
            },
            ### cash account Credit Entry ###
            {
                **common_attrs,
                "account": cash_account,
                "against": self.internal_supplier,
                "credit": self.amount,
            },
        ]
        gl_entries = []
        for entry in gl_base_entries:
            gl_entries.append(self.get_gl_dict({**entry}, item=self))
        return gl_entries

    def get_gl_dict(self, args, account_currency=None, item=None):
        """this method populates the common properties of a gl entry record"""

        posting_date = args.get("posting_date") or self.get("posting_date")
        fiscal_years = get_fiscal_years(posting_date, company=self.company)
        if len(fiscal_years) > 1:
            frappe.throw(
                _(
                    "Multiple fiscal years exist for the date {0}. Please set company in Fiscal Year"
                ).format(formatdate(posting_date))
            )
        else:
            fiscal_year = fiscal_years[0][0]

        gl_dict = frappe._dict(
            {
                "company": self.company,
                "posting_date": posting_date,
                "fiscal_year": fiscal_year,
                "voucher_type": self.doctype,
                "voucher_no": self.name,
                "remarks": self.get("remarks") or self.get("remark"),
                "debit": 0,
                "credit": 0,
                "debit_in_account_currency": 0,
                "credit_in_account_currency": 0,
                "is_opening": self.get("is_opening") or "No",
                "party_type": None,
                "party": None,
                "project": self.get("project"),
                "post_net_value": args.get("post_net_value"),
                "voucher_detail_no": args.get("voucher_detail_no"),
                "voucher_subtype": self.get_voucher_subtype(),
            }
        )

        with temporary_flag("company", self.company):
            update_gl_dict_with_regional_fields(self, gl_dict)

        accounting_dimensions = get_accounting_dimensions()
        dimension_dict = frappe._dict()

        for dimension in accounting_dimensions:
            dimension_dict[dimension] = self.get(dimension)
            if item and item.get(dimension):
                dimension_dict[dimension] = item.get(dimension)

        gl_dict.update(dimension_dict)
        gl_dict.update(args)

        if not account_currency:
            account_currency = get_account_currency(gl_dict.account)

        self.validate_account_currency(gl_dict.account, account_currency)
        set_balance_in_account_currency(
            gl_dict,
            account_currency,
            self.get("conversion_rate"),
            self.company_currency,
        )

        # Update details in transaction currency
        gl_dict.update(
            {
                "transaction_currency": self.get("currency") or self.company_currency,
                "transaction_exchange_rate": self.get("conversion_rate", 1),
                "debit_in_transaction_currency": self.get_value_in_transaction_currency(
                    account_currency, gl_dict, "debit"
                ),
                "credit_in_transaction_currency": self.get_value_in_transaction_currency(
                    account_currency, gl_dict, "credit"
                ),
            }
        )

        if not args.get("against_voucher_type") and self.get("against_voucher_type"):
            gl_dict.update({"against_voucher_type": self.get("against_voucher_type")})

        if not args.get("against_voucher") and self.get("against_voucher"):
            gl_dict.update({"against_voucher": self.get("against_voucher")})

        return gl_dict

    def get_voucher_subtype(self):
        return self.doctype

    def get_value_in_transaction_currency(self, account_currency, gl_dict, field):
        if account_currency == self.get("currency"):
            return gl_dict.get(field + "_in_account_currency")
        else:
            return flt(gl_dict.get(field, 0) / self.get("conversion_rate", 1))

    def validate_account_currency(self, account, account_currency=None):
        valid_currency = [self.company_currency]
        if self.get("currency") and self.currency != self.company_currency:
            valid_currency.append(self.currency)

        if account_currency not in valid_currency:
            frappe.throw(
                _("Account {0} is invalid. Account Currency must be {1}").format(
                    account, (" " + _("or") + " ").join(valid_currency)
                )
            )


@erpnext.allow_regional
def update_gl_dict_with_regional_fields(doc, gl_dict):
    pass


def set_balance_in_account_currency(
    gl_dict, account_currency=None, conversion_rate=None, company_currency=None
):
    if (not conversion_rate) and (account_currency != company_currency):
        frappe.throw(
            _("Account: {0} with currency: {1} can not be selected").format(
                gl_dict.account, account_currency
            )
        )

    gl_dict["account_currency"] = (
        company_currency if account_currency == company_currency else account_currency
    )

    # set debit/credit in account currency if not provided
    if flt(gl_dict.debit) and not flt(gl_dict.debit_in_account_currency):
        gl_dict.debit_in_account_currency = (
            gl_dict.debit
            if account_currency == company_currency
            else flt(gl_dict.debit / conversion_rate, 2)
        )

    if flt(gl_dict.credit) and not flt(gl_dict.credit_in_account_currency):
        gl_dict.credit_in_account_currency = (
            gl_dict.credit
            if account_currency == company_currency
            else flt(gl_dict.credit / conversion_rate, 2)
        )
