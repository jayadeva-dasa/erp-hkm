import re
from erpnext.accounts.party import get_default_contact
import frappe
from frappe.contacts.doctype.address.address import get_default_address


def on_submit(self, method=None):
    reconcile_bank_transaction_for_entries_from_statement(self)


def reconcile_bank_transaction_for_entries_from_statement(self):
    if not self.get("bank_statement_name"):
        return

    bank_transaction = frappe.get_doc("Bank Transaction", self.bank_statement_name)

    if self.paid_amount > bank_transaction.unallocated_amount:
        frappe.throw(
            frappe._(
                f"Total Paid Amount can not be more than Bank Transaction {bank_transaction.name}'s unallocated amount ({bank_transaction.unallocated_amount})."
            )
        )

    pe = {
        "payment_document": self.doctype,
        "payment_entry": self.name,
        "allocated_amount": self.paid_amount,
    }
    bank_transaction.append("payment_entries", pe)
    bank_transaction.save(ignore_permissions=True)
    frappe.db.set_value(
        "Payment Entry",
        self.name,
        {
            "clearance_date": bank_transaction.date.strftime("%Y-%m-%d"),
            "bank_statement_name": None,
        },
        update_modified=False,
    )
    frappe.db.commit()  # v16: REVIEW - check if needed


@frappe.whitelist()
def get_payment_entry_from_statement(statement):
    bank_transaction = frappe.get_doc("Bank Transaction", statement)
    company_account = frappe.get_value(
        "Bank Account", bank_transaction.bank_account, "account"
    )
    account_currency = frappe.get_value("Account", company_account, "account_currency")

    payment_entry_dict = frappe._dict(
        company=bank_transaction.company,
        payment_type="Receive" if bank_transaction.deposit > 0 else "Pay",
        party_type="Supplier",
        paid_from=company_account,
        paid_amount=bank_transaction.withdrawal,
        received_amount=bank_transaction.withdrawal,
        paid_from_account_currency=account_currency,
        posting_date=bank_transaction.date,
        bank_statement_name=bank_transaction.name,
        reference_no=bank_transaction.description,
        reference_date=bank_transaction.date,
    )

    payment_entry = frappe.new_doc("Payment Entry")
    payment_entry.update(payment_entry_dict)
    return payment_entry


def before_save(self, method=None):
    meta = frappe.get_meta("Payment Entry")
    if not meta.has_field("custom_mobile_number"):
        return
    if self.get("custom_mobile_number"):
        return
    if not self.party_type or not self.party:
        return
    mobile_number = frappe.db.get_value("Supplier", self.party, "mobile_no")
    if not mobile_number:
        address = get_default_address(doctype=self.party_type, name=self.party)
        if address:
            mobile_number = frappe.db.get_value("Address", address, "phone")
    if not mobile_number:
        contact_id = get_default_contact(doctype=self.party_type, name=self.party)
        if contact_id:
            contact_doc = frappe.get_doc("Contact", contact_id)
            if len(contact_doc.phone_nos) > 0:
                mobile_number = contact_doc.phone_nos[0].phone
    if mobile_number:
        match = re.search(r"(\d{10})\D*$", mobile_number)

        # If a match is found, prepend '91'
        if match:
            mobile_number = "91" + match.group(1)
        self.custom_mobile_number = mobile_number
    return
