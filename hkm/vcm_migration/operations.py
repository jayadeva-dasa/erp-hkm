from datetime import datetime, date
from io import BytesIO
import json
from warnings import filters

import chardet
import magic
import requests
from erpnext.buying import page
import frappe
from hkm.vcm_migration.connection import ERPConnection


def execute():
    print("test")
    ERPConnection().test()


## Setup Connection
## Mention Site


## Import Print Format
def create_print_formats():
    for p in frappe.get_all("DJ Receipt Format", fields=["*"]):
        del p["creation"]
        del p["modified"]
        p["doctype"] = "DJ Receipt Format"
        ERPConnection().create_doc("DJ Receipt Format", p)


## Import Seva Type Accounts (Normal & CSR)
def create_seva_types():
    seva_types = frappe.get_all("Seva Type", fields=["*"])
    unique_accounts = list(set([s["account"] for s in seva_types]))
    unique_csr_accounts = list(set([s["csr_account"] for s in seva_types]))

    accounts = list(set(unique_accounts + unique_csr_accounts))

    for a in frappe.get_all(
        "Account", filters={"name": ("in", accounts)}, fields=["*"]
    ):
        company_abbr = frappe.get_value("Company", a["company"], "abbr")
        a["parent_account"] = f"Income - {company_abbr}"
        del a["creation"]
        del a["modified"]
        a["doctype"] = "Account"
        a["company"] = a["company"].upper()
        ERPConnection().create_doc("Account", a)

    for s in seva_types:
        company_abbr = frappe.get_value("Company", a["company"], "abbr")
        if not s["account"]:
            s["account"] = f"Temporary Opening - {company_abbr}"
        s["company"] = s["company"].upper()
        s["doctype"] = "Seva Type"
        del s["creation"]
        del s["modified"]
        ERPConnection().create_doc("Seva Type", s)


## Import Seva subtypes
def create_seva_subtypes():
    for s in frappe.get_all("Seva Subtype", fields=["*"]):
        del s["creation"]
        del s["modified"]
        del s["from_date"]
        del s["to_date"]
        s["doctype"] = "Seva Subtype"
        # print(s)
        ERPConnection().create_doc("Seva Subtype", s)


## Import LLP Preachers
def create_preachers():
    for i, p in enumerate(frappe.get_all("LLP Preacher", pluck="name")):
        print(f"P : {i+1}")
        p = frappe.get_doc("LLP Preacher", p).as_dict()
        p["doctype"] = "LLP Preacher"
        ERPConnection().create_doc("LLP Preacher", p)


## Import Donor Creation Request


def create_donor_creation_requests():
    for i, d in enumerate(frappe.get_all("Donor Creation Request", pluck="name")):
        print(f"DCR : {i+1}")
        if i >= 1:
            break
        # if d != "DCR-25-92096":
        #     continue
        d = frappe.get_doc("Donor Creation Request", d).as_dict()
        d["doctype"] = "Donor Creation Request"
        ERPConnection().create_doc("Donor Creation Request", d)


## Import Donors
def create_donors():
    donors = frappe.get_all("Donor", pluck="name")
    length = len(donors)
    for i, d in enumerate(donors):
        if i >= 600:
            break
        print(f"Processing Donor : {i+1} / {length}")
        d = frappe.get_doc("Donor", d).as_dict()
        d["doctype"] = "Donor"
        # d["name"] = f"P{d['name']}"
        ERPConnection().create_doc("Donor", d)
        # ERPConnection().api_create("Donor", d)


## Import Patron Seva Type
def create_patron_seva_types():
    for p in frappe.get_all("Patron Seva Type", pluck="name"):
        p = frappe.get_doc("Patron Seva Type", p).as_dict()
        p["doctype"] = "Patron Seva Type"
        ERPConnection().create_doc("Patron Seva Type", p)


## Import Patrons
def create_patrons():
    for i, p in enumerate(frappe.get_all("Patron", pluck="name")):
        p = frappe.get_doc("Patron", p).as_dict()
        p["doctype"] = "Patron"
        ERPConnection().create_doc("Patron", p)


## Donor & Patron Pujas
def create_patron_pujas():
    for i, p in enumerate(frappe.get_all("Patron Privilege Puja", pluck="name")):
        p = frappe.get_doc("Patron Privilege Puja", p).as_dict()
        p["doctype"] = "Patron Privilege Puja"
        ERPConnection().create_doc("Patron Privilege Puja", p)


## Import Bank Accounts
def create_bank_accounts():
    for i, p in enumerate(
        frappe.get_all("Bank Account", filters={"is_company_account": 1}, pluck="name")
    ):
        p = frappe.get_doc("Bank Account", p).as_dict()
        p["doctype"] = "Bank Account"
        ERPConnection().create_doc("Bank Account", p)


## Import Bank Transactions
def create_bank_transactions():
    for i, p in enumerate(frappe.get_all("Bank Transaction", pluck="name")):
        if i > 200:
            break
        p = frappe.get_doc("Bank Transaction", p).as_dict()
        p["doctype"] = "Bank Transaction"
        ERPConnection().create_doc("Bank Transaction", p)


## Import Attachemnts (Patron)


def create_donation_receipts():
    for i, d in enumerate(
        frappe.get_all(
            "Donation Receipt",
            # filters={
            #     # "company": ["!=", "TOUCHSTONE FOUNDATION VRINDAVAN - NCR"],
            #     # "name": "HKMV-DR2404-0322",
            # },
            pluck="name",
        )
    ):
        print(f"Processing Donation Receipt : {i+1} | {d}")
        d = frappe.get_doc("Donation Receipt", d).as_dict()
        d["doctype"] = "Donation Receipt"
        d["payment_gateway_document"] = None
        d["company"] = d["company"].upper()
        # if d["donor"]:
        #     d["donor"] = f"P{d['donor']}"
        if d["amended_from"]:
            d["amended_from"] = None
        del d["creation"]
        del d["modified"]
        d["receipt_date"] = d["receipt_date"].isoformat()
        ERPConnection().create_doc("Donation Receipt", d)


def create_donation_credits():
    for i, d in enumerate(
        frappe.get_all(
            "Donation Credit",
            filters={
                "company": ["!=", "TOUCHSTONE FOUNDATION VRINDAVAN - NCR"],
            },
            pluck="name",
        )
    ):
        print(f"Processing Donation Credit : {i+1} | {d}")
        d = frappe.get_doc("Donation Credit", d).as_dict()
        d["doctype"] = "Donation Credit"
        d["company"] = d["company"].upper()
        del d["creation"]
        del d["modified"]
        d["posting_date"] = d["posting_date"].isoformat()
        ERPConnection().create_doc("Donation Credit", d)


def create_comments():
    for i, d in enumerate(
        frappe.get_all(
            "Comment",
            pluck="name",
        )
    ):
        if i < 61750:
            continue
        print(f"Processing Comment : {i+1} | {d}")
        d = frappe.get_doc("Comment", d).as_dict()
        d["doctype"] = "Comment"
        d["creation"] = d["creation"].isoformat()
        d["modified"] = d["modified"].isoformat()
        # d["posting_date"] = d["posting_date"].isoformat()
        ERPConnection().create_doc("Comment", d)


def create_attachments():
    for i, p in enumerate(frappe.get_all("File", pluck="name")):
        print(f"Processing File : {i+1} | {p}")
        # if i >= 10:
        #     break
        files = []
        file_doc = frappe.get_doc("File", p)
        try:
            contents = file_doc.dfp_external_storage_download_file()
        except:
            print(f"Couldn't fetch file from Remote")
        file_type = magic.from_buffer(contents, mime=True)
        image_bytes = BytesIO(contents)
        files.append(("file", (file_doc.file_name, image_bytes, file_type)))
        response = requests.post(
            "https://pb.vcmerp.in" + f"/api/method/upload_file",
            headers=frappe._dict(
                Authorization=f"token 86eec78dd2ef82e:143f9867f3e824b"
            ),
            data={
                "name": file_doc.name,
                "is_private": file_doc.is_private,
                "file_name": file_doc.file_name,
                "file_type": file_doc.file_type,
                "folder": file_doc.folder,
                "doctype": file_doc.attached_to_doctype,
                "docname": file_doc.attached_to_name,
                "fieldname": file_doc.attached_to_field,
            },
            files=files,
        )
        try:
            r = json.loads(response.text)
            if "exception" in r:
                print(r["exception"])
        except:
            print(response.text)


def update_receipt_dates():
    receipts = frappe.get_all(
        "Donation Receipt",
        fields=["name", "receipt_date"],
        # page_length=1000,
        # filters={"name": "HKMV-DR2404-0063"},
    )
    receipts_map = {}
    for receipt in receipts:
        receipts_map[receipt.name] = receipt.receipt_date.isoformat()
    response = requests.post(
        "https://pb.vcmerp.in"
        + f"/api/method/vcm.migration.operations.update_receipts",
        headers=frappe._dict(Authorization=f"token 86eec78dd2ef82e:143f9867f3e824b"),
        data=json.dumps(receipts_map),
    )
    print(response.text)


def update_series():
    data = {}
    for s in frappe.db.sql("SELECT * FROM `tabSeries` WHERE name = ''", as_dict=1):
        data[s["name"]] = s["current"]
    response = requests.post(
        "https://pb.vcmerp.in" + f"/api/method/vcm.migration.operations.update_series",
        headers=frappe._dict(Authorization=f"token 86eec78dd2ef82e:143f9867f3e824b"),
        data=json.dumps(data),
    )
    print(response.text)


## Import Donors
def create_donors_2():
    donors = frappe.get_all(
        "Donor",
        pluck="name",
        filters={
            "creation": [">=", "2025-03-30"],
        },
    )
    length = len(donors)
    # print(length)
    for i, d in enumerate(donors):
        # if i >= 10000:
        #     break
        print(f"Processing Donor : {i+1} / {length}")
        d = frappe.get_doc("Donor", d).as_dict()
        d["doctype"] = "Donor"
        d["name"] = f"L{d['name']}"
        ERPConnection().create_doc("Donor", d)
        # ERPConnection().api_create("Donor", d)
