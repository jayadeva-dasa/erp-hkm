from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
    get_accounting_dimensions,
)
from erpnext.controllers.accounts_controller import check_if_child_table_updated
from hkm.erpnext___custom.overrides.buying_validations import validate_buying_dates
import frappe
from frappe import _
from frappe.utils import get_link_to_form


def validate(self, method=None):
    set_expense_account_for_asset_items(self)
    validate_word_order(self)
    validate_buying_dates(self)


def set_expense_account_for_asset_items(self):
    """Set expense_account for fixed asset items from Asset Category (Fixed Asset or CWIP account).
    Ensures asset receipts use Balance Sheet asset accounts, not P&L expense accounts."""
    from erpnext.assets.doctype.asset.asset import is_cwip_accounting_enabled
    from erpnext.assets.doctype.asset_category.asset_category import get_asset_category_account

    for item in self.get("items"):
        if not item.is_fixed_asset:
            continue
        if not item.asset_category:
            item.asset_category = frappe.db.get_value("Item", item.item_code, "asset_category")
        if not item.asset_category:
            frappe.throw(
                _("Row {0}: Asset Category is required for fixed asset item {1}.").format(
                    item.idx, item.item_code
                ),
                title=_("Asset Category Required"),
            )
        account_type = (
            "capital_work_in_progress_account"
            if is_cwip_accounting_enabled(item.asset_category)
            else "fixed_asset_account"
        )
        account = get_asset_category_account(
            account_type, item=item.item_code, company=self.company
        )
        if not account:
            frappe.throw(
                _("Please set Fixed Asset Account in {0} against {1}.").format(
                    get_link_to_form("Asset Category", item.asset_category), self.company
                ),
                title=_("Missing Account"),
            )
        item.expense_account = account


def on_update_after_submit(self, method=None):
    fields_to_check = []
    child_tables = {"items": ("expense_account",), "taxes": ("account_head",)}
    self.needs_repost = self.check_if_fields_updated(fields_to_check, child_tables)
    if self.needs_repost:
        self.repost_accounting_entries()
    return


def check_if_fields_updated(self, fields_to_check, child_tables):
    # Check if any field affecting accounting entry is altered
    doc_before_update = self.get_doc_before_save()
    accounting_dimensions = [*get_accounting_dimensions(), "cost_center", "project"]

    # Parent Level Accounts excluding party account
    fields_to_check += accounting_dimensions
    for field in fields_to_check:
        if doc_before_update.get(field) != self.get(field):
            return True

    # Check for child tables
    for table in child_tables:
        if check_if_child_table_updated(
            doc_before_update.get(table), self.get(table), child_tables[table]
        ):
            return True

    return False


@frappe.whitelist()
def repost_accounting_entries(self):
    repost_ledger = frappe.new_doc("Repost Accounting Ledger")
    repost_ledger.company = self.company
    repost_ledger.append(
        "vouchers", {"voucher_type": self.doctype, "voucher_no": self.name}
    )
    repost_ledger.flags.ignore_permissions = True
    repost_ledger.insert()
    repost_ledger.submit()
    return


def validate_word_order(self):
    linked_purchase_orders = [d.purchase_order for d in self.get("items")]
    linked_purchase_orders = list(set(linked_purchase_orders))
    for po in linked_purchase_orders:
        work_order = frappe.db.get_value("Purchase Order", po, "for_a_work_order")
        if work_order == 1:
            frappe.throw(
                _("Work Order {0} isn't allowed to have a Purchase Receipt.").format(
                    frappe.bold(po),
                ),
                title=_("Not Allowed"),
            )
    return