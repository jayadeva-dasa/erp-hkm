from frappe import _
import frappe
from erpnext.accounts.report.supplier_ledger_summary.supplier_ledger_summary import (
    execute as supplier_ledger_summary_execute,
)


def execute(filters=None):
    columns, data, *args = supplier_ledger_summary_execute(filters)
    columns = get_columns(columns)
    data = get_data(data)
    return columns, data, *args


def get_columns(columns):
    if columns:
        columns[1:1] = [
            # {
            #     "fieldname": "bank",
            #     "label": "Bank",
            #     "fieldtype": "Data",
            #     "width": 150,
            # },
            {
                "fieldname": "beneficiary_name",
                "label": "Beneficiary Name",
                "fieldtype": "Data",
                "width": 150,
            },
            {
                "fieldname": "bank_account_number",
                "label": "Bank Account Number",
                "fieldtype": "HTML",
                "width": 150,
            },
            {
                "fieldname": "branch_code",
                "label": "Branch Code",
                "fieldtype": "Data",
                "width": 150,
            },
        ]
    return columns


def get_data(data):
    if not data:
        return data
    supplier_names = list(set(row.get("party") for row in data if row.get("party")))

    if not supplier_names:
        return data

    placeholders = ",".join(["%s"] * len(supplier_names))
    bank_accounts = frappe.db.sql(
        f"""
            SELECT 
                party,
                name,
                account_name,
                bank,
                branch_code,
                bank_account_no,
                is_default
            FROM `tabBank Account`
            WHERE party_type = 'Supplier'
                AND party IN ({placeholders})
                AND disabled = 0
            ORDER BY is_default DESC, modified DESC
        """,
        tuple(supplier_names),
        as_dict=True,
    )

    supplier_dict = {}
    for ba in bank_accounts:
        supplier = ba.get("party")
        if supplier and supplier not in supplier_dict:
            bank_account_link = frappe.utils.get_url_to_form(
                "Bank Account", ba.get("name")
            )
            supplier_dict[supplier] = {
                "bank": ba.get("bank"),
                "beneficiary_name": ba.get("account_name"),
                "bank_account_number": f"""<a href="{bank_account_link}" target="_blank">{ba.get("bank_account_no")}</a>""",
                "branch_code": ba.get("branch_code"),
            }
        

    for row in data:
        party = row.get("party")
        if party in supplier_dict:
            row.update(supplier_dict[party])

    return data
