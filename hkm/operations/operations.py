from dataclasses import field
from io import StringIO
import io
import json
import re
import time
from urllib.request import Request, urlopen
from warnings import filters

import requests
from sqlalchemy import false

# from dhananjaya.dhananjaya.api.v3.marketing.identify import identify_donor
from dhananjaya.dhananjaya.utils import get_best_contact_address
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
    get_doctypes_with_dimensions,
    make_dimension_in_accounting_doctypes,
)
from erpnext.accounts.doctype.process_payment_reconciliation.process_payment_reconciliation import (
    fetch_and_allocate,
    get_next_allocation,
    reconcile,
)
from erpnext.accounts.utils import get_balance_on
import frappe
from datetime import datetime
from frappe import cstr, enqueue
from frappe.core.page.permission_manager.permission_manager import reset
from frappe.model import document
from frappe.utils.data import flt, nowdate
from frappe.utils.nestedset import NestedSetChildExistsError, get_descendants_of
from frappe.utils import add_to_date, now
from frappe.desk.page.setup_wizard.setup_wizard import make_records
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
import calendar, time
from pypdf import PdfReader

import pandas as pd
import frappe


def set_account_type_for_donation_accounts():
    for a in list(set(frappe.get_all("Seva Type", pluck="account"))):
        if a is None:
            continue
        doc = frappe.get_doc("Account", a)
        doc.account_type = None
        doc.save()


def create_accounting_dimension_fields():
    doctypes = frappe.get_hooks(
        "accounting_dimension_doctypes",
        app_name="hkm",
    )

    dimensions = frappe.get_all("Accounting Dimension", pluck="name")
    for dimension in dimensions:
        doc = frappe.get_doc("Accounting Dimension", dimension)
        make_dimension_in_accounting_doctypes(doc, doctypes)


def submit_assets():
    a = 1
    for i in frappe.get_all("Asset Category", pluck="name"):
        asset_cat = frappe.get_doc("Asset Category", i)
        for j in frappe.get_all(
            "Asset",
            filters={
                "docstatus": 0,
                "purchase_date": ["between", ["2024-01-01", "2024-12-31"]],
                "asset_category": asset_cat.name,
            },
            pluck="name",
        ):
            document = frappe.get_doc("Asset", j)

            document.cost_head = "Main"
            document.calculate_depreciation = 1
            document.available_for_use_date = document.purchase_date
            dep_details = [
                frappe._dict(
                    finance_book=i.finance_book,
                    total_number_of_depreciations=i.total_number_of_depreciations,
                    frequency_of_depreciation=i.frequency_of_depreciation,
                    rate_of_depreciation=i.rate_of_depreciation,
                    depreciation_method=i.depreciation_method,
                    depreciation_start_date=get_last_dates_of_month(
                        document.purchase_date
                    ),
                )
                for i in asset_cat.finance_books
                if i.depreciation_method
            ]

            document.finance_books = []

            document.append("finance_books", dep_details[0])

            print(document.name, document.finance_books[0])
            try:
                document.submit()
            except Exception as e:
                print(e)


def get_last_dates_of_month(date_obj):
    if isinstance(date_obj, datetime):
        date_obj = date_obj.date()

    last_day = calendar.monthrange(date_obj.year, date_obj.month)[1]
    return date_obj.replace(day=last_day)


def check_unattached_purchase_invoice():
    headers = ["Name", "Status", "Company"]
    df = pd.DataFrame(columns=headers)
    query = frappe.db.sql(
        """
    SELECT 
        name, status , company
    FROM 
        `tabPurchase Invoice`
    WHERE 
        posting_date BETWEEN '2024-09-01' AND '2025-01-03'
        AND status != 'Cancelled'
        AND name NOT IN (
            SELECT 
                pi.name 
            FROM 
                `tabPurchase Invoice` pi
            LEFT JOIN 
                `tabFile` f 
            ON 
                pi.name = f.attached_to_name
            WHERE
                pi.status != 'Cancelled'
                AND pi.posting_date BETWEEN '2024-09-01' AND '2025-01-03'
                AND f.attached_to_name IS NOT NULL
        );
    """
    )

    for row in query:
        df.loc[len(df)] = row
    df.to_excel("unattached_doc.xlsx", index=false)


def check_unattached_journal_cash_entries():
    headers = ["Name", "Company"]
    df = pd.DataFrame(columns=headers)
    query = frappe.db.sql(
        """
    SELECT 
        name, company
    FROM 
        `tabJournal Entry`
    WHERE posting_date BETWEEN '2024-09-01' AND '2025-01-03'
        AND voucher_type = 'Cash Entry'
        AND docstatus = 1
        AND name NOT IN (
            SELECT 
                ji.name 
            FROM 
                `tabJournal Entry` ji
            LEFT JOIN 
                `tabFile` f 
            ON 
                ji.name = f.attached_to_name
            WHERE ji.docstatus = 1
                AND ji.voucher_type = 'Cash Entry'
                AND ji.posting_date BETWEEN '2024-09-01' AND '2025-01-03'
                AND f.attached_to_name IS NOT NULL
        );
    """
    )

    for row in query:
        df.loc[len(df)] = row
    df.to_excel("unattached_doc.xlsx", index=false)


def retrieve_cancelled_po():
    headers = [
        "Transaction Date",
        "PO Number",
        "Company",
        "Department",
        "Supplier",
        "Grand Total",
    ]
    df = pd.DataFrame(columns=headers)
    query = frappe.db.sql(
        """
    SELECT
        transaction_date,
        name,
        company,
        department,
        supplier,
        grand_total
    FROM 
        `tabPurchase Order`
    WHERE 
        docstatus = 2
        AND modified BETWEEN '2024-12-24' AND '2025-01-06'
        AND modified_by = 'Administrator'
    """
    )
    for row in query:
        df.loc[len(df)] = row
    df.to_excel("cancelled_po.xlsx", index=False)


# def revamp_seva_subtype_defaults():
#     for doc in frappe.db.sql(
#         """
#         SELECT *
#         FROM `tabSeva Subtype Cost Center`
#         WHERE 1
#     """,
#         as_dict=1,
#     ):
#         dict_d = doc
#         dict_d["doctype"] = "Seva Subtype Defaults"
#         del dict_d["name"]
#         frappe.get_doc(dict_d).save()


def update_cost_center():
    frappe.db.sql(
        f"""
        UPDATE 
            `tabPurchase Invoice Item` pii
        JOIN 
            `tabPurchase Invoice` pi
        ON 
            pi.name = pii.parent
        SET 
            pii.cost_center = pi.cost_center
        WHERE 
            pi.docstatus = 1
            AND pii.cost_center != pi.cost_center
            AND pi.owner = 'accounts2@hkmjaipur.org'
            AND pi.posting_date BETWEEN '2024-11-01' AND '2024-12-13';
            """
    )
    frappe.db.commit()  # v16: OK - operations script
    return


def hsn_code():
    frappe.db.sql(
        f"""
        UPDATE 
        `tabSales Invoice Item` AS tsit
        JOIN `tabItem` AS ti
            ON ti.name = tsit.item_code
        JOIN `tabSales Invoice` AS tsi
            ON tsi.name = tsit.parent
        SET tsit.gst_hsn_code = ti.gst_hsn_code
        WHERE tsi.posting_date BETWEEN '2024-04-01' AND '2025-1-11'
        AND (
            tsit.gst_hsn_code IS NULL 
            OR tsit.gst_hsn_code != ti.gst_hsn_code
        )
        """
    )
    frappe.db.commit()  # v16: OK - operations script
    return


def test():
    pass


def make_sadhana_report():
    headers = [
        "Initial Name",
        "Full Name",
        "Total Students",
        "Mobile Number Filled %",
        "Email %",
        "Photo %",
        "Address %",
        "Address Linked Google Map %",
        "Ashraya Level %",
        "About %",
    ]
    df = pd.DataFrame(columns=headers)
    data_rows = []
    preachers = frappe.get_all("Nexus Preacher", pluck="name")
    for preacher in preachers:
        initital_name = preacher
        full_name = frappe.db.get_value("Nexus Preacher", preacher, "full_name")
        sadhaks = frappe.get_all(
            "Nexus Sadhak", filters={"preacher": preacher}, pluck="name"
        )
        total_students = len(sadhaks)
        mobile_number_filled = 0
        email_filled = 0
        photo_filled = 0
        address_filled = 0
        address_linked_google_map = 0
        about_filled = 0
        ashraya_level_filled = 0
        for sadhak in sadhaks:
            sadhak_doc = frappe.get_doc("Nexus Sadhak", sadhak).as_dict()
            if sadhak_doc.profile_image:
                photo_filled += 1
            if len(sadhak_doc.contacts) > 0:
                mobile_number_filled += 1
            if len(sadhak_doc.emails) > 0:
                email_filled += 1
            if len(sadhak_doc.addresses) > 0:
                address_filled += 1
                for address in sadhak_doc.addresses:
                    if address.longitude and address.latitude:
                        address_linked_google_map += 1
                        break
            if sadhak_doc.spiritual_level:
                ashraya_level_filled += 1
            if sadhak_doc.about:
                about_filled += 1
        if total_students > 0:
            mobile_number_filled = (
                f"{(mobile_number_filled / total_students) * 100:.2f} %"
            )
            email_filled = f"{(email_filled / total_students) * 100:.2f} %"
            photo_filled = f"{(photo_filled / total_students) * 100:.2f} %"
            address_filled = f"{(address_filled / total_students) * 100:.2f} %"
            address_linked_google_map = (
                f"{(address_linked_google_map / total_students) * 100:.2f} %"
            )
            about_filled = f"{(about_filled / total_students) * 100:.2f} %"
            ashraya_level_filled = (
                f"{(ashraya_level_filled / total_students) * 100:.2f} %"
            )
        data_rows.append(
            [
                initital_name,
                full_name,
                total_students,
                mobile_number_filled,
                email_filled,
                photo_filled,
                address_filled,
                address_linked_google_map,
                ashraya_level_filled,
                about_filled,
            ]
        )
    for row in data_rows:
        df.loc[len(df)] = row
    df.to_excel("sadhak_report.xlsx", index=False)


def get_scanner_count():
    site_name = cstr(frappe.local.site)
    files = frappe.get_all(
        "File",
        filters={
            "owner": "scanner@hkmjerp.in",
            "creation": ("between", ["2024-12-01", "2024-12-07"]),
        },
        fields=["name", "file_name", "file_type", "file_url"],
    )
    total_pages = 0
    for f in files:
        if f["file_type"] == "PDF":
            url = "https://" + site_name + f["file_url"]
            response = requests.get(url=url, timeout=120)
            on_fly_mem_obj = io.BytesIO(response.content)
            pdf_file = PdfReader(on_fly_mem_obj)
            pages = len(pdf_file.pages)
        else:
            pages = 1
        total_pages += pages
        print(f" File : {f['file_name']} | Pages : {pages}")

    print(f"Total Pages : {total_pages}")


def create_supplier_otv():
    link = frappe.utils.get_url_to_form("HKM General Settings", "HKM General Settings")
    fields = {
        "Supplier": [
            dict(
                fieldname="is_one_time_vendor",
                label="Is One Time Vendor",
                fieldtype="Check",
                description=f"For setting related to One Time Vendor : <a href='{link}'>Settings</a>",
                insert_after="is_transporter",
            )
        ]
    }
    create_custom_fields(fields, update=True)


# def create_asset_field():
#     fields = {
#         "Asset": [
#             dict(
#                 fieldname="donation_receipt",
#                 label="Donation Receipt",
#                 fieldtype="Link",
#                 options="Donation Receipt",
#                 insert_after="location",
#             )
#         ]
#     }
#     create_custom_fields(fields, update=True)
#     frappe.db.commit()

#     frappe.db.sql(
#         """
#         UPDATE `tabAsset`
#         SET donation_receipt = custom_donation_receipt
#         WHERE 1
#     """
#     )
#     frappe.db.commit()

#     for field in frappe.get_all(
#         "Custom Field", filters={"dt": "Asset", "fieldname": "custom_donation_receipt"}
#     ):
#         frappe.delete_doc("Custom Field", field.name)


# def reset_perms():
#     reset("Donation Receipt")
#     reset("Donor")
#     reset("Patron")

# def set_icr():
#     frappe.db.sql(
#         """
#         UPDATE `tabItem Creation Request`
#         SET status = 'Created'
#         WHERE workflow_state ='Created'
#                 """
#     )
#     frappe.db.sql(
#         """
#         UPDATE `tabItem Creation Request`
#         SET status = 'Rejected'
#         WHERE workflow_state ='Rejected'
#                 """
#     )
#     frappe.db.commit()


# def set_scr():
#     frappe.db.sql(
#         """
#         UPDATE `tabSupplier Creation Request`
#         SET status = 'Created'
#         WHERE workflow_state ='Created'
#                 """
#     )
#     frappe.db.sql(
#         """
#         UPDATE `tabSupplier Creation Request`
#         SET status = 'Rejected'
#         WHERE workflow_state ='Rejected'
#                 """
#     )
#     frappe.db.commit()


def set_it_user():
    pass
    # for v in frappe.get_all(
    #     "Version",
    #     filters={"ref_doctype": "IT Device", "creation": ["<=", "2024-06-01"]},
    #     fields=["name", "data", "docname"],
    # ):
    #     data = json.loads(v["data"])
    #     if "changed" in data:
    #         for ch in data["changed"]:
    #             if ch[0] == "it_user":
    #                 print(v["docname"])
    #                 print(ch)
    #                 # frappe.db.set_value("IT Device",v["docname"],"it_user",ch[2])
    # frappe.db.commit()


def set_brs():
    for je in frappe.db.sql(
        """
                SELECT tje.name as number, tje.reversal_of
                FROM `tabJournal Entry` tje
                JOIN `tabJournal Entry Account` tjea
                    ON tjea.parent = tje.name
                WHERE tjea.account = '1781220613087427 - AU Small; Finance Bank Ltd. - HKMJ'
                    AND tje.posting_date <= '2022-05-01'
                    AND tje.reversal_of IS NOT NULL
                    AND tje.clearance_date IS NULL
                """,
        as_dict=1,
    ):
        reversal_doc = frappe.get_doc("Journal Entry", je["number"])
        original_doc = frappe.get_doc("Journal Entry", je["reversal_of"])
        if (not (original_doc.clearance_date)) and (not (reversal_doc.clearance_date)):
            frappe.db.set_value(
                "Journal Entry",
                original_doc.name,
                "clearance_date",
                original_doc.posting_date,
            )
            frappe.db.set_value(
                "Journal Entry",
                reversal_doc.name,
                "clearance_date",
                original_doc.posting_date,
            )
        frappe.db.commit()  # v16: OK - operations script


def set_brs2():
    for je in frappe.db.sql(
        """
                SELECT tje.name as number, tje.cheque_no, tje.cheque_date, tje.total_debit
                FROM `tabJournal Entry` tje
                JOIN `tabJournal Entry Account` tjea
                    ON tjea.parent = tje.name
                WHERE tjea.account = '1781220613087427 - AU Small; Finance Bank Ltd. - HKMJ'
                    AND tje.posting_date <= '2022-05-01'
                    AND tje.clearance_date IS NULL
                    AND tje.docstatus = 1
                """,
        as_dict=1,
    ):
        reversal_doc = frappe.get_doc("Journal Entry", je["number"])
        original_docs = frappe.get_all(
            "Journal Entry",
            filters={
                "clearance_date": ["is", "not set"],
                "cheque_no": je["cheque_no"],
                "cheque_date": je["cheque_date"],
                "total_debit": je["total_debit"],
                "name": ["!=", je["number"]],
                "docstatus": 1,
            },
            pluck="name",
        )
        if len(original_docs) == 1:
            print(f"Matched  : {reversal_doc.name} with {original_docs[0]}")
        # if (not (original_doc.clearance_date)) and (not (reversal_doc.clearance_date)):
        #     frappe.db.set_value("Journal Entry",original_doc.name,"clearance_date",original_doc.posting_date)
        #     frappe.db.set_value("Journal Entry",reversal_doc.name,"clearance_date",original_doc.posting_date)
        # frappe.db.commit()


def operation_against_account():

    jes = frappe.get_all(
        "Journal Entry",
        filters={"donation_receipt": ["is", "set"]},
        pluck="name",
        # page_length=5,
    )
    length = len(jes)
    for idx, je in enumerate(jes):
        print(f"Processing {idx+1}/{length}")
        set_against_account(je)


def set_against_account(docname):
    doc = frappe.get_doc("Journal Entry", docname)

    accounts_debited, accounts_credited = [], []

    for d in doc.get("accounts"):
        if flt(d.debit) > 0:
            accounts_debited.append(d.party or d.account)
        if flt(d.credit) > 0:
            accounts_credited.append(d.party or d.account)

    accounts_map = {}

    for d in doc.get("accounts"):
        if d.against_account:
            return
        if flt(d.debit) > 0:
            against_account = ", ".join(list(set(accounts_credited)))
        if flt(d.credit) > 0:
            against_account = ", ".join(list(set(accounts_debited)))

        if d.account in accounts_map:
            frappe.throw(f"The Account {d.account} might be duplicate in {docname}")

        accounts_map.setdefault(d.account, against_account)
        frappe.db.set_value(
            "Journal Entry Account",
            d.name,
            "against_account",
            against_account,
            # update_modified=False,
        )

    for gl in frappe.get_all(
        "GL Entry",
        filters={"voucher_no": docname, "voucher_type": "Journal Entry"},
        fields=["name", "account", "credit", "debit"],
    ):
        frappe.db.set_value(
            "GL Entry",
            gl["name"],
            {"against": accounts_map[gl["account"]]},
            # update_modified=False,
        )

    frappe.db.commit()  # v16: OK - operations script


def clean_account():
    for a in frappe.get_all("Account", pluck="name", filters={"is_group": 0}):
        balance = get_balance_on(account=a, date=nowdate())
        if balance == 0:
            try:
                frappe.delete_doc("Account", a)
            except Exception as e:
                print(f"{a} : {e}")

    for a in frappe.get_all("Account", pluck="name", filters={"is_group": 1}):
        desc = get_descendants_of("Account", a)
        if len(desc) == 0:
            try:
                frappe.delete_doc("Account", a)
            except Exception as e:
                print(f"GROUP => {a} : {e}")
    frappe.db.commit()  # v16: OK - operations script


def update_ka_head():
    doctypes = [
        "Purchase Invoice",
        "Purchase Invoice Item",
        "Journal Entry Account",
        "Payment Entry",
        "Payment Ledger Entry",
        "GL Entry",
        "Stock Entry",
    ]

    for doctype in doctypes:
        print(f"Processing  {doctype}")
        for d in frappe.get_all(
            doctype,
            fields=["name", "ka_head"],
            filters={
                "cost_center": "Jaipur - Shri Annapurna Rasoi - TSFJ",
                "ka_head": ["is", "set"],
            },
            # limit=3,
        ):
            frappe.db.set_value(
                doctype,
                d["name"],
                {
                    "cost_center": "KA - Shri Annapurna Rasoi - TSFJ",
                    "ka_head": d["ka_head"],
                },
                update_modified=false,
            )
        frappe.db.commit()  # v16: OK - operations script


def shift_user_company_persmission():
    for p in frappe.get_all("User Company Allowed", fields=["name", "company", "user"]):
        if not frappe.db.exists(
            {
                "doctype": "User Permission",
                "user": p["user"],
                "allow": "Company",
                "for_value": p["company"],
            }
        ):
            frappe.get_doc(
                {
                    "doctype": "User Permission",
                    "user": p["user"],
                    "allow": "Company",
                    "for_value": p["company"],
                }
            ).insert()
        # frappe.db.commit()


def delete_tasks_workflow():
    i = 1
    for f in frappe.get_all("Task", pluck="name"):
        i += 1
        print(f"WF : {i}")
        frappe.delete_doc("Task", f)
    frappe.db.commit()  # v16: OK - operations script


def create_devotee_dimension():
    for p in frappe.get_all("LLP Preacher", pluck="name"):
        if not frappe.db.exists("Devotee", p):
            frappe.get_doc({"doctype": "Devotee", "name1": p}).insert()


def bring_back():
    doctypes = [
        "Dhananjaya Settings",
        "Firebase Admin App",
        "Navbar Settings",
        "Domain Settings",
        "Website Settings",
        "Letter Head",
    ]
    for d in doctypes:
        for f in frappe.get_all(
            "File",
            pluck="name",
            filters={"attached_to_doctype": d, "dfp_external_storage": ["is", "set"]},
        ):
            doc = frappe.get_doc("File", f)
            doc.dfp_external_storage = None
            try:
                doc.save()
                frappe.db.commit()  # v16: OK - operations script
            except Exception as e:
                print(e)
                continue


def set_missing_files():
    for f in frappe.get_all(
        "File",
        filters={
            "file_size": 0,
            "dfp_external_storage": ["is", "not set"],
            "is_folder": 0,
        },
        fields=["name", "file_url", "file_name"],
        # limit=50,
    ):
        print(f"Processing {f['name']}")
        if "http" not in f["file_url"]:
            print(f"Redesingning {f['name']}")
            try:
                similar_file = frappe.get_doc("File", {"file_name": f["file_name"]})
                frappe.db.set_value(
                    "File", f["name"], "file_url", similar_file.file_url
                )
                frappe.db.commit()  # v16: OK - operations script
            except Exception as e:
                print(f"""File : {f["name"]} Not Found""")
                continue


def files_migrate1():
    index = 0
    for f in frappe.get_all(
        "File",
        pluck="name",
        limit=200,
        filters={
            "dfp_external_storage": ["is", "not set"],
            "attached_to_doctype": ["!=", "Prepared Report"],
        },
    ):
        index += 1
        print(f"Processing {index}")
        doc = frappe.get_doc("File", f)
        doc.dfp_external_storage = "DFP.ES.hkmjaipur.240628.271012"
        try:
            doc.save()
            frappe.db.commit()  # v16: OK - operations script
        except OSError as e:
            print(e)


def files_migrate():
    index = 0
    for f in frappe.get_all(
        "File",
        pluck="name",
        filters={
            "dfp_external_storage": ["is", "not set"],
            "attached_to_doctype": [
                "not in",
                ["Prepared Report", "Repost Item Valuation", "Data Import"],
            ],
            "file_size": ["!=", 0],
        },
        # limit=10000,
    ):
        index += 1
        print(f"Processing {index} : {f}")
        doc = frappe.get_doc("File", f)
        doc.dfp_external_storage = "DFP.ES.hkmjaipur.240628.271012"
        try:
            doc.save()
            frappe.db.commit()  # v16: OK - operations script
        except OSError as e:
            print(e)
        except frappe.exceptions.CharacterLengthExceededError as e:
            print(e)
        except frappe.exceptions.LinkValidationError as e:
            print(e)
        except frappe.exceptions.ValidationError as e:
            print(e)
        except Exception as e:
            print(f"file Number : {f}")
            raise e


def repost():
    errros = []
    index = 0
    for j in frappe.get_all(
        "Journal Entry", filters={"docstatus": 1, "repost_required": 1}
    ):
        index += 1
        print(f"Reposting {index}: {j}")
        doc = frappe.get_doc("Journal Entry", j)
        try:
            doc.repost_accounting_entries()
        except Exception as e:
            errros.append(e)
        frappe.db.commit()  # v16: OK - operations script
    print(errros)


def set_direct_cost_centers():
    for je in frappe.db.sql(
        f"""
               SELECT
                    tje.name,
                    JSON_ARRAYAGG(
                                        JSON_OBJECT(
                                            'jea_name', tjea.name,
                                            'new_cost_center', tpi.cost_center,
                                            'pi_name', tpi.name
                                        )
                                    ) AS data
                FROM
                    `tabJournal Entry` tje
                JOIN `tabJournal Entry Account` tjea ON
                    tjea.parent = tje.name
                JOIN `tabPurchase Invoice` tpi 
                                                    ON
                    tjea.reference_name = tpi.name
                WHERE
                    tpi.company = 'Touchstone Foundation Jaipur'
                    AND tpi.cost_center IS NOT NULL
                    AND tpi.cost_center != ""
                    AND tjea.cost_center != tpi.cost_center
                    AND tje.docstatus = 1
                GROUP BY
                    tje.name
                LIMIT 100
                    """,
        as_dict=1,
    ):
        print(f"Processing {je['name']}")
        json_data = json.loads(je["data"])
        account_map = {}
        for d in json_data:
            account_map.setdefault(d["jea_name"], d["new_cost_center"])

        for d in json_data:
            frappe.db.set_value(
                "Journal Entry Account",
                d["jea_name"],
                "cost_center",
                account_map[d["jea_name"]],
            )
        for d in json_data:
            frappe.db.set_value(
                "Journal Entry Account",
                d["jea_name"],
                "cost_center",
                account_map[d["jea_name"]],
            )


def set_cost_centers():
    jes = frappe.db.sql(
        f"""
               SELECT
                    tje.name,
                    JSON_ARRAYAGG(
                                        JSON_OBJECT(
                                            'jea_name', tjea.name,
                                            'new_cost_center', tpi.cost_center,
                                            'account', tjea.account
                                        )
                                    ) AS data
                FROM
                    `tabJournal Entry` tje
                JOIN `tabJournal Entry Account` tjea ON
                    tjea.parent = tje.name
                JOIN `tabPurchase Invoice` tpi 
                                                    ON
                    tjea.reference_name = tpi.name
                JOIN `tabSupplier` ts
                    ON ts.name = tpi.supplier
                WHERE
                    tpi.company = 'Touchstone Foundation Jaipur'
                    AND tpi.cost_center IS NOT NULL
                    AND tpi.cost_center != ""
                    AND tjea.cost_center != tpi.cost_center
                    AND tje.docstatus = 1
                    AND ts.disabled = 0
                GROUP BY
                    tje.name
                    """,
        as_dict=1,
    )
    length = len(jes)
    errors = []
    for index, je in enumerate(jes):
        print(f"Processing {index+1}/{length} : {je['name']}")
        json_data = json.loads(je["data"])
        account_map = {}
        for d in json_data:
            account_map.setdefault(d["jea_name"], d["new_cost_center"])
        je_doc = frappe.get_doc("Journal Entry", je["name"])
        for a in je_doc.accounts:
            if a.name in account_map:
                a.cost_center = account_map[a.name]
        try:
            je_doc.save()
            je_doc.repost_accounting_entries()
            frappe.db.commit()  # v16: OK - operations script
        except Exception as e:
            errors.append(e)
            continue
            # print(str(e))
            # if "Cannot create accounting entries against disabled accounts" in str(e):
            #     account_name = str(e).split(": ")[-1]
            #     frappe.db.set_value("Account", account_name, "disabled", "0")
            #     frappe.db.commit()
            #     je_doc.save()
            # else:
            #     raise e
    print(errors)


def divide_list(lst, n):
    """Divide the list `lst` into sublists of size `n`."""
    return [lst[i : i + n] for i in range(0, len(lst), n)]


def reconcile_payments():
    from erpnext.accounts.doctype.process_payment_reconciliation.process_payment_reconciliation import (
        trigger_job_for_doc,
    )

    entries = frappe.get_all(
        "Process Payment Reconciliation",
        fields=["name", "party"],
        filters={"status": "Queued"},
    )
    for e in entries:
        print(f"Processing : {e['party']}")
        reconcile_based_on_filters(e["name"])
        # count = frappe.db.count(
        #     "Purchase Invoice", filters={"status": "Overdue", "supplier": e["party"]}
        # )
        # frappe.db.commit()
        # print(count)
        # time.sleep(10 * count)


def reconcile_based_on_filters(doc: None | str = None) -> None:
    """
    Identify current state of document and execute next tasks in background
    """
    if doc:
        log = frappe.db.get_value(
            "Process Payment Reconciliation Log", filters={"process_pr": doc}
        )
        if not log:
            log = frappe.new_doc("Process Payment Reconciliation Log")
            log.process_pr = doc
            log.status = "Running"
            log = log.save()

            fetch_and_allocate(doc=doc)
        else:
            res = frappe.get_all(
                "Process Payment Reconciliation Log",
                filters={"name": log},
                fields=["allocated", "reconciled"],
                as_list=1,
            )
            allocated, reconciled = res[0]

            if not allocated:
                fetch_and_allocate(doc=doc)
            elif not reconciled:
                allocation = get_next_allocation(log)
                reconcile(doc=doc)

            elif reconciled:
                frappe.db.set_value(
                    "Process Payment Reconciliation", doc, "status", "Completed"
                )


def add_cleaning_task():
    frappe.enqueue(clean_accounts, queue="long", timeout=100000)


def clean_accounts():
    unused_accounts = frappe.db.sql(
        """
        SELECT acc.name, COUNT(gl.name) as count, MAX(gl.posting_date) as last
        FROM `tabAccount` acc
        LEFT JOIN  `tabGL Entry` gl
            ON gl.account = acc.name
        WHERE 1
        AND acc.is_group = 0
        AND acc.disabled = 0
        GROUP BY acc.name
        HAVING ( count = 0 OR last < DATE_SUB(CURDATE(), INTERVAL 1 YEAR) )
        """,
        as_dict=1,
    )
    # print(unused_accounts)
    length = len(unused_accounts)
    for ind, u in enumerate(unused_accounts):
        print(f"Processing : {ind+1}/{length} {u.name}")
        if u.count != 0:
            balance = get_balance_on(account=u.name)
            if balance == 0:
                print("Zero Balance")
                frappe.db.set_value("Account", u.name, "disabled", 1)
        else:
            print("Deleting")
            try:
                frappe.delete_doc("Account", u.name, delete_permanently=True)
            except NestedSetChildExistsError as e:
                print("Nested Error " + str(e))
            except Exception as e:
                print("OTEHER ERROR " + str(e))
    frappe.db.commit()  # v16: OK - operations script


def set_proper_donors():
    old_donor_id_map = {}
    i = 0
    for d in frappe.db.sql(
        """
                SELECT old_donor_id,GROUP_CONCAT(JSON_OBJECT('name',name,'full_name',full_name,'old_trust_code',old_trust_code)) as names
                FROM `tabDonor` 
                WHERE 1
                GROUP BY old_donor_id 
                HAVING count(*) > 1
                    """,
        as_dict=1,
    ):
        i = i + 1
        print(f"Preparing OLD DR Map Task {i}")
        one_map = {}
        for donor in json.loads("[" + d["names"] + "]"):
            address, contact, _ = get_best_contact_address(donor["name"])
            one_map.setdefault(
                str(donor["old_trust_code"]),
                {
                    "name": donor["name"],
                    "full_name": donor["full_name"],
                    "contact": contact,
                    "address": address,
                },
            )
        old_donor_id_map.setdefault(d["old_donor_id"], one_map)
        # old_donor_id_map.setdefault(
        #     d["old_donor_id"],
        #     {
        #         str(d["old_trust_code"]): d["name"]
        #         for d in json.loads("[" + d["names"] + "]")
        #     },
        # )
        # name1 = json.loads(names[0])
        # print(name1)
    # print(old_donor_id_map)
    print("_______________________________")
    print("_______________________________")
    print("____________Started Main Jon_______________")
    print("_______________________________")
    print("_______________________________")
    i = 0
    for receipt in frappe.db.sql(
        """
                    SELECT tdr.name,tdr.company,tdis.old_trust_code,tdr.donor,donor.old_donor_id 
                    FROM `tabDonation Receipt` tdr
                    JOIN `tabDhananjaya Import Settings Company` tdis
                    ON tdr.company = tdis.company
                    JOIN `tabDonor` donor
                    ON donor.name = tdr.donor
                    WHERE 1
                    """,
        as_dict=1,
    ):
        i += 1
        print(f"Receipt Task {i}")
        if receipt["old_donor_id"] in old_donor_id_map:
            required_donor = old_donor_id_map[receipt["old_donor_id"]][
                str(receipt["old_trust_code"])
            ]
            if receipt["donor"] != required_donor["name"]:
                frappe.db.set_value(
                    "Donation Receipt",
                    receipt["name"],
                    {
                        "donor": required_donor["name"],
                        "full_name": required_donor["full_name"],
                        "contact": required_donor["contact"],
                        "address": required_donor["address"],
                    },
                )

        if i % 1000 == 0:
            frappe.db.commit()  # v16: OK - operations script

    frappe.db.commit()  # v16: OK - operations script


def set_proper_patrons():
    old_patron_id_map = {}
    i = 0
    for d in frappe.db.sql(
        """
                SELECT old_patron_id,GROUP_CONCAT(JSON_OBJECT('name',name,'full_name',full_name,'old_trust_code',old_trust_code)) as names
                FROM `tabPatron` 
                WHERE 1
                GROUP BY old_patron_id 
                HAVING count(*) > 1
                    """,
        as_dict=1,
    ):
        i = i + 1
        print(f"Preparing OLD DR Map Task {i}")
        one_map = {}
        for patron in json.loads("[" + d["names"] + "]"):
            one_map.setdefault(
                str(patron["old_trust_code"]),
                {
                    "name": patron["name"],
                    "patron_name": patron["full_name"],
                },
            )
        old_patron_id_map.setdefault(d["old_patron_id"], one_map)
        # old_donor_id_map.setdefault(
        #     d["old_donor_id"],
        #     {
        #         str(d["old_trust_code"]): d["name"]
        #         for d in json.loads("[" + d["names"] + "]")
        #     },
        # )
        # name1 = json.loads(names[0])
        # print(name1)
    # print(old_donor_id_map)
    print("_______________________________")
    print("_______________________________")
    print("____________Started Main Job_______________")
    print("_______________________________")
    print("_______________________________")
    i = 0
    for receipt in frappe.db.sql(
        """
                    SELECT tdr.name,tdr.company,tdis.old_trust_code,tdr.patron,patron.old_patron_id 
                    FROM `tabDonation Receipt` tdr
                    JOIN `tabDhananjaya Import Settings Company` tdis
                    ON tdr.company = tdis.company
                    JOIN `tabPatron` patron
                    ON patron.name = tdr.patron
                    WHERE 1
                    """,
        as_dict=1,
    ):
        i += 1
        print(f"Receipt Task {i}")
        if receipt["old_patron_id"] in old_patron_id_map:
            required_patron = old_patron_id_map[receipt["old_patron_id"]][
                str(receipt["old_trust_code"])
            ]
            if receipt["patron"] != required_patron["name"]:
                frappe.db.set_value(
                    "Donation Receipt",
                    receipt["name"],
                    {
                        "patron": required_patron["name"],
                        "patron_name": required_patron["patron_name"],
                    },
                )

        if i % 1000 == 0:
            frappe.db.commit()  # v16: OK - operations script

    frappe.db.commit()  # v16: OK - operations script


# def cash_entries_adjust():
# 	query = """
# 			SELECT tdr.name as receipt, tdr.amount as Amount
# 			FROM `tabDonation Receipt` tdr
# 			LEFT JOIN `tabJournal Entry` tje
# 			ON tje.donation_receipt  = tdr.name
# 			WHERE tdr.docstatus = 1
# 			AND tdr.payment_method  = "Cash"
# 			AND tje.name IS NULL
# 			AND tdr.receipt_date >= "2023-04-01"
# 			AND tdr.company = "Hare Krishna Movement Jaipur"
# 			"""
# 	for r in frappe.db.sql(query=query,as_dict=1):
# 		cash_journal_entry(r['receipt'])
# 	frappe.db.commit()

# def cash_journal_entry(receipt_number):
# 	receipt_doc = frappe.get_doc("Donation Receipt",receipt_number)
# 	seva_type_doc = frappe.get_cached_doc("Seva Type", receipt_doc.seva_type)

# 	default_cost_center = receipt_doc.get_cost_center()

# 	je = {
# 		"doctype": "Journal Entry",
# 		"voucher_type": "Cash Entry",
# 		"company": receipt_doc.company,
# 		"donation_receipt": receipt_doc.name,
# 		"docstatus": 1,
# 	}

# 	##### In Case of New Donor Request #####

# 	if not receipt_doc.donor:
# 		if not receipt_doc.donor_creation_request:
# 			frappe.throw(
# 				"At least one of Donor or Donation Creation Request document is must to process."
# 			)
# 		donor_name = frappe.get_value(
# 			"Donor Creation Request", receipt_doc.donor_creation_request, "full_name"
# 		)
# 	else:
# 		donor_name = receipt_doc.full_name

# 	########################################

# 	je.setdefault(
# 		"user_remark",
# 		f"BEING AMOUNT RECEIVED FOR {receipt_doc.seva_type} FROM {donor_name} AS PER R.NO.{receipt_doc.name} DT:{receipt_doc.receipt_date} {receipt_doc.preacher} ",
# 	)

# 	# Jounrnal Entry date should be the day Cashier received the amount because it has to tally with Cashbook.
# 	cash_date = receipt_doc.modified

# 	je.setdefault("posting_date", cash_date)
# 	je.setdefault(
# 		"accounts",
# 		[
# 			{
# 				"account": receipt_doc.donation_account,
# 				"credit_in_account_currency": receipt_doc.amount,
# 				# This is needed for cost center analysis.
# 				"cost_center": default_cost_center,
# 			},
# 			{
# 				"account": receipt_doc.cash_account,
# 				"debit_in_account_currency": receipt_doc.amount,
# 				# As it not compulsory. It will pick up the default.--> But now it is picking of other company, so explicitly declared.
# 				"cost_center": default_cost_center,
# 			},
# 		],
# 	)
# 	je_doc = frappe.get_doc(je)
# 	je_doc.insert()


def notifiy_users_of_new_version():
    users = frappe.get_all(
        "Firebase App Token", filters={"app": "Dhananjaya"}, pluck="user"
    )
    users = list(set(users))
    for user in users:
        message = f"""Starting soon, we're switching to OTP login for simplicity.\n\nRemember, your registered email is {user}\n\nMake sure you have access to it for OTPs.\n\nNext App Update will be released on 12th March | 07:00 PM.
                    """
        doc = frappe.get_doc(
            {
                "doctype": "App Notification",
                "app": "Dhananjaya",
                "user": user,
                "subject": "Important Update!",
                "message": message,
            }
        )
        doc.insert(ignore_permissions=True)
    frappe.db.commit()  # v16: OK - operations script


def ahmd_mobile_clean():
    frappe.db.sql("Donor Contact")


def import_special_pujas():
    for idx, d in enumerate(frappe.get_all("Temp Data", fields="*")):
        if d["value_set"]:
            continue
        if not d["occasion"]:
            continue
        print(f"Processing {idx}")
        if len(d["mobile"]) < 15:
            clean_contact = re.sub(r"\D", "", d["mobile"])
            clean_contact = clean_contact[-10:]
        else:
            contacts = []
            # if " " in d["mobile"]:
            #     contacts = d["mobile"].split(" ")
            # for contact in contacts:
            clean_contact = re.sub(r"\D", "", d["mobile"])[:10]
            print(clean_contact)
            donor = identify_donor(
                contact=clean_contact, email=None, pan=None, aadhar=None
            )
            if donor:
                donor = frappe.get_doc("Donor", donor)
                donor.append(
                    "puja_details",
                    {
                        "day": d["day"],
                        "month": calendar.month_name[int(d["month"])],
                        "occasion": d["occasion"],
                    },
                )
                print(f"Saving Donor{donor.name}")
                donor.save()
                frappe.db.set_value("Temp Data", d["name"], "value_set", 1)
                # break
        frappe.db.commit()  # v16: OK - operations script


def create_seva_type():
    for s in frappe.db.sql(
        "SELECT company,seva_type FROM `tabDonation Receipt` WHERE seva_type IS NOT NULL GROUP BY company,seva_type"
    ):
        if not frappe.db.exists("Seva Type", {"company": s[0], "seva_name": s[1]}):
            doc = frappe.get_doc(
                {
                    "doctype": "Seva Type",
                    "company": s[0],
                    "seva_name": s[1],
                    "80g_applicable": 1,
                    # 'patronship_allowed':1,
                    "include_in_analysis": 1,
                    # 'csr_allowed':1
                }
            )
            doc.insert()
    frappe.db.commit()  # v16: OK - operations script


def create_seva_subtype():
    for s in frappe.db.sql(
        "SELECT seva_subtype FROM `tabDonation Receipt` WHERE seva_subtype IS NOT NULL GROUP BY seva_subtype"
    ):
        if not frappe.db.exists("Seva Subtype", {"seva_name": s[0]}):
            doc = frappe.get_doc(
                {
                    "doctype": "Seva Subtype",
                    # "company": s[0],
                    "seva_name": s[0],
                    "80g_applicable": 1,
                    # 'patronship_allowed':1,
                    "include_in_analysis": 1,
                    # 'csr_allowed':1
                }
            )
            doc.insert()
    frappe.db.commit()  # v16: OK - operations script


def set_seva_type():
    for r in frappe.get_all(
        "Donation Receipt",
        filters={
            "company": "Hare Krishna Movement Vrindavan",
            "seva_type": ["is", "not set"],
        },
        pluck="name",
    ):
        print(r)
        frappe.db.set_value("Donation Receipt", r, "seva_type", "GEN - HKMV")

    for r in frappe.get_all(
        "Donation Receipt",
        filters={
            "company": "Vrindavan Chandrodaya Mandir Trust",
            "seva_type": ["is", "not set"],
        },
        pluck="name",
    ):
        frappe.db.set_value("Donation Receipt", r, "seva_type", "GNRL - VCMT")

    frappe.db.commit()  # v16: OK - operations script


def set_seva_type_for_no_company_tagged():
    companies_abbr = {}
    for c in frappe.get_all("Company", fields=["company_name", "abbr"]):
        companies_abbr.setdefault(c["company_name"], c["abbr"])
    for r in frappe.get_all(
        "Donation Receipt", fields=["name", "seva_type", "company"]
    ):
        if r["seva_type"] and "-" not in r["seva_type"]:
            new_seva_type = r["seva_type"] + " - " + companies_abbr[r["company"]]
            frappe.db.set_value("Donation Receipt", r, "seva_type", new_seva_type)
    frappe.db.commit()  # v16: OK - operations script


def set_full_name():
    for r in frappe.get_all(
        "Donation Receipt",
        fields=["name", "donor"],
    ):
        full_name = frappe.db.get_value("Donor", r["donor"], "full_name")
        frappe.db.set_value("Donation Receipt", r, "full_name", full_name)

    frappe.db.commit()  # v16: OK - operations script


def correct_names_patron():
    # for p in frappe.get_all("Patron",pluck = "name"):
    #     patron_doc = frappe.get_doc("Patron",p)
    #     patron_doc.first_name = patron_doc.first_name + " "
    #     patron_doc.save()
    # frappe.db.commit()
    for p in frappe.get_all("Patron Privilege Puja", pluck="name"):
        puja_doc = frappe.get_doc("Patron Privilege Puja", p)
        puja_doc.occasion = puja_doc.occasion + " "
        puja_doc.save()
    frappe.db.commit()  # v16: OK - operations script
    for p in frappe.get_all("Patron Privilege Puja", pluck="name"):
        puja_doc = frappe.get_doc("Patron Privilege Puja", p)
        puja_doc.occasion = puja_doc.occasion.strip()
        puja_doc.save()
    frappe.db.commit()  # v16: OK - operations script


@frappe.whitelist()
def query():
    pass
    # return update_depreciations()
    # update_barcodes()
    # update_special_pujas()
    # return upload_mumbai_data()
    # update_current_preacher()
    return


def update_depreciations():
    for temp_entry in frappe.get_all("Temp Data", fields=["*"]):
        asset_doc = frappe.get_doc("Asset", temp_entry["asset_id"])
        asset_location = asset_doc.location
        if asset_doc.docstatus == 1:
            cancel_dependent_asset_docs(asset_doc)
            asset_doc.reload()
            asset_doc.cancel()
        asset_doc.reload()
        duplicate_asset = frappe.copy_doc(doc=asset_doc)
        duplicate_asset.location = asset_location
        if duplicate_asset.available_for_use_date is None:
            duplicate_asset.available_for_use_date = duplicate_asset.purchase_date
        duplicate_asset.finance_books[0].depreciation_start_date = temp_entry[
            "depreciation_posting_date"
        ]
        duplicate_asset.finance_books[0].total_number_of_depreciations = temp_entry[
            "total_number_of_dep"
        ]
        duplicate_asset.finance_books[0].frequency_of_depreciation = temp_entry[
            "frequency_of_dep"
        ]
        duplicate_asset.save()
        duplicate_asset.submit()
        frappe.rename_doc(
            "Asset", duplicate_asset.name, asset_doc.name + "-1", merge=False
        )
        frappe.db.commit()  # v16: OK - operations script


def cancel_dependent_asset_docs(asset_doc):
    jeas = frappe.get_all(
        "Journal Entry Account",
        filters=[
            ["docstatus", "=", 1],
            ["reference_name", "=", asset_doc.name],
            ["account", "LIKE", "%Accumulated Depreciations%"],
        ],
        pluck="parent",
    )
    journal_entries = list(set(jeas))
    for j in journal_entries:
        frappe.get_doc("Journal Entry", j).cancel()

    for m in frappe.get_all(
        "Asset Movement Item",
        filters=[["docstatus", "=", 1], ["asset", "=", asset_doc.name]],
        pluck="parent",
    ):
        frappe.get_doc("Asset Movement", m).cancel()


@frappe.whitelist()
def fetch_successful_docs(doctype):
    docs = frappe.get_all(
        "Data Migration Success", filters={"document_type": doctype}, pluck="docname"
    )
    return docs


@frappe.whitelist()
def create_document():
    data = json.loads(frappe.request.data)
    # frappe.local.response.update({"request":data})

    # insert document from request data
    doc = frappe.get_doc(data).insert(ignore_links=True, ignore_mandatory=True)

    # set response data
    frappe.local.response.update({"data": doc.as_dict()})

    if doc.name != data["name"]:
        frappe.rename_doc(data["doctype"], doc.name, data["name"], merge=False)

    # commit for POST requests
    frappe.db.commit()  # v16: OK - operations script


def update_barcodes():
    for item in frappe.get_all(
        "Item", fields=["item_code"], filters=[["is_sales_item", "=", "1"]]
    ):
        item_doc = frappe.get_doc("Item", item["item_code"])
        found = False
        for b in item_doc.barcodes:
            if b.barcode == item_doc.item_code:
                found = True
                break
        if not found:
            item_doc.append("barcodes", {"barcode": item_doc.name})
            item_doc.save()
            frappe.db.commit()  # v16: OK - operations script


def update_special_pujas():
    datas = frappe.get_all("Temp Data", fields=["*"])
    for data in datas:
        if data["mobile"]:
            clean_contact = re.sub(r"\D", "", data["mobile"])[-10:]
            contacts = frappe.db.sql(
                f"""
                    select contact_no,parent
                    from `tabDonor Contact`
                    where REGEXP_REPLACE(contact_no, '[^0-9]+', '') LIKE '%{clean_contact}%' and parenttype = 'Donor'
                    """,
                as_dict=1,
            )
            donor = None
            if len(contacts) > 0:
                donor = contacts[0]["parent"]
                donor_doc = frappe.get_doc("Donor", donor)
                if not data["date"]:
                    data["date"] = "NA"
                donor_doc.append(
                    "puja_details",
                    {
                        "month": data["donor"].strftime("%B"),
                        "day": data["donor"].day,
                        "occasion": data["date"],
                    },
                )
                donor_doc.save()

            if donor is not None:
                frappe.db.set_value("Temp Data", data["name"], "found", 1)
    frappe.db.commit()  # v16: OK - operations script


# @frappe.whitelist()
def update_preacher_donor(d):
    max = frappe.db.sql(
        f"""
                    SELECT preacher, count(*) as nos
                    from `tabDonation Receipt` tdr 
                    where donor = '{d}' AND receipt_date > NOW() - INTERVAL 3 YEAR  
                    GROUP BY preacher
                    order by nos desc, receipt_date desc
                    """
    )
    if len(max) > 0:
        max_preacher = max[0][0]
        if max_preacher is not None:
            frappe.db.set_value(
                "Donor", d, "llp_preacher", max_preacher, update_modified=False
            )
    else:
        latest_data = frappe.db.sql(
            f"""
                SELECT preacher,receipt_date
                FROM `tabDonation Receipt` tdr 
                WHERE donor = '{d}'
                order by receipt_date desc
                """
        )
        if len(latest_data) > 0:
            frappe.db.set_value(
                "Donor", d, "llp_preacher", latest_data[0][0], update_modified=False
            )
    frappe.db.commit()  # v16: OK - operations script


def cancel_dr():
    from dhananjaya.dhananjaya.doctype.donation_receipt.donation_receipt import (
        receipt_cancel_operations,
    )

    drs = frappe.get_all("Donation Receipt", filters={"is_ecs": 1}, pluck="name")
    for dr in drs:
        receipt_cancel_operations(dr)
    frappe.db.commit()  # v16: OK - operations script


def journal_entry_preacher_update():
    import re

    jeas = frappe.get_all(
        "Journal Entry Account",
        filters={"is_a_donation": 1},
        fields=["parent", "devotee", "name", "dr_no"],
    )
    # return jeas
    pattern = r"^RC-\d{2}-\d{5}$"
    selected = []
    for jea in jeas:
        if jea.dr_no and (not jea.devotee) and re.match(pattern, str(jea.dr_no)):
            selected.append([jea.dr_no, jea.name, jea.parent])

    # return selected
    for s in selected:
        devotee = frappe.db.get_value("Donation Receipt", s[0], "preacher")

        if s[0] is None or devotee is None:
            return devotee, s

        frappe.db.set_value("Journal Entry Account", s[1], "devotee", devotee)

        statement = frappe.db.get_value("Journal Entry", s[2], "user_remark")
        pattern = r"None$"
        try:
            new_statement = re.sub(pattern, devotee, statement)
        except:
            return pattern, devotee, statement, s

        # return new_statement
        frappe.db.sql(
            f"""
                        update `tabJournal Entry`
                        set user_remark ='{new_statement}'
                        where name = '{jea.parent}'
                        """
        )
        frappe.db.set_value("Journal Entry", s[2], "user_remark", new_statement)

    frappe.db.commit()  # v16: OK - operations script
    # return selected, len(selected)
    # frappe.db.commit()


def get_donation_details():
    conditions = """
                    AND tdr.receipt_date > NOW() - INTERVAL 10 year
                    AND tdr.docstatus = 1
                    AND tdr.seva_subtype NOT LIKE "%heri%"
                    """
    donors = {}
    for i in frappe.db.sql(
        f"""
                    select tdr.donor as donor_id, tdr.receipt_date 
                    from `tabDonation Receipt` tdr
                    join (
                        select tdr.donor, MAX(tdr.receipt_date) as last_donation_date
                        from `tabDonation Receipt` tdr
                        where 1 {conditions}
                        group by donor
                    ) as last_donation_details
                    on last_donation_details.donor = tdr.donor and tdr.receipt_date = last_donation_details.last_donation_date
                    where 1 {conditions} AND tdr.preacher = 'PNVD'
                    """,
        as_dict=1,
    ):
        donors.setdefault(i["donor_id"], i)

    donors_str = ",".join([f"'{k}'" for k in donors.keys()])

    for i in frappe.db.sql(
        f"""
                    select
                        tdr.donor as donor_id,
                        tdr.full_name as donor_name, 
                        sum(tdr.amount) as total_donation,
                        count(tdr.name) as times,
                        donor_details.contact,
                        donor_details.address
                        # MAX(tdr.receipt_date) as last_donation
                    from `tabDonation Receipt` tdr
                    join (
                            select
                                td.name as donor_id, td.full_name,
                                GROUP_CONCAT(DISTINCT tc.contact_no SEPARATOR' , ') as contact,
                                GROUP_CONCAT(DISTINCT ta.address_line_1,ta.address_line_2,ta.city SEPARATOR' | ') as address
                            from `tabDonor` td
                            left join `tabDonor Address` ta 
                                on ta.parent = td.name
                            left join `tabDonor Contact` tc 
                                on tc.parent = td.name
                            group by donor_id
                        ) as donor_details
                        on donor_details.donor_id = tdr.donor 
                    where tdr.donor IN ({donors_str})
                    {conditions}
                    group by tdr.donor
                    order by times desc
                    """,
        as_dict=1,
    ):
        donors[i["donor_id"]].update(i)

    for i in frappe.db.sql(
        f"""
                            select 
                                donor as donor_id,
                                preacher,
                                sum(tdr.amount) as total_donation,count(tdr.amount) as times
                            from `tabDonation Receipt` tdr
                            where 1 {conditions} AND tdr.donor IN ({donors_str})
                            group by donor,preacher
                            order by donor,total_donation desc
                                """,
        as_dict=1,
    ):
        if not "top_collector" in donors[i["donor_id"]]:
            donors[i["donor_id"]].setdefault("top_collector", i["preacher"])
            donors[i["donor_id"]].setdefault(
                "top_collector_donation", i["total_donation"]
            )
            donors[i["donor_id"]].setdefault("top_collector_times", i["times"])
            continue
        if not "second_collector" in donors[i["donor_id"]]:
            donors[i["donor_id"]].setdefault("second_collector", i["preacher"])
            donors[i["donor_id"]].setdefault(
                "second_collector_donation", i["total_donation"]
            )
            donors[i["donor_id"]].setdefault("second_collector_times", i["times"])

    delets = []
    for d in donors:
        if "total_donation" not in donors[d]:
            delets.append(d)

    donors = {k: v for k, v in donors.items() if k not in delets}

    data = [v for k, v in donors.items()]
    headers = list(set().union(*data))
    # return headers
    from frappe.utils.xlsxutils import make_xlsx

    xlsx_data = [headers]

    for d in data:
        row = []
        for h in headers:
            if h in d:
                row.append(d[h])
            else:
                row.append("")
        xlsx_data.append(row)

    xlsx_file = make_xlsx(xlsx_data, "Donation Receipt")

    frappe.response["filename"] = "PNVD" + ".xlsx"
    frappe.response["filecontent"] = xlsx_file.getvalue()
    frappe.response["type"] = "binary"

    return xlsx_file


def create_donors_clear_suspense():
    all = frappe.get_all("Temp Data", fields="*")
    for index, a in enumerate(all):
        # if index > 100 and index <= 150:
        # if index:
        receipt = frappe.new_doc("Donation Receipt")
        receipt.update(
            {
                "naming_series": "RC-.YY.-1.####",
                "company": "Hare Krishna Movement Jaipur",
                "receipt_date": a["date"],
                "donor": a["donor"],
                "payment_method": "NEFT/IMPS",
                "amount": a["amount"],
                "seva_type": "GEN - HKMJ",
                "remarks": a["remarks"],
            }
        )
        if a["devotee"]:
            receipt.preacher = a["devotee"]
        receipt.save()

        frappe.db.set_value(
            "Donation Receipt",
            receipt.name,
            {"workflow_state": "Realized", "docstatus": 1},
        )

        je = {
            "voucher_type": "Journal Entry",
            "naming_series": "ACC-JV-.YYYY.-",
            "company": "Hare Krishna Movement Jaipur",
            # "temp_datetime":f"{dattime}",
            "posting_date": "2023-03-25",
            "cheque_no": a["remarks"],
            "cheque_date": f"{a['date']}",
            "user_remark": f"BEING AMOUNT RECEIVED FOR General Donation - HKMJ FROM {receipt.full_name} AS PER R.NO. {receipt.name} DT. {a['date']} {receipt.preacher}",
            "accounts": [
                {
                    "account": "Donation Income-India - HKMJ",
                    "devotee": f"{receipt.preacher}",
                    "cost_center": "General Donation - HKMJ",
                    "debit_in_account_currency": 0,
                    "debit": 0,
                    "credit_in_account_currency": a["amount"],
                    "credit": a["amount"],
                    "is_a_donation": 1,
                    "dr_no": receipt.name,
                    "donor_name": f"{receipt.full_name}",
                    "receipt_date": f"{a['date']}",
                },
                {
                    "account": "Suspense - HKMJ",
                    "cost_center": "Main - HKMJ",
                    "debit_in_account_currency": a["amount"],
                    "debit": a["amount"],
                    "credit_in_account_currency": 0,
                    "credit": 0,
                    "suspense_jv": a["suspense"],
                },
            ],
        }
        # je_doc = frappe.get_doc(je)
        # return je
        je_doc = frappe.new_doc("Journal Entry")
        je_doc.update(je)
        je_doc.save()
        je_doc.submit()

        frappe.db.commit()  # v16: OK - operations script


def update_suspense():
    all = frappe.get_all("Temp Data", fields=["donation_jv", "bank_jv"])
    i = 1
    for a in all:
        frappe.db.sql(
            f"""
                        update `tabJournal Entry Account`
                        set suspense_jv = '{a["bank_jv"]}'
                        where parent = '{a["donation_jv"]}' and account = 'Suspense - HKMJ'
                        """
        )
        # if i == 1:
        # 	break
    frappe.db.commit()  # v16: OK - operations script


def make_custom_fields():
    custom_fields = {
        "Journal Entry": [
            dict(
                fieldname="donation_receipt",
                label="Donation Receipt",
                fieldtype="Link",
                options="Donation Receipt",
                insert_after="tax_withholding_category",
            ),
            dict(
                fieldname="bank_statement_name",
                label="Bank Statement Name",
                fieldtype="Data",
                insert_after="donation_receipt",
                hidden=1,
                read_only=1,
            ),
        ]
    }

    create_custom_fields(custom_fields)
    frappe.db.commit()  # v16: OK - operations script
    return custom_fields


def update_current_preacher():
    donors = frappe.get_all("Donor", pluck="name")
    for d in donors:
        frappe.enqueue(
            update_preacher_donor,
            queue="long",
            job_name="Updating Preacher",
            timeout=1000000,
            d=d,
        )


# def update_preachers():
#     settings = frappe.get_cached_doc("Dhananjaya Import Settings")
#     companies = ",".join([str(c.old_trust_code) for c in settings.companies_to_import])
#     data = run_query(
#         f"""
#                     select DR_NUMBER,PREACHER_CODE
#                     from `view_receipt_details`
#                     where TRUST_ID IN ({companies})
#                     """
#     )
#     for d in data:
#         frappe.enqueue(
#             update_donation_receipt,
#             queue="long",
#             job_name="Updating Donor Receipt",
#             timeout=100000,
#             d=d,
#         )
# n = 10000
# chunks = [data[i * n:(i + 1) * n] for i in range((len(data) + n - 1) // n )]
# for ind, chunk in enumerate(chunks):
# 	frappe.enqueue(assign_chunk, queue='long',job_name=f"Assinging Chunk #{ind}",timeout=100000,chunk=chunk)
# # return chunks


def assign_chunk(chunk):
    for d in chunk:
        frappe.enqueue(
            update_donation_receipt,
            queue="long",
            job_name="Updating Donor Receipt",
            timeout=100000,
            d=d,
        )


def update_donation_receipt(d):
    frappe.db.sql(
        f"""
                    update `tabDonation Receipt`
                    set preacher = '{d['PREACHER_CODE']}'
                    where old_dr_no = '{d['DR_NUMBER']}'
                    """
    )
    frappe.db.commit()  # v16: OK - operations script


# def assign_
# 	frappe.enqueue(insert_a_donor, queue='short',job_name="Inserting Donor",timeout=100000,d=d)
# 	for d in data:
# 		frappe.db.sql(f"""
# 						update `tabDonation Receipt`
# 						set preacher = '{d['PREACHER_CODE']}'
# 						where old_dr_no = '{d['DR_NUMBER']}'
# 						""")
# 	frappe.db.commit()


def update_asset_data():
    category_details = {}
    for c in frappe.db.get_all("Asset Category", fields="*"):
        category = frappe.get_doc("Asset Category", c)
        if len(category.finance_books) > 0:
            details = category.finance_books[0]
            category_details.setdefault(c["name"], details.as_dict())
    # return category_details
    for a in frappe.db.get_all(
        "Asset",
        filters={
            "docstatus": 0,
        },
        fields=["name", "asset_category"],
    ):
        if a["asset_category"] in category_details:
            asset = frappe.get_doc("Asset", a["name"])
            if len(asset.finance_books) == 0:
                asset.available_for_use_date = asset.purchase_date
                asset.append(
                    "finance_books",
                    {
                        "finance_book": category_details[asset.asset_category][
                            "finance_book"
                        ],
                        "depreciation_method": category_details[asset.asset_category][
                            "depreciation_method"
                        ],
                        "total_number_of_depreciations": category_details[
                            asset.asset_category
                        ]["total_number_of_depreciations"],
                        "frequency_of_depreciation": category_details[
                            asset.asset_category
                        ]["frequency_of_depreciation"],
                        "depreciation_start_date": add_to_date(
                            asset.purchase_date, days=1
                        ),
                    },
                )
            # asset.docstatus = 1
            asset.submit()
    frappe.db.commit()  # v16: OK - operations script
    # return categories


def match_suspense():
    frappe.db.sql(
        """
                        
                    """
    )


def update_total_debit_credit():
    entries = frappe.get_all(
        "Journal Entry", fields=["name"], filters={"total_debit": 0}
    )

    return entries
    for e in entries:
        total = 0
        je = frappe.get_doc("Journal Entry", e)
        for a in je.accounts:
            total += a.debit
        frappe.db.set_value("Journal Entry", e, "total_debit", total)
        frappe.db.set_value("Journal Entry", e, "total_credit", total)
    frappe.db.commit()  # v16: OK - operations script


def update_taxes():
    import re

    parent_item_groups = {"BBT": "BBT"}

    for parent_item_group, tax_title in parent_item_groups.items():
        children_groups = get_descendants_of("Item Group", parent_item_group)
        children_groups.append(parent_item_group)
        items = []
        query = """select item.name,tax.item_tax_template,tax.name as tax_name
                        from `tabItem` item
                        join `tabItem Group` item_group
                        on item.item_group = item_group.name
                        join `tabItem Tax` tax
                        on tax.parent = item.name
                        where item_group.name in {}
                        """.format(
            tuple(children_groups)
        )
        items = frappe.db.sql(query, as_dict=1)

        for item in items:
            tax_rate = (re.findall("[0-9]+", item["item_tax_template"]))[0]
            new_tax_template = "{} - {}% - TSFJ".format(tax_title, tax_rate)
            frappe.db.set_value(
                "Item Tax", item["tax_name"], "item_tax_template", new_tax_template
            )
    frappe.db.commit()  # v16: OK - operations script
    return "success"


def update_item_types_of_materi_request_items():
    items = frappe.db.get_all(
        "Item", fields=["item_code", "is_stock_item", "is_fixed_asset"]
    )
    item_map = {}
    for item in items:
        item_map[item["item_code"]] = frappe._dict(
            is_stock_item=item["is_stock_item"], is_fixed_asset=item["is_fixed_asset"]
        )
    mr_items = frappe.db.get_all("Material Request Item", pluck="item_code")

    unique_items = list(set(mr_items))

    for item in unique_items:
        if item in item_map:
            item_type = get_item_type(item_map[item])
            frappe.db.sql(
                """
                            UPDATE `tabMaterial Request Item`
                            SET item_type = '{}'
                            WHERE  item_code = '{}'
                            """.format(
                    item_type, item
                )
            )
            frappe.db.sql(
                """
                            UPDATE `tabPurchase Order Item`
                            SET item_type = '{}'
                            WHERE  item_code = '{}'
                            """.format(
                    item_type, item
                )
            )

    frappe.db.commit()  # v16: OK - operations script

    return unique_items


def get_item_type(item_details):
    if item_details["is_fixed_asset"] == 1:
        return "Asset"
    if item_details["is_stock_item"] == 1:
        return "Stock"
    return "Non-Stock"


def update_all_trashed_po():
    pos = frappe.db.sql(
        """
        select po.name
        from `tabPurchase Order` po
        join `tabToDo` todo on todo.reference_name = po.name
        where po.workflow_state = 'Trashed'
        group by po.name
        """,
        as_dict=0,
    )  #
    for po in pos:
        frappe.db.sql(
            """
                UPDATE `tabToDo`
                SET status = 'Cancelled'
                WHERE status = 'Open'
                AND reference_name = '{}'
                AND reference_type = 'Purchase Order'
                """.format(
                po[0]
            )
        )
    frappe.db.commit()  # v16: OK - operations script
    return pos


def update_folk_student_name():
    folk_students = frappe.get_all(
        "FOLK Student",
        fields=["name", "student_mobile_number"],
        filters={"name": ["like", "%KS%"]},
    )
    for std in folk_students:
        frappe.rename_doc("FOLK Student", std["name"], std["student_mobile_number"])
        frappe.db.commit()  # v16: OK - operations script


# Operation - Update all FOLK Donation with FOLK Guide Value


def update_folk_donation():
    donations = frappe.get_all("FOLK Donation", fields=["name", "folk_student"])
    for d in donations:
        std = frappe.get_doc("FOLK Student", d["folk_student"])
        frappe.db.set_value("FOLK Donation", d["name"], "folk_guide", std.folk_guide)

    frappe.db.commit()  # v16: OK - operations script


def update_items():
    app_items = []

    items = frappe.get_all("Temp TSF HSN", fields=["name", "hsn", "rate"])

    for item in items:
        siblings = getSiblings(item["name"])
        for s in siblings:
            app_items.append(
                {
                    "name": s,
                    "hsn": int(item["hsn"]),
                    "rate": int(item["rate"]),
                }
            )
    app_items = getUniqueItems(app_items)
    updateItems(app_items)

    return app_items


def updateItems(items):
    for item in items:
        doc = frappe.get_doc("Item", item["name"])
        if item["hsn"] != 0:
            doc.gst_hsn_code = item["hsn"]
        old_rate = 0
        if doc.taxes != []:
            old_rate = int(list(doc.taxes[0].item_tax_template.split(" "))[-1])
        doc.set("taxes", [])
        if item["rate"] != 0:
            doc.append(
                "taxes", {"item_tax_template": "TSF GST {}".format(item["rate"])}
            )

        doc.save()
        frappe.db.commit()  # v16: OK - operations script

        if doc.has_variants != 1:
            prices = frappe.get_all(
                "Item Price",
                filters={"item_code": doc.name, "price_list": "Standard Selling"},
                fields=["name", "price_list_rate"],
            )
            for price in prices:
                old_price = price["price_list_rate"]
                cur_rate = item["rate"]
                cur_price = old_price * ((100 + old_rate) / (100 + cur_rate))
                frappe.db.set_value(
                    "Item Price", price["name"], "price_list_rate", cur_price
                )


def getUniqueItems(items):
    result = []

    for item in items:
        found = 0
        for r in result:
            if item["name"] == r["name"]:
                found = 1
                r["rate"] = max(item["rate"], r["rate"])
                break
        if found == 0:
            result.append(item)
    return result


def getSiblings(name):
    sbls = []
    doc = frappe.get_doc("Item", name)
    if doc.variant_of is not None:
        parent = doc.variant_of
        sbls.extend(
            frappe.get_all("Item", filters={"variant_of": doc.variant_of}, pluck="name")
        )
        sbls.append(parent)
    else:
        sbls.append(doc.name)
    return sbls
    # items = frappe.db.sql("""
    # 	SELECT DISTINCT `tabItem`.`name`
    # 	FROM `tabItem`
    # 	JOIN `tabItem Price`
    # 	ON `tabItem Price`.item_code = `tabItem`.name
    # 	WHERE 1
    # 	""",as_dict=1)
    # pricesp = []
    # maxp =[]
    # for item in items:
    # 	prices = frappe.db.sql("""
    # 				SELECT `name`,`price_list_rate`,`item_code`
    # 				FROM `tabItem Price`
    # 				WHERE `tabItem Price`.item_code = '{}'
    # 				AND selling = 1
    # 				""".format(item['name']),as_dict=1)
    # 	if len(prices) > 1:
    # 		pricesp.append(prices)
    # 		maxPricedItem = max(prices, key=lambda x:x['price_list_rate'])
    # 		maxp.append(maxPricedItem)
    # 		for price in prices:
    # 			if price['name'] != maxPricedItem['name']:
    # 				# frappe.delete_doc('Item Price', price['name'])
    # 				frappe.db.sql("""
    # 					DELETE FROM `tabItem Price`
    # 					WHERE name = '{}';
    # 					""".format(price['name']))
    # 				frappe.db.commit()
    # return(pricesp,maxp)
    # doc = frappe.get_doc('POS Closing Entry','POS-CLO-2021-00076')
    # return doc.pos_transactions
    # candidates = frappe.db.sql("""
    # 	SELECT `name`
    # 	FROM `tabAshraya Candidate`
    # 	WHERE 1
    # 	""",as_dict=1)
    # for candidate_id in candidates:
    # 	latest_ashraya = frappe.db.sql("""
    # 						SELECT acp.level
    # 						FROM `tabAshraya Candidate` as ac
    # 						JOIN
    # 						(
    # 							SELECT `tabAshraya Ceremony Participant`.participant ,`tabAshraya Ceremony`.date, `tabAshraya Ceremony Participant`.level, `tabAshraya Level`.level_index
    # 							FROM `tabAshraya Ceremony Participant`
    # 							JOIN `tabAshraya Level`
    # 							ON `tabAshraya Ceremony Participant`.level = `tabAshraya Level`.name
    # 							JOIN `tabAshraya Ceremony`
    # 							ON `tabAshraya Ceremony Participant`.ashraya_ceremony = `tabAshraya Ceremony`.name
    # 						) as acp
    # 						ON acp.participant = ac.name
    # 						WHERE ac.name = '{}'
    # 						ORDER BY level_index DESC
    # 						LIMIT 1
    # 						""".format(candidate_id['name']))
    # 	if len(latest_ashraya) > 0 and len(latest_ashraya[0]) > 0:
    # 		frappe.db.sql("""
    # 			UPDATE `tabAshraya Candidate`
    # 			SET latest_level_of_ashraya = '{}'
    # 			WHERE `tabAshraya Candidate`.name = '{}'
    # 			""".format(latest_ashraya[0][0],candidate_id['name']))
    # 	frappe.db.commit()
    # data = frappe.db.sql("""
    #     SELECT
    #        	`item_code`,`item_name`,`item_tax_template`,itax.`name` as tax_name
    #     FROM `tabItem` item
    #     JOIN `tabItem Tax` itax
    #         ON itax.parent = item.name
    # """, values={}, as_dict=1) #-- WHERE gl.company = %(company)s
    # for row in data:
    # 	if "TSF GST" in row['item_tax_template']:
    # 		frappe.db.set_value('Item Tax', row['tax_name'], 'tax_category', '')
    # 		#frappe.db.delete('Item Tax', {'name': row['tax_name']})
    # # frappe.db.commit()
    # # for item in data:
    # # 	doc = frappe.get_doc('Item', item['item_code'])
    # # 	if len(doc.taxes)==1:
    # # 		if "TSF" in doc.taxes[0].item_tax_template:
    # # 			first_tax = doc.taxes[0].item_tax_template
    # # 			new_tax = frappe.get_doc(
    # # 				doctype='Item Tax',
    # # 				item_tax_template='TSF IGST '+lastWord(first_tax)+' - TSFJ',
    # # 				parent = item['item_code'],
    # # 				parentfield= "taxes",
    # # 				parenttype= "Item",
    # # 				tax_category= "Out of State"
    # # 				)
    # # 			new_tax.insert() idx
    # frappe.db.commit()
    # return data


def lastWord(string):
    # split by space and converting
    # string to list and
    lis = list(string.split(" "))

    # length of list
    length = len(lis)

    # returning last element in list
    return lis[length - 1]


def update_stock_ledger_gl_entries(voucher_no):
    gl_entries = frappe.db.sql(
        """
                                select * from `tabGL Entry` where voucher_no = '{}'
                                """.format(
            voucher_no
        )
    )


def query_specific():
    blocks = [
        ("SINV-21-00310", 771.5),
        ("SINV-21-00311", 2911.47),
        ("SINV-21-00313", 836.5),
        ("SINV-21-00314", 2494.7),
        ("SINV-21-00316", 2869.75),
        ("SINV-21-00318", 5398),
        ("SINV-21-00319", 1649.76),
        ("SINV-21-00322", 2468.76),
        ("SINV-21-00321", 551.5),
    ]

    for block in blocks:
        voucher_no, amount = block[0], block[1]

        current_doc = frappe.get_doc("Sales Invoice", voucher_no)
        # Create Cost of Good Sold
        create_a_GL_Entry(
            current_doc, "Cost of Goods Sold - TSFJ", "Stock In Hand - TSFJ", amount, 0
        )
        create_a_GL_Entry(
            current_doc, "Stock In Hand - TSFJ", "Cost of Goods Sold - TSFJ", 0, amount
        )
        frappe.db.commit()  # v16: OK - operations script


def create_a_GL_Entry(doc, account, against, debit, credit):
    gl_doc = frappe.get_doc(
        {
            "doctype": "GL Entry",
            "posting_date": doc.posting_date,
            "account": account,
            "cost_center": "Main - TSFJ",
            "debit": debit,
            "debit_in_account_currency": debit,
            "credit": credit,
            "credit_in_account_currency": credit,
            "against": against,
            "voucher_type": doc.doctype,
            "voucher_no": doc.name,
            "company": doc.company,
        }
    )
    gl_doc.save(ignore_permissions=True)
    # frappe.get_doc("Sales Invoice",{})


def delete_two_entries():
    frappe.db.sql(
        """DELETE FROM `tabGL Entry` WHERE name = '{}'""".format("9c2aaa3a3d")
    )
    frappe.db.sql(
        """DELETE FROM `tabGL Entry` WHERE name = '{}'""".format("5013f4f9be")
    )
    frappe.db.commit()  # v16: OK - operations script


vec = []
depth = 1
max_depth = 0


def demo111():
    accounts = frappe.db.get_all(
        "Account",
        fields=["name", "is_group", "parent_account"],
        filters={"company": "Hare Krishna Movement Jaipur"},
    )
    final_data = []

    root = "Application of Funds (Assets) - HKMJ"

    def generate_accounts(root):
        if root is None:
            return

        global vec
        global depth
        global max_depth
        vec.append(root)
        depth = depth + 1

        c_accounts = [a["name"] for a in accounts if a["parent_account"] == root]
        if len(c_accounts) == 0:
            fill_data(vec)
            vec.pop()
            depth = depth - 1
            if depth > max_depth:
                max_depth = depth + 1
            return
        else:
            for index, account in enumerate(c_accounts):
                generate_accounts(account)
        vec.pop()
        depth = depth - 1

    root_accounts = []
    for account in accounts:
        if account["parent_account"] is None:
            root_accounts.append(account["name"])

    def fill_data(vec):
        row = []
        for ele in vec:
            row.append(ele)
        final_data.append(row)

    for r_account in root_accounts:
        generate_accounts(r_account)
    # return final_data
    i = 0
    # while i<=max_depth:
    # 	columns.append("D{}".format(i))
    for d in final_data:
        extra = [""] * (max_depth - len(d) + 1)
        d.extend(extra)

    return final_data


# # def make_custom_records():
# 	records = [
# 		{'doctype': "Role", "role_name": "DCC Preacher"},
# 		{'doctype': "Role", "role_name": "DCC Executive"},
# 		{'doctype': "Role", "role_name": "DCC Manager"},
# 		{'doctype': "Role", "role_name": "DCC Cashier"}
# 	]
# 	records.extend(get_states_and_actions())
# 	if not frappe.db.exists("Workflow", "Donation Receipt Workflow"):
# 		records.append(get_workflow())
# 	make_records(records)


# def setup_dhananjaya():
# 	make_custom_records()
# 	make_custom_fields()
# 	frappe.db.commit()
# 	frappe.clear_cache()

# def make_custom_fields(update=True):
# 	custom_fields = get_custom_fields()
# 	create_custom_fields(custom_fields, update=update)


# def get_custom_fields():
# 	custom_fields = {
# 		'Journal Entry':[
# 			dict(fieldname ='donation_receipt', label ='Donation Receipt',
# 					fieldtype='Link',options='Donation Receipt',insert_after='bank_account')
# 		]
# 		# 'Company': [
# 		# 	dict(fieldname='dhananjaya_section', label='Dhananjaya Settings',
# 		# 		 fieldtype='Section Break', insert_after='asset_received_but_not_billed', collapsible=1),
# 		# 	dict(fieldname='dhananjaya_trust_code', label='Old Dhananjaya Trust Code',
# 		# 		 fieldtype='Data', insert_after='dhananjaya_section'),
# 		# 	dict(fieldname='c_80g_number', label='80G Number',
# 		# 		 fieldtype='Data', insert_after='dhananjaya_trust_code'),
# 		# 	dict(fieldname='pan_details', label='PAN Number',
# 		# 		 fieldtype='Data', insert_after='c_80g_number')
# 		# ]
# 	}
# 	return custom_fields

# def get_states_and_actions():
# 	return [
# 		## States ##
# 		{'doctype': "Workflow State", "workflow_state_name": "Light Blue"},
# 		{'doctype': "Workflow State", "workflow_state_name": "Acknowledged","style":"Dark Blue"},
# 		{'doctype': "Workflow State", "workflow_state_name": "Suspense", "style":"Warning"},
# 		{'doctype': "Workflow State", "workflow_state_name": "Received by Cashier", "style":"Success"},
# 		{'doctype': "Workflow State", "workflow_state_name": "Realized", "style":"Success"},
# 		{'doctype': "Workflow State", "workflow_state_name": "Cancelled","style":"Danger"},
# 		## Actions ##
# 		{'doctype': "Workflow Action Master", "workflow_action_name": "Acknowledge"},
# 		{'doctype': "Workflow Action Master", "workflow_action_name": "Receive Cash"},
# 		{'doctype': "Workflow Action Master", "workflow_action_name": "Confirm"},
# 		{'doctype': "Workflow Action Master", "workflow_action_name": "Cancel"},
# 	]
# def get_workflow():
# 	return {
# 				"workflow_name": "Donation Receipt Workflow",
# 				"document_type": "Donation Receipt",
# 				"is_active": 1,
# 				"override_status": 0,
# 				"send_email_alert": 0,
# 				"workflow_state_field": "workflow_state",
# 				"doctype": "Workflow",
# 				"transitions": [
# 									{
# 									"idx": 1,
# 									"state": "Draft",
# 									"action": "Acknowledge",
# 									"next_state": "Acknowledged",
# 									"allowed": "DCC Preacher",
# 									"allow_self_approval": 1,
# 									"condition": "doc.donor",
# 									"parent": "Donation Receipt Workflow",
# 									"parentfield": "transitions",
# 									"parenttype": "Workflow",
# 									"doctype": "Workflow Transition"
# 									},
# 									{
# 									"idx": 2,
# 									"state": "Acknowledged",
# 									"action": "Receive Cash",
# 									"next_state": "Received by Cashier",
# 									"allowed": "DCC Cashier",
# 									"allow_self_approval": 1,
# 									"parent": "Donation Receipt Workflow",
# 									"parentfield": "transitions",
# 									"parenttype": "Workflow",
# 									"doctype": "Workflow Transition"
# 									},
# 									{
# 									"idx": 3,
# 									"state": "Acknowledged",
# 									"action": "Confirm",
# 									"next_state": "Realized",
# 									"allowed": "DCC Executive",
# 									"allow_self_approval": 1,
# 									"parent": "Donation Receipt Workflow",
# 									"parentfield": "transitions",
# 									"parenttype": "Workflow",
# 									"doctype": "Workflow Transition"
# 									},
# 									{
# 									"idx": 4,
# 									"state": "Draft",
# 									"action": "Confirm",
# 									"next_state": "Suspense",
# 									"allowed": "DCC Executive",
# 									"allow_self_approval": 1,
# 									"condition": "not doc.donor",
# 									"parent": "Donation Receipt Workflow",
# 									"parentfield": "transitions",
# 									"parenttype": "Workflow",
# 									"doctype": "Workflow Transition"
# 									}
# 								],
# 				"states": [
# 							{
# 							"idx": 1,
# 							"state": "Draft",
# 							"doc_status": "0",
# 							"is_optional_state": 0,
# 							"allow_edit": "DCC Preacher",
# 							"parent": "Donation Receipt Workflow",
# 							"parentfield": "states",
# 							"parenttype": "Workflow",
# 							"doctype": "Workflow Document State"
# 							},
# 							{
# 							"idx": 2,
# 							"state": "Acknowledged",
# 							"doc_status": "0",
# 							"is_optional_state": 0,
# 							"allow_edit": "DCC Manager",
# 							"parent": "Donation Receipt Workflow",
# 							"parentfield": "states",
# 							"parenttype": "Workflow",
# 							"doctype": "Workflow Document State"
# 							},
# 							{
# 							"idx": 3,
# 							"state": "Received by Cashier",
# 							"doc_status": "1",
# 							"is_optional_state": 0,
# 							"allow_edit": "DCC Manager",
# 							"parent": "Donation Receipt Workflow",
# 							"parentfield": "states",
# 							"parenttype": "Workflow",
# 							"doctype": "Workflow Document State"
# 							},
# 							{
# 							"idx": 4,
# 							"state": "Realized",
# 							"doc_status": "1",
# 							"is_optional_state": 0,
# 							"allow_edit": "DCC Manager",
# 							"parent": "Donation Receipt Workflow",
# 							"parentfield": "states",
# 							"parenttype": "Workflow",
# 							"doctype": "Workflow Document State"
# 							},
# 							{
# 							"idx": 5,
# 							"state": "Suspense",
# 							"doc_status": "1",
# 							"is_optional_state": 0,
# 							"allow_edit": "DCC Manager",
# 							"parent": "Donation Receipt Workflow",
# 							"parentfield": "states",
# 							"parenttype": "Workflow",
# 							"doctype": "Workflow Document State"
# 							},
# 							{
# 							"idx": 6,
# 							"state": "Cancelled",
# 							"doc_status": "2",
# 							"is_optional_state": 0,
# 							"allow_edit": "DCC Manager",
# 							"parent": "Donation Receipt Workflow",
# 							"parentfield": "states",
# 							"parenttype": "Workflow",
# 							"doctype": "Workflow Document State"
# 							}
# 						]
# 			}


def clean_drs_1():
    for dr in frappe.get_all(
        "Donation Receipt",
        filters={"workflow_state": "Realized", "donor": ["is", "not set"]},
        fields=["name", "donor_creation_request"],
    ):
        donors = frappe.get_all(
            "Donor", filters={"donor_creation_request": dr["donor_creation_request"]}
        )
        if donors:
            frappe.db.set_value(
                "Donation Receipt", dr["name"], "donor", donors[0]["name"]
            )
        frappe.db.commit()  # v16: OK - operations script


def get_respective_cost_head(dept):
    chead_map = {
        "Main - SCVT": "D - Basil Woods School",
        "Main - HKMA": "D - Admin",
        "Main - GLF": "D - Admin",
        "Samras Girls Ahmedabad - TSF": "Samras Girls Ahmedabad",
        "GMERS Rajpipla - TSF": "GMERS Rajpipla",
        "GMERS Godhara - TSF": "GMERS Godhara",
        "SRM Gaushala - SF": "D - Temple Gaushala",
        "Madhavas Eco Village - SF": "D - Madhava's Eco Village",
        "Main - SF": "D - Temple Gaushala",
        "FOLK - HKMA": "D - FOLK",
        "FOLK Ahmedabad - HKMA": "FOLK Ahmedabad",
        "FOLK SOCET - HKMA": "FOLK SOCET",
        "FOLK NIRMA - HKMA": "FOLK NIRMA",
        "FOLK PDEU - HKMA": "FOLK PDEU",
        "HKM Surat - HKMA": "HKM Surat Center",
        "Dhamyatra - HKMA": "D - Dham Yatra",
        "BLISS - HKMA": "D - BLISS",
        "BASH - HKMA": "D - BASH",
        "Grihastha - HKMA": "D - Grihastha",
        "FOLK Surat - HKMA": "FOLK Surat",
        "HKM Vadodara - HKMA": "HKM Vadodara Center",
        "FOLK Vadodara - HKMA": "FOLK Vadodara",
        "FOLK Yatra - HKMA": "FOLK Yatras",
        "CVC - HKMA": "D - CVC",
        "Online Presence & Fundraising - HKMA": "D - Online Presence & Fundraising",
        "Dubai Preaching - HKMA": "D - Dubai Preaching",
        "DCC & LLP - HKMA": "D - DCC & LLP",
        "Gaushala - HKMA": "D - Temple Gaushala",
        "Maintenance - HKMA": "D - Maintenance",
        "Guest House - HKMA": "D - Guest House",
        "IT & Graphics - HKMA": "D - IT",
        "Festivals - HKMA": "D - Festivals",
        "Matchless Gift Shop - TSF": "MGS",
        "Store - HKMA": "Store",
        "Capex - HKMA": "D - Maintenance",
        "Construction - TSF": "Projects",
        "FOLK JASD - HKMA": "FOLK Navrangpura",
        "Construction - HKMA": "Projects",
        "Admin - HKMA": "D - Admin",
        "GMERS Porbandar - TSF": "GMERS Porbandar",
        "GMERS Junagadh - TSF": "GMERS Junagadh",
        "Pujari - HKMA": "D - Deity",
        "Dham Yatras - GLF": "D - Dham Yatra",
        "Bakery - GLF": "Bakery",
        "Tribal Kharedi Dahod - TSF": "Tribal Kharedi Dahod",
        "Tribal Limkheda Dahod - TSF": "Tribal Limkheda Dahod",
        "Tribal Lokhadiya Dahod - TSF": "Tribal Lokhadiya Dahod",
        "Tribal Mira Khedi Dahod - TSF": "Tribal Mira Khedi Dahod",
        "Tribal Nani Khajuri Dahod - TSF": "Tribal Nani Khajuri Dahod",
        "Tribal Singvad Dahod - TSF": "Tribal Singvad Dahod",
        "Tribal Usarvan Dahod - TSF": "Tribal Usarvan Dahod",
        "Construction - SF": "Projects",
        "Tribal Bariyani Hathodh Dahod - TSF": "Tribal Bariyani Hathodh Dahod",
        "Samras Boys Bhuj - TSF": "Samras Boys Bhuj",
        "Samras Girls Bhuj - TSF": "Samras Girls Bhuj",
        "BASH - GLF": "D - BASH",
        "Group A - TSF": "Group A",
        "Group B - TSF": "Group B",
        "Samras Hostel - TSF": "Samras Hostel",
        "GMERS - TSF": "GMERS",
        "Tribal - TSF": "Tribal",
        "Vadodara - TSF": "TSF Vadodara",
        "Surat - TSF": "TSF Surat",
        "Bharuch - TSF": "TSF Bharuch",
        "Bhavnagar - TSF": "TSF Bhavnagar",
        "Silvassa - TSF": "TSF Silvassa",
        "Ambaji - TSF": "TSF Ambaji",
        "Temple - TSF": "D - Ashram Kitchen",
        "Prasadam - TSF": "TSF Prasadam",
        "Dahod - TSF": "TSF Dahod",
        "Ahmedabad - AMD - TSF": "TSF Ahmedabad - AMD",
        "Jamnagar GG Hospital - TSF": "TSF Jamnagar GG Hospital",
        "Jamnagar Annapurna - TSF": "TSF Jamnagar Annapurna",
        "GMERS Patan - TSF": "GMERS Patan",
        "FOLK NTSD - HKMA": "FOLK IITGn",
        "Vadodara - Mental Hospital - TSF": "TSF Vadodara - Mental Hospital",
        "Dairy - GLF": "Dairy",
        "Tribal Kesharpura Campus Dahod - TSF": "Tribal Kesharpura Campus Dahod",
        "Tribal Lindatekra Campus Dahod - TSF": "Tribal Lindatekra Campus Dahod",
        "Food Supply - GLF": "TSF Ahmedabad - AMD",
        "GMERS VDR Canteen - GLF": "GMERS Vadodara Canteen",
        "CSR - HKMA": "CSR",
        "HKM Rajkot - HKMA": "HKM Rajkot Center",
        "FOLK Rajkot - HKMA": "FOLK Rajkot",
    }
    return chead_map.get(dept)


def set_pi():
    invoices = frappe.get_all("Purchase Invoice", fields=["name", "cost_center"])
    lth = len(invoices)
    for i, p in enumerate(invoices):

        print(f"Processing {i+1}/{lth} : {p}")

        if p.cost_center:
            frappe.db.set_value(
                "Purchase Invoice",
                p["name"],
                "cost_head",
                get_respective_cost_head(p["cost_center"]),
            )

        for item in frappe.get_all(
            "Purchase Invoice Item",
            filters={"parent": p["name"], "cost_center": ["is", "set"]},
            fields=["name", "cost_center"],
        ):
            frappe.db.set_value(
                "Purchase Invoice Item",
                item["name"],
                "cost_head",
                get_respective_cost_head(item["cost_center"]),
            )

        for tax in frappe.get_all(
            "Purchase Taxes and Charges",
            filters={"parent": p["name"], "cost_center": ["is", "set"]},
            fields=["name", "cost_center"],
        ):
            frappe.db.set_value(
                "Purchase Taxes and Charges",
                tax["name"],
                "cost_head",
                get_respective_cost_head(tax["cost_center"]),
            )

        for gl in frappe.get_all(
            "GL Entry",
            filters={"voucher_no": p["name"], "cost_center": ["is", "set"]},
            fields=["name", "cost_center"],
        ):
            frappe.db.set_value(
                "GL Entry",
                gl["name"],
                "cost_head",
                get_respective_cost_head(gl["cost_center"]),
            )

        frappe.db.commit()  # v16: OK - operations script


def set_sales_invoices():
    invoices = frappe.get_all("Sales Invoice", fields=["name", "cost_center"])
    lth = len(invoices)
    for i, p in enumerate(invoices):

        print(f"Processing {i+1}/{lth} : {p}")

        if p.cost_center:
            frappe.db.set_value(
                "Sales Invoice",
                p["name"],
                "cost_head",
                get_respective_cost_head(p["cost_center"]),
            )

        for item in frappe.get_all(
            "Sales Invoice Item",
            filters={"parent": p["name"], "cost_center": ["is", "set"]},
            fields=["name", "cost_center"],
        ):
            frappe.db.set_value(
                "Sales Invoice Item",
                item["name"],
                "cost_head",
                get_respective_cost_head(item["cost_center"]),
            )

        for tax in frappe.get_all(
            "Sales Taxes and Charges",
            filters={"parent": p["name"], "cost_center": ["is", "set"]},
            fields=["name", "cost_center"],
        ):
            frappe.db.set_value(
                "Sales Taxes and Charges",
                tax["name"],
                "cost_head",
                get_respective_cost_head(tax["cost_center"]),
            )

        for gl in frappe.get_all(
            "GL Entry",
            filters={"voucher_no": p["name"], "cost_center": ["is", "set"]},
            fields=["name", "cost_center"],
        ):
            frappe.db.set_value(
                "GL Entry",
                gl["name"],
                "cost_head",
                get_respective_cost_head(gl["cost_center"]),
            )

        frappe.db.commit()  # v16: OK - operations script


def set_donation_receipts():
    invoices = frappe.get_all("Donation Receipt", fields=["name", "cost_center"])
    lth = len(invoices)
    for i, p in enumerate(invoices):

        print(f"Processing {i+1}/{lth} : {p}")

        if p.cost_center:
            frappe.db.set_value(
                "Donation Receipt",
                p["name"],
                "cost_head",
                get_respective_cost_head(p["cost_center"]),
            )

        for gl in frappe.get_all(
            "GL Entry",
            filters={"voucher_no": p["name"], "cost_center": ["is", "set"]},
            fields=["name", "cost_center"],
        ):
            frappe.db.set_value(
                "GL Entry",
                gl["name"],
                "cost_head",
                get_respective_cost_head(gl["cost_center"]),
            )

        frappe.db.commit()  # v16: OK - operations script


def set_purchase_orders():
    invoices = frappe.get_all("Purchase Order", fields=["name", "cost_center"])
    lth = len(invoices)
    for i, p in enumerate(invoices):

        print(f"Processing {i+1}/{lth} : {p}")

        if p.cost_center:
            frappe.db.set_value(
                "Purchase Order",
                p["name"],
                "cost_head",
                get_respective_cost_head(p["cost_center"]),
            )

        for item in frappe.get_all(
            "Purchase Order Item",
            filters={"parent": p["name"], "cost_center": ["is", "set"]},
            fields=["name", "cost_center"],
        ):
            frappe.db.set_value(
                "Purchase Order Item",
                item["name"],
                "cost_head",
                get_respective_cost_head(item["cost_center"]),
            )

        for tax in frappe.get_all(
            "Purchase Taxes and Charges",
            filters={"parent": p["name"], "cost_center": ["is", "set"]},
            fields=["name", "cost_center"],
        ):
            frappe.db.set_value(
                "Purchase Taxes and Charges",
                tax["name"],
                "cost_head",
                get_respective_cost_head(tax["cost_center"]),
            )

        # for gl in frappe.get_all("GL Entry",filters={"voucher_no":p["name"],"cost_center":["is","set"]},fields=["name","cost_center"]):
        #     frappe.db.set_value("GL Entry",gl["name"],"cost_head",get_respective_cost_head(gl["cost_center"]))

        frappe.db.commit()  # v16: OK - operations script


def set_purchase_receipts():
    invoices = frappe.get_all("Purchase Receipt", fields=["name", "cost_center"])
    lth = len(invoices)
    for i, p in enumerate(invoices):

        print(f"Processing {i+1}/{lth} : {p}")

        if p.cost_center:
            frappe.db.set_value(
                "Purchase Receipt",
                p["name"],
                "cost_head",
                get_respective_cost_head(p["cost_center"]),
            )

        for item in frappe.get_all(
            "Purchase Receipt Item",
            filters={"parent": p["name"], "cost_center": ["is", "set"]},
            fields=["name", "cost_center"],
        ):
            frappe.db.set_value(
                "Purchase Receipt Item",
                item["name"],
                "cost_head",
                get_respective_cost_head(item["cost_center"]),
            )

        for tax in frappe.get_all(
            "Purchase Taxes and Charges",
            filters={"parent": p["name"], "cost_center": ["is", "set"]},
            fields=["name", "cost_center"],
        ):
            frappe.db.set_value(
                "Purchase Taxes and Charges",
                tax["name"],
                "cost_head",
                get_respective_cost_head(tax["cost_center"]),
            )

        for gl in frappe.get_all(
            "GL Entry",
            filters={"voucher_no": p["name"], "cost_center": ["is", "set"]},
            fields=["name", "cost_center"],
        ):
            frappe.db.set_value(
                "GL Entry",
                gl["name"],
                "cost_head",
                get_respective_cost_head(gl["cost_center"]),
            )

        frappe.db.commit()  # v16: OK - operations script


def set_payment_entries():
    invoices = frappe.get_all("Payment Entry", fields=["name", "cost_center"])
    lth = len(invoices)
    for i, p in enumerate(invoices):

        print(f"Processing {i+1}/{lth} : {p}")

        if p.cost_center:
            frappe.db.set_value(
                "Payment Entry",
                p["name"],
                "cost_head",
                get_respective_cost_head(p["cost_center"]),
            )

        # for item in frappe.get_all("Purchase Receipt Item",filters={"parent":p["name"],"cost_center":["is","set"]},fields=["name","cost_center"]):
        #     frappe.db.set_value("Purchase Receipt Item",item["name"],"cost_head",get_respective_cost_head(item["cost_center"]))

        # for tax in frappe.get_all("Advance Taxes and Charges",filters={"parent":p["name"],"cost_center":["is","set"]},fields=["name","cost_center"]):
        #     frappe.db.set_value("Advance Taxes and Charges",tax["name"],"cost_head",get_respective_cost_head(tax["cost_center"]))

        for gl in frappe.get_all(
            "GL Entry",
            filters={"voucher_no": p["name"], "cost_center": ["is", "set"]},
            fields=["name", "cost_center"],
        ):
            frappe.db.set_value(
                "GL Entry",
                gl["name"],
                "cost_head",
                get_respective_cost_head(gl["cost_center"]),
            )

        frappe.db.commit()  # v16: OK - operations script


def set_payment_ledger_entries():
    invoices = frappe.get_all("Payment Ledger Entry", fields=["name", "cost_center"])
    lth = len(invoices)
    for i, p in enumerate(invoices):

        print(f"Processing {i+1}/{lth} : {p}")

        if p.cost_center:
            frappe.db.set_value(
                "Payment Entry",
                p["name"],
                "cost_head",
                get_respective_cost_head(p["cost_center"]),
            )

        # for item in frappe.get_all("Purchase Receipt Item",filters={"parent":p["name"],"cost_center":["is","set"]},fields=["name","cost_center"]):
        #     frappe.db.set_value("Purchase Receipt Item",item["name"],"cost_head",get_respective_cost_head(item["cost_center"]))

        # for tax in frappe.get_all("Advance Taxes and Charges",filters={"parent":p["name"],"cost_center":["is","set"]},fields=["name","cost_center"]):
        #     frappe.db.set_value("Advance Taxes and Charges",tax["name"],"cost_head",get_respective_cost_head(tax["cost_center"]))

        # for gl in frappe.get_all("GL Entry",filters={"voucher_no":p["name"],"cost_center":["is","set"]},fields=["name","cost_center"]):
        #     frappe.db.set_value("GL Entry",gl["name"],"cost_head",get_respective_cost_head(gl["cost_center"]))

        frappe.db.commit()  # v16: OK - operations script


def set_stock_entries():
    invoices = frappe.get_all("Stock Entry", fields=["name", "cost_center"])

    lth = len(invoices)

    for i, p in enumerate(invoices):

        print(f"Processing {i+1}/{lth} : {p}")

        if p.cost_center:
            frappe.db.set_value(
                "Stock Entry",
                p["name"],
                "cost_head",
                get_respective_cost_head(p["cost_center"]),
            )

        for item in frappe.get_all(
            "Stock Entry Detail",
            filters={"parent": p["name"], "cost_center": ["is", "set"]},
            fields=["name", "cost_center"],
        ):
            frappe.db.set_value(
                "Stock Entry Detail",
                item["name"],
                "cost_head",
                get_respective_cost_head(item["cost_center"]),
            )

        # for tax in frappe.get_all("Purchase Taxes and Charges",filters={"parent":p["name"],"cost_center":["is","set"]},fields=["name","cost_center"]):
        #     frappe.db.set_value("Purchase Taxes and Charges",tax["name"],"cost_head",get_respective_cost_head(tax["cost_center"]))

        for gl in frappe.get_all(
            "GL Entry",
            filters={"voucher_no": p["name"], "cost_center": ["is", "set"]},
            fields=["name", "cost_center"],
        ):
            frappe.db.set_value(
                "GL Entry",
                gl["name"],
                "cost_head",
                get_respective_cost_head(gl["cost_center"]),
            )

        frappe.db.commit()  # v16: OK - operations script


def set_journal_entries():

    invoices = frappe.get_all("Journal Entry", fields=["name"])

    lth = len(invoices)

    for i, p in enumerate(invoices):

        print(f"Processing {i+1}/{lth} : {p}")

        # if p.cost_center:
        #     frappe.db.set_value("Journal Entry",p["name"],"cost_head",get_respective_cost_head(p["cost_center"]))

        for item in frappe.get_all(
            "Journal Entry Account",
            filters={"parent": p["name"], "cost_center": ["is", "set"]},
            fields=["name", "cost_center"],
        ):
            frappe.db.set_value(
                "Journal Entry Account",
                item["name"],
                "cost_head",
                get_respective_cost_head(item["cost_center"]),
            )

        # for tax in frappe.get_all("Purchase Taxes and Charges",filters={"parent":p["name"],"cost_center":["is","set"]},fields=["name","cost_center"]):
        #     frappe.db.set_value("Purchase Taxes and Charges",tax["name"],"cost_head",get_respective_cost_head(tax["cost_center"]))

        for gl in frappe.get_all(
            "GL Entry",
            filters={"voucher_no": p["name"], "cost_center": ["is", "set"]},
            fields=["name", "cost_center"],
        ):
            frappe.db.set_value(
                "GL Entry",
                gl["name"],
                "cost_head",
                get_respective_cost_head(gl["cost_center"]),
            )

        frappe.db.commit()  # v16: OK - operations script

    # pis = frappe.db.sql(
    #     """
    #     SELECT tpi.name
    #     FROM `tabPurchase Invoice` tpi
    #     JOIN `tabPurchase Invoice Item` tpii ON tpi.name = tpii.parent
    #     WHERE tpi.docstatus = 1
    #         AND tpi.cost_head IS NOT NULL AND tpii.cost_head IS NULL
    #         AND tpi.posting_date > '2024-04-01'
    #               """,
    #     pluck="name",
    # )

    # unique_pi = set(list(pis))
    # for pi in unique_pi:
    #     if pi in ["HKMJ-PI-2411-00502", "HKMJ-PI-2411-00425"]:
    #         continue
    #     print(f"Processing {pi}")
    #     doc = frappe.get_doc("Purchase Invoice", pi)
    #     for item in doc.items:
    #         if not item.cost_head:
    #             item.cost_head = doc.cost_head
    #     for ti in doc.taxes:
    #         if not ti.cost_head:
    #             ti.cost_head = doc.cost_head
    #     try:
    #         doc.save()
    #     except Exception as e:
    #         print(e)
    #     frappe.db.commit()


def set_costhead_in_se():
    for row in frappe.db.sql(
        """
        SELECT tse.name as se_entry,tgl.name as gl_entry, tse.cost_head
        FROM `tabStock Entry` tse
        JOIN `tabGL Entry` tgl
            ON tgl.voucher_no = tse.name
        WHERE
            tgl.is_cancelled = 0
            AND tgl.account NOT LIKE '%Stock In Hand%'
            AND tgl.cost_head IS NULL
        """,
        as_dict=1,
    ):
        frappe.db.set_value("GL Entry", row["gl_entry"], "cost_head", row["cost_head"])
    frappe.db.commit()  # v16: OK - operations script


def set_purchase_receipt_cost_head():
    prs = frappe.db.sql(
        """
        select tpr.name
        from `tabPurchase Receipt` tpr
        join `tabPurchase Receipt Item` tpri
        on tpr.name = tpri.parent
        where tpr.posting_date >= '2024-04-01'
            and tpri.asset_category is not null
                  """,
        pluck="name",
    )

    unique_prs = list(set(prs))
    for pr in unique_prs:
        print(f"Processing {pr}")
        doc = frappe.get_doc("Purchase Receipt", pr)
        for item in doc.items:
            if not item.cost_head:
                item.cost_head = get_respective_cost_head(doc.department)
        try:
            doc.save()
        except Exception as e:
            print(e)
        frappe.db.commit()  # v16: OK - operations script


def correct_pi_122121():
    entries = frappe.db.sql(
        """
    SELECT tpi.name,tpi.company, tpi.posting_date, count(tgl.name)
    FROM `tabPurchase Invoice` tpi
    LEFT JOIN `tabGL Entry` tgl
        ON tgl.voucher_no = tpi.name AND tgl.is_cancelled = 0
    WHERE tpi.docstatus = 1
    GROUP BY tpi.name
    HAVING COUNT(tgl.name) = 0
    """,
        as_dict=1,
    )
    # print(entries)
    cm_map = {}
    for e in entries:
        if e.company not in cm_map:
            cm_map[e.company] = 0
        cm_map[e.company] += 1
    # unique_companiues = list(set([e.company for e in entries]))
    print(cm_map)

    # for e in entries:
    #     # if e.company != "Hare Krishna Movement Jaipur":
    #     #     continue
    #     print(f"Processing {e.name}")
    #     doc = frappe.get_doc("Purchase Invoice", e.name)
    #     doc.cost_head = None
    #     for item in doc.items:
    #         item.cost_head = None
    #     for ti in doc.taxes:
    #         ti.cost_head = None
    #     doc.save()
    # frappe.db.commit()


def check_cost_head_change():
    headers = [
        "Docname",
        "Company",
        "Supplier",
        "Grand Total",
        "Department",
        "Old Cost Head",
        "New Cost Head",
        "Modified",
    ]
    df = pd.DataFrame(columns=headers)

    from_date = "2025-05-17"
    to_date = "2025-05-22"
    doctype = "Purchase Invoice"

    # Get relevant Version records
    versions = frappe.get_all(
        "Version",
        filters={
            "ref_doctype": doctype,
            "owner": "Administrator",
            "modified": ["between", [from_date, to_date]],
        },
        fields=["name", "data", "docname", "modified"],
    )

    results = []

    for version in versions:
        try:
            version_data = json.loads(version["data"])
            if "changed" in version_data:
                for fieldname, old_val, new_val in version_data["changed"]:
                    if fieldname == "cost_head":
                        company, supplier, grand_total, department = (
                            frappe.db.get_value(
                                doctype,
                                version["docname"],
                                ["company", "supplier", "grand_total", "department"],
                            )
                        )
                        results.append(
                            [
                                version["docname"],
                                company,
                                supplier,
                                grand_total,
                                department,
                                old_val,
                                new_val,
                                version["modified"],
                            ]
                        )
        except Exception as e:
            frappe.log_error(f"Error parsing Version {version['name']}: {str(e)}")

    # Add rows to DataFrame
    for row in results:
        df.loc[len(df)] = row

    # Save to Excel
    df.to_excel("cost_head_change.xlsx", index=False)  # path may vary by server


def check_compatibility():
    entries = frappe.db.sql(
        """
        SELECT tpr.name, COUNT(tgl.name) as entries
        FROM `tabPurchase Invoice` tpr
        JOIN `tabGL Entry` tgl
            ON tpr.name = tgl.voucher_no
        WHERE tpr.docstatus = 1
            AND tpr.posting_date BETWEEN '2024-04-01' AND '2024-04-10'
            AND tgl.cost_head IS NOT NULL
            AND tgl.is_cancelled = 0
            AND tpr.company = "Touchstone Foundation Jaipur"
            AND tgl.account = "Creditors - TSFJ"
        GROUP BY tpr.name
                  """,
        as_dict=1,
    )
    print(len(entries))


@frappe.whitelist(allow_guest=True)
def set_gl_correction():
    data = json.loads(frappe.request.data)
    gl_entries = frappe.get_all(
        "GL Entry",
        filters={
            "voucher_no": data["pi"],
            "account": data["account"],
            "credit": data["credit"],
            "is_cancelled": 0,
        },
        pluck="name",
    )
    if len(gl_entries) != 1:
        frappe.throw("More than one GL Entry found")
    else:
        frappe.db.set_value(
            "GL Entry",
            gl_entries[0],
            "cost_head",
            data["cost_head"],
        )
        frappe.db.commit()  # v16: OK - operations script
        return f"Success : {gl_entries[0]}"


@frappe.whitelist(allow_guest=True)
def set_ple_correction():
    data = json.loads(frappe.request.data)
    ple_entries = frappe.get_all(
        "Payment Ledger Entry",
        filters={
            "voucher_no": data["ple"],
            "account": data["account"],
            "amount": data["amount"],
            "delinked": 0,
        },
        pluck="name",
    )
    if len(ple_entries) != 1:
        frappe.throw("More than one PLE Entry found")
    else:
        frappe.db.set_value(
            "Payment Ledger Entry",
            ple_entries[0],
            "cost_head",
            data["cost_head"],
        )
        frappe.db.commit()  # v16: OK - operations script
        return f"Success : {ple_entries[0]}"


def set_cost_head_in_donation_receipt():
    yatras = [
        "Economy Rampath Yatra 25-30 July 2024",
        "Ayodhya Yatra - 11 to 16 Aug",
        "Economy yatra Dakshin Yatra 15 sep to 27 sep",
        "Jaipur-Karoli Sampurna Darshan Yatra 30th June - 2024",
        "Kartik Ayodhya Yatra 19 oct to 22 oct 2024",
        "GOVERDHAN",
    ]
    cost_head = frappe.get_all(
        "Seva Subtype Defaults",
        filters={
            "parent": ["in", yatras],
            "company": "Sri Radha Krishna Mandir Foundation",
        },
        fields=["parent", "cost_head"],
    )
    cost_head_map = {c["parent"]: c["cost_head"] for c in cost_head}
    for d in frappe.get_all(
        "Donation Receipt",
        filters={
            "seva_subtype": ["in", yatras],
            "cost_head": ["is", "not set"],
            "company": "Sri Radha Krishna Mandir Foundation",
            "docstatus": 1,
        },
        pluck="name",
    ):

        doc = frappe.get_doc("Donation Receipt", d)
        doc.cost_head = cost_head_map.get(doc.seva_subtype)
        try:
            doc.save()
        except Exception as e:
            print(e)
    frappe.db.commit()  # v16: OK - operations script


# def set_donation_receipt_cost_head_correction():
#     yatras = [
#     "Economy Rampath Yatra 25-30 July 2024",
#     "Ayodhya Yatra - 11 to 16 Aug",
#     "Economy yatra Dakshin Yatra 15 sep to 27 sep",
#     "Jaipur-Karoli Sampurna Darshan Yatra 30th June - 2024",
#     "Kartik Ayodhya Yatra 19 oct to 22 oct 2024",
#     "GOVERDHAN"
#     ]
#     # cost_head = frappe.get_all(
#     #     "Seva Subtype Defaults",
#     #     filters={
#     #         "parent": ["in", yatras],
#     #         "company": "Sri Radha Krishna Mandir Foundation",
#     #     },
#     #     fields=["parent", "cost_head"],
#     # )
#     count = 0
#     yatras = ",".join([f"'{_}'" for _ in yatras])
#     for d in frappe.db.sql_list(
#     f"""
#     SELECT name
#     FROM `tabDonation Receipt`
#     WHERE payment_method = 'Cash'
#     AND company = 'Sri Radha Krishna Mandir Foundation'
#     AND docstatus = 1
#     AND modified_by = 'Administrator'
#     AND DATE(modified) = '2025-06-10'
#     AND seva_subtype IN ({yatras})
#     """
#     ):

#         count += 1
#         cost_head = ""
#         doc = frappe.get_doc("Donation Receipt", d)
#         if not frappe.db.exists("GL Entry", {"voucher_no": doc.name, "voucher_type": "Donation Receipt"}):
#             print(f"No GL Entry found for {doc.name}")
#             continue
#         if not doc.payment_method == "Cash":
#             print(f"Payment method is not Cash for {doc.name}")
#             continue
#         data = get_realized_activity(doc.name)
#         if data == get_realized_date(doc.name):
#             try:
#                 frappe.db.set_value(
#                     "Donation Receipt",
#                     doc.name,
#                     "cash_received_date",
#                     data,
#                 )
#                 frappe.db.commit()
#                 doc = frappe.get_doc("Donation Receipt", doc.name)
#                 cost_head = doc.cost_head
#                 doc.cost_head = "YTE017"
#                 doc.save()
#                 doc = frappe.get_doc("Donation Receipt", doc.name)
#                 doc.cost_head = cost_head
#                 doc.save()
#                 frappe.db.commit()
#                 print("Realized activity and date match")
#                 print(cost_head)
#                 if count == 2:
#                     break
#             except Exception as e:
#                 print(e)
#         else:
#             print("Realized activity and date do not match")


# def get_realized_activity(docname):
#     # Check document existence
#     if not frappe.db.exists("Donation Receipt", docname):
#         print(f"Document {docname} does not exist in donation_receipt")
#         return


#     communications = frappe.get_all("Communication",
#         filters={
#             "reference_doctype": "Donation Receipt",
#             "reference_name": docname,
#             "communication_type": "Comment",
#             "content": ["like", "%Received by Cashier%"]
#         },
#         fields=["content", "creation", "owner"],
#         order_by="creation asc"
#     )
#     comments = frappe.get_all("Comment",
#         filters={
#             "reference_doctype": "Donation Receipt",
#             "reference_name": docname,
#             "comment_type": ["in", ["Comment", "Workflow"]],
#             "content": ["like", "%Received by Cashier%"]
#         },
#         fields=["content", "creation", "comment_by"],
#         order_by="creation asc"
#     )


#     if not comments and not communications:
#        # Query tabCommunication for activities mentioning "Realized"
#         communications = frappe.get_all("Communication",
#         filters={
#             "reference_doctype": "Donation Receipt",
#             "reference_name": docname,
#             "communication_type": "Comment",
#             "content": ["like", "%Realized%"]
#         },
#         fields=["content", "creation", "owner"],
#         order_by="creation asc"
#     )

#     # Query tabComment for activities mentioning "Realized"
#         comments = frappe.get_all("Comment",
#         filters={
#             "reference_doctype": "Donation Receipt",
#             "reference_name": docname,
#             "comment_type": ["in", ["Comment", "Workflow"]],
#             "content": ["like", "%Realized%"]
#         },
#         fields=["content", "creation", "comment_by"],
#         order_by="creation asc"
#         )


#     # Print results from Communications
#     if not communications and not comments:
#         print(f"No activities found mentioning 'Realized' for {docname}")
#         return

#     print("Activities in Timeline mentioning 'Realized':")
#     for comm in communications:
#         # Extract only the date from creation
#         date_only = comm.creation.strftime("%Y-%m-%d")
#         print(f"Activity at {date_only} by {comm.owner}: {comm.content}")

#     # Print results from Comments
#     for comment in comments:
#         # Extract only the date from creation
#         date_only = comment.creation.strftime("%Y-%m-%d")
#         print(date_only)
#         return date_only

# def get_realized_date(docname = "RKM-DR2407-0976"):
#     # Verify document existence
#     if not frappe.db.exists("Donation Receipt", docname):
#         print(f"Document {docname} does not exist in Donation Receipt")
#         return

#     # Query Version table for workflow_state changes to "Realized"
#     versions = frappe.get_all("Version",
#         filters={
#             "ref_doctype": "Donation Receipt",
#             "docname": docname
#         },
#         fields=["data", "creation"],
#         order_by="creation asc"
#     )

#     # Check for workflow_state changes to "Realized"
#     realized_date = None
#     for version in versions:
#         changes = frappe.parse_json(version.data)
#         if changes.get("changed"):
#             for field, old_val, new_val in changes["changed"]:
#                 print(field, old_val, new_val)
#                 if (field == "workflow_state" and new_val == "Received by Cashier") or (field == "workflow_state" and new_val == "Realized"):
#                     realized_date = version.creation
#                     break
#         if realized_date:
#             break

#     # Output result
#     if realized_date:
#         # Extract only the date
#         date_only = realized_date.strftime("%Y-%m-%d")
#         print(date_only)
#         return date_only
#     else:
#         print(f"No workflow state change to Realized found for {docname}")


import frappe
from frappe.model.document import Document
from firebase_admin import messaging
from datetime import datetime, timedelta


def send_app_signal():
    tokens = frappe.get_all(
        "Firebase App Token",
        pluck="token",
        filters={"user": "arorapriyanshu33@gmail.com"},
    )
    if tokens:
        message = messaging.MulticastMessage(
            data={
                "action": "Expense Voucher Created",
                "payload": "Expense voucher approval request created by "
                + frappe.session.user,
            },
            tokens=tokens,
            android=messaging.AndroidConfig(
                ttl=timedelta(seconds=3600),
                priority="high",
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(aps=messaging.Aps(content_available=True))
            ),
        )
        fa_doc = frappe.get_doc("Firebase Admin App", "Task Flow")
        response = messaging.send_each_for_multicast(message, app=fa_doc.instance)
        # Convert BatchResponse to a JSON-serializable dictionary
    result = {
        "success_count": response.success_count,
        "failure_count": response.failure_count,
        "responses": [
            {
                "success": r.success,
                "message_id": r.message_id,
                "exception": str(r.exception) if r.exception else None,
            }
            for r in response.responses
        ],
    }
    return result


def move_cost_head():
    doclist = get_doctypes_with_dimensions()
    exclude_doctypes = [
        "Sales Order Item",
        "Opening Invoice Creation Tool",
        "Loyalty Program",
        "Payment Reconciliation",
    ]
    for l in doclist:
        print(f" Processing {l}")
        try:
            frappe.db.sql(
                f"""
                update `tab{l}`
                set cost_head = additional_cost_center
                where additional_cost_center is not null  
                        """
            )
        except Exception as e:
            print(e)


def set_uom_p():
    frappe.db.sql(
        """
        UPDATE `tabItem Price` tip
            JOIN `tabItem` ti
            ON tip.item_code = ti.name
        SET tip.uom = ti.stock_uom
        WHERE tip.uom IS NULL
                  """
    )
    frappe.db.commit()  # v16: OK - operations script


def set_addresses_pin():
    addresses = frappe.db.sql(
        """
        select 
            tda.name as address_id,td.name as donor_id,tda.address_line_1,tda.address_line_2,tda.city,tda.state,tda.country
        from `tabDonor Address` tda
        join `tabDonor` td
        on tda.parent = td.name
        where tda.pin_code is null
        and td.last_donation > now() - interval 6 year    
                  """,
        as_dict=1,
    )
    lth = len(addresses)
    for i, d in enumerate(addresses):
        print(f"Processing {i+1} of {lth} for {d['donor_id']}")
        full_address = f"{d['address_line_1']}, {d['address_line_2']}, {d['city']}, {d['state']}, {d['country']}"
        postal_code = get_postal_code(full_address)
        if postal_code:
            print(f"Setting PINCODE : {postal_code} for {full_address}")
            frappe.db.set_value(
                "Donor Address", d["address_id"], "pin_code", postal_code
            )
            frappe.db.commit()  # v16: OK - operations script


def get_postal_code(address):
    api_key = "AIzaSyCIS0Gs0e6pZY1bQEK-5AGzi3JoYAhuD3w"
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": api_key}

    response = requests.get(base_url, params=params)
    data = response.json()

    if data["status"] == "OK":
        for component in data["results"][0]["address_components"]:
            if "postal_code" in component["types"]:
                return component["long_name"]
        return None
    else:
        return None


ch_map = {
    "Audio Expenses - HKMJ": "Mobile & Sound",
    "Book & Gifts Expenses - HKMJ": "DCC",
    "Cultural Program Expenses - HKMJ": "Pujari",
    "Donor Development Expenses - HKMJ": "DCC",
    "Flowers/Decoration Expenses - HKMJ": "Pujari",
    "Food Distribution Expenses - HKMJ": "DCC",
    "Freight and Forwarding Expenses - HKMJ": "Store",
    "Fuel Expenses - HKMJ": "Vehicle",
    "Gateway Expenses - HKMJ": "DCC",
    "Grocery Expenses - HKMJ": "Ashram Kitchen",
    "Guest Room Expenses - HKMJ": "Guest House",
    "Housekeeping Expenses - HKMJ": "Housekeeping",
    "Kitchen Expenses - HKMJ": "Ashram Kitchen",
    "Labour (Chokti) Expenses - HKMJ": "Civil / Maintainance",
    "Labour Expenses - HKMJ": "Civil / Maintainance",
    "Laundry Expenses - HKMJ": "Guest House",
    "Medical Expenses - HKMJ": "HR",
    "Miscellaneous Expenses - General - HKMJ": "Main",
    "Postage & Courier Expenses - HKMJ": "DCC",
    "Printing and Stationary Expenses - HKMJ": "Graphics",
    "Publicity & Promotion Expenses - HKMJ": "Graphics",
    "Rental Expenses (DG Set) - HKMJ": "Civil / Maintainance",
    "Rental Expenses (IT Devices) - HKMJ": "IT & ERP",
    "Repair & Maintainance (Civil) - HKMJ": "Civil / Maintainance",
    "Repair & Maintainance (Vehicle) - HKMJ": "Vehicle",
    "Repair & Maintenance (IT) - HKMJ": "IT & ERP",
    "Repairs & Maintenance (General) - HKMJ": "Civil / Maintainance",
    "Rounded Off - HKMJ": "Main",
    "Security Expenses - HKMJ": "Security",
    "Staff Welfare Expenses - HKMJ": "HR",
    "Travel Expenses - HKMJ": "Vehicle",
    "Vehicle Hiring Expenses - HKMJ": "Vehicle",
    "Videography/ Photography Expenses - HKMJ": "Media",
    "Water Expenses - HKMJ": "Civil / Maintainance",
    "Youth Programs Expenses - HKMJ": "FOLK Main",
    #   "Stock Received But Not Billed - HKMJ":"Store",
    #   "Stock Received But Not Billed - RKM":"Store",
    #   "Stock Received But Not Billed - TSFJ":"Store"
}


def change_cost_heads():
    vouchers = frappe.db.sql(
        """
                  SELECT voucher_type, voucher_no
                  FROM `tabGL Entry`
                  WHERE cost_head = 'Festival'
                  AND is_cancelled = 0
                  GROUP BY voucher_type,voucher_no
                  """,
        as_dict=1,
    )
    lth = len(vouchers)
    for i, v in enumerate(vouchers):
        if v.voucher_type == "Purchase Invoice":
            doc = frappe.get_doc(v.voucher_type, v.voucher_no)
            approax_ch = "Store"
            for item in doc.items:
                if "Stock Received But Not Billed" not in item.expense_account:
                    approax_ch = ch_map[item.expense_account]
                    break
            try:
                doc.cost_head = approax_ch
                for item in doc.items:
                    item.cost_head = approax_ch
                for ti in doc.taxes:
                    ti.cost_head = approax_ch
                doc.cost_center = "Main - HKMJ"
                doc.save()
                frappe.db.commit()  # v16: OK - operations script
                print(f"Completed {i+1}/{lth}  : {v.voucher_no}")
            except:
                print(f"Failed {i+1}/{lth}  : {v.voucher_no}")
            # break

        if v.voucher_type == "Journal Entry":
            doc = frappe.get_doc(v.voucher_type, v.voucher_no)
            for item in doc.accounts:
                root_type = frappe.db.get_value("Account", item.account, "root_type")
                if root_type == "Expense" and item.cost_head == "Festival":
                    item.cost_head = ch_map[item.account]
                item.cost_center = "Main - HKMJ"
            try:
                doc.save()
                frappe.db.commit()  # v16: OK - operations script
                print(f"Completed JE {i+1}/{lth}  : {v.voucher_no}")
            except:
                print(f"Failed JE {i+1}/{lth}  : {v.voucher_no}")
            # break


def change_cost_heads_je():
    vouchers = frappe.db.sql(
        """
                  SELECT parent
                  FROM `tabJournal Entry Account`
                  WHERE cost_head = 'Festival'
                  AND docstatus = 1
                  GROUP BY parent
                  """,
        pluck="parent",
    )
    for v in vouchers:
        doc = frappe.get_doc("Journal Entry", v)
        for item in doc.accounts:
            root_type = frappe.db.get_value("Account", item.account, "root_type")
            if root_type == "Expense" and item.cost_head == "Festival":
                item.cost_head = ch_map[item.account]
            item.cost_center = "Main - HKMJ"
        try:
            doc.save()
            frappe.db.commit()  # v16: OK - operations script
            print(f"Completed {v}")
        except:
            print(f"Failed {v}")


# def asset_dep_schedule_delete():


def change_site_name_in_files():

    for f in frappe.get_all(
        "File",
        filters={"file_url": ["LIKE", "%erp.harekrishna%"]},
        fields=["name", "file_url"],
    ):
        updated_url = re.sub(
            rf"https://erp.harekrishnamandir.org", f"https://hkmerp.in", f["file_url"]
        )
        frappe.db.set_value("File", f["name"], "file_url", updated_url, modified=False)


def change_expense_head_in_pi():
    JAIPUR_COMPANIES = [
        "Hare Krishna Movement Jaipur",
        "Sri Radha Krishna Mandir Foundation",
        "Touchstone Foundation Jaipur",
    ]
    for company in JAIPUR_COMPANIES:
        company_abbr = frappe.db.get_value("Company", company, "abbr")
        frappe.db.sql(
            """
            UPDATE `tabPurchase Invoice Item` pii
            JOIN `tabPurchase Invoice` pi
            ON pi.name = pii.parent
            JOIN `tabItem` item
            ON item.name = pii.item_code
            SET pii.expense_account = {company_abbr}
            WHERE pi.company = '{company}'
            AND pi.docstatus = 1
            AND item.is_stock_item = 1 
            AND pi.posting_date BETWEEN '2025-04-07' AND '2025-08-18'
            AND pii.expense_account != 'Stock Received But Not Billed - {company_abbr}'
        """.format(
                company_abbr=company_abbr, company=company
            )
        )

        frappe.db.commit()  # v16: OK - operations script


FROM_DATE = "2025-04-01"
TO_DATE = "2025-09-18"


def change_gl_entries_in_pi():
    docs = frappe.get_all(
        "Purchase Invoice",
        filters={
            # "name":"TSFK-PI-2504-00003",
            "docstatus": 1,
            "posting_date": ["between", [FROM_DATE, TO_DATE]],
        },
        fields=["name", "company"],
    )
    for index, pi in enumerate(docs):
        if index < 9359:
            continue
        print(f"Processing {index+1}/{len(docs)}: {pi.name}")
        company_abbr = frappe.get_cached_value("Company", pi.company, "abbr")
        items = frappe.db.get_all(
            "Purchase Invoice Item",
            filters={"parent": pi.name},
            fields=["name", "item_code", "expense_account"],
        )
        for item in items:
            item_type_stock = frappe.db.get_value(
                "Item", item.item_code, "is_stock_item"
            )
            print(item_type_stock)
            if (
                item_type_stock
                and item.expense_account
                != f"Stock Received But Not Billed - {company_abbr}"
            ):
                frappe.db.set_value(
                    "Purchase Invoice Item",
                    item.name,
                    "expense_account",
                    f"Stock Received But Not Billed - {company_abbr}",
                )
        frappe.db.commit()  # v16: OK - operations script

        doc = frappe.get_doc("Purchase Invoice", pi.name)
        frappe.db.delete(
            "GL Entry", filters={"voucher_type": doc.doctype, "voucher_no": doc.name}
        )
        frappe.db.delete(
            "Payment Ledger Entry",
            filters={"voucher_type": doc.doctype, "voucher_no": doc.name},
        )
        doc.force_set_against_expense_account()
        doc.make_gl_entries()


def change_gl_entries_in_purchase_receipts():
    docs = frappe.get_all(
        "Purchase Receipt",
        filters={
            "docstatus": 1,
            "posting_date": ["between", [FROM_DATE, TO_DATE]],
        },
        fields=["name", "company"],
    )

    for index, d in enumerate(docs):
        print(f"Processing {index+1}/{len(docs)}: {d.name}")
        doc = frappe.get_doc("Purchase Receipt", d.name)
        frappe.db.delete(
            "GL Entry", filters={"voucher_type": doc.doctype, "voucher_no": doc.name}
        )
        frappe.db.delete(
            "Payment Ledger Entry",
            filters={"voucher_type": doc.doctype, "voucher_no": doc.name},
        )
        doc.make_gl_entries(from_repost=True)


def change_gl_entries_in_stock_entries():
    docs = frappe.get_all(
        "Stock Entry",
        filters={
            "docstatus": 1,
            "posting_date": ["between", [FROM_DATE, TO_DATE]],
        },
        fields=["name", "company"],
    )

    for index, d in enumerate(docs):
        print(f"Processing {index+1}/{len(docs)}: {d.name}")
        doc = frappe.get_doc("Stock Entry", d.name)
        frappe.db.delete(
            "GL Entry", filters={"voucher_type": doc.doctype, "voucher_no": doc.name}
        )
        doc.make_gl_entries(repost=True)


def revert_approval_matrix_changes_clean():
    """
    Revert Approval Matrix document '4bngsta6s5' to state before today.
    Clears all transitions and rebuilds from scratch to avoid duplicates.
    """
    from frappe.utils import today, get_datetime, now_datetime
    import json
    
    doctype = "Approval Matrix"
    docname = "4bngsta6s5"
    
    # Get today's date at start of day
    today_start = get_datetime(today() + " 00:00:00")
    
    print(f"\n{'='*60}")
    print(f"Reverting {doctype}: {docname} to state before today")
    print(f"{'='*60}\n")
    
    # Check if document exists
    if not frappe.db.exists(doctype, docname):
        print(f"ERROR: Document {docname} does not exist")
        return
    
    # Get all versions for this document
    versions = frappe.get_all(
        "Version",
        filters={"ref_doctype": doctype, "docname": docname},
        fields=["name", "creation", "data", "owner"],
        order_by="creation asc"
    )
    
    if not versions:
        print("ERROR: No version history found")
        return
    
    # Get versions before today
    versions_before_today = [
        v for v in versions 
        if get_datetime(v.creation) < today_start
    ]
    
    if not versions_before_today:
        print("ERROR: No versions found before today. Cannot revert.")
        return
    
    today_versions = [
        v for v in versions 
        if get_datetime(v.creation) >= today_start
    ]
    
    print(f"Total versions: {len(versions)}")
    print(f"Versions before today: {len(versions_before_today)}")
    print(f"Versions today (to be reverted): {len(today_versions)}")
    
    # Load the current document
    doc = frappe.get_doc(doctype, docname)
    print(f"\nCurrent state: {len(doc.transitions)} transitions")
    
    # Reconstruct document state from before today
    # Start with an empty state and apply all versions up to (not including) today
    reconstructed_transitions = []
    
    print(f"\nReconstructing document from {len(versions_before_today)} versions...\n")
    
    # Process each version before today
    for idx, version_data in enumerate(versions_before_today):
        version = frappe.get_doc("Version", version_data.name)
        diff_data = version.get_data()
        
        if not diff_data:
            continue
        
        print(f"  Processing version {idx+1}/{len(versions_before_today)}: {version_data.creation}")
        
        # Apply changed fields
        if "changed" in diff_data:
            for change in diff_data["changed"]:
                if len(change) >= 3:
                    fieldname = change[0]
                    new_value = change[2]  # New value after this change
                    if fieldname not in ["name", "docstatus", "modified", "modified_by"]:
                        doc.set(fieldname, new_value)
        
        # Handle table changes
        # For added rows
        if "added" in diff_data:
            for added in diff_data["added"]:
                if len(added) >= 2:
                    table_fieldname = added[0]
                    row_data = added[1]
                    if table_fieldname == "transitions":
                        reconstructed_transitions.append(row_data)
        
        # For removed rows
        if "removed" in diff_data:
            for removed in diff_data["removed"]:
                if len(removed) >= 2:
                    table_fieldname = removed[0]
                    row_data = removed[1]
                    if table_fieldname == "transitions":
                        # Remove from reconstructed list
                        reconstructed_transitions = [
                            t for t in reconstructed_transitions 
                            if t.get("name") != row_data.get("name")
                        ]
        
        # For row changes
        if "row_changed" in diff_data:
            for row_change in diff_data["row_changed"]:
                if len(row_change) >= 4:
                    table_fieldname = row_change[0]
                    row_name = row_change[2]
                    child_changes = row_change[3]
                    if table_fieldname == "transitions":
                        # Find and update the row in reconstructed list
                        for trans in reconstructed_transitions:
                            if trans.get("name") == row_name:
                                for child_change in child_changes:
                                    if len(child_change) >= 3:
                                        field = child_change[0]
                                        new_val = child_change[2]  # New value after change
                                        trans[field] = new_val
    
    print(f"\nReconstructed state: {len(reconstructed_transitions)} unique transitions")
    
    # Clear all current transitions
    doc.transitions = []
    
    # Add reconstructed transitions (ensuring uniqueness)
    added_count = 0
    for row_data in reconstructed_transitions:
        new_row = doc.append("transitions", {})
        # Set all fields except system fields
        for key, value in row_data.items():
            if key not in ["name", "idx", "owner", "creation", "modified", "modified_by", "docstatus", "parent", "parenttype", "parentfield"]:
                new_row.set(key, value)
        
        # Set dimension_doctype from parent.dimension
        if doc.dimension:
            try:
                dimension_doc = frappe.get_doc("Accounting Dimension", doc.dimension)
                new_row.dimension_doctype = dimension_doc.document_type
            except:
                pass
        
        added_count += 1
    
    print(f"Added {added_count} unique transitions to document")
    
    # Validate before saving
    print("\nValidating document...")
    try:
        doc.validate()
        print("✓ Validation passed")
    except Exception as e:
        print(f"✗ Validation failed: {str(e)}")
        print("\nDocument cannot be saved. Please review manually.")
        return
    
    # Save the document
    print("\nSaving document...")
    doc.flags.ignore_version = True
    doc.save(ignore_permissions=True)
    frappe.db.commit()  # v16: OK - operations script
    
    print(f"\n{'='*60}")
    print(f"✓ Successfully reverted to state before today")
    print(f"  Final state: {len(doc.transitions)} unique transitions")
    print(f"{'='*60}\n")

from india_compliance.gst_india.constants import (
        GST_RCM_TAX_TYPES,
        GST_REFUND_TAX_TYPES,
        GST_TAX_TYPES,
        SALES_DOCTYPES,
        STATE_NUMBERS,
        SUBCONTRACTING_DOCTYPES,
        TAX_TYPES,
        TAXABLE_GST_TREATMENTS,
    )

def change_sl_invoice():
    invoice = "TSFJ-2602-0009"
    irn = frappe.get_value("Sales Invoice", invoice, "irn")
    print(irn)
    # frappe.db.set_value("Sales Invoice",invoice,"docstatus",0)
    doc = frappe.get_doc("Sales Invoice",invoice)
    for item in doc.items:
        item.description += " "
    # update_gst_details(doc)
    doc.irn = irn
    try:
        doc.save()
        doc.submit()
    except Exception as e:
        print(f"Error processing {invoice}: {e}")

def dummy():
    from datetime import datetime
    
    start_time = datetime(2026, 1, 29)
    end_time = datetime(2026, 2, 2)
    
    sales_invoices = frappe.get_all(
        "Sales Invoice",
        filters={
            "creation": ["between", [start_time, end_time]]
        },
        fields=["name", "customer", "posting_date", "grand_total", "creation"],
        order_by="creation desc"
    )
    
    print(f"Found {len(sales_invoices)} sales invoices")
    return
    for invoice in sales_invoices:
        irn = frappe.get_value("Sales Invoice", invoice, "irn")
        print(irn)
        frappe.db.set_value("Sales Invoice",invoice,"docstatus",0)
        doc = frappe.get_doc("Sales Invoice",invoice)
        for item in doc.items:
            item.description += " S"
        # update_gst_details(doc)
        doc.irn = irn
        try:
            doc.save()
            doc.submit()
        except Exception as e:
            print(f"Error processing {invoice}: {e}")



def find_sl_invoices():
    
   
    entries = ["TSF-2502-0022",
"TSF-2502-0021",
"TSF-2502-0020",
"TSF-2501-0242",
"TSF-2501-0241",
"TSF-2501-0239",
"TSF-2501-0238",
"HKMA-2501-0378-1",
"TSF-2501-0240"]
    
    repost_entry = frappe.get_doc({
        "doctype" : "Repost Accounting Ledger",
        "vouchers" : [
            {"voucher_type":"Sales Invoice","voucher_no" : voucher} for voucher in entries],
        "delete_cancelled_entries":1
    })
    repost_entry.insert()
    repost_entry.submit()
    print(entries)
   
    
    


def restore_old_posting_date():
    """Find Sales Invoices that shifted from Cancelled to Draft (via Version history), then repost."""
    

    versions = frappe.db.sql(
        """
        SELECT v.creation, v.docname, v.data
        FROM `tabVersion` v
        JOIN `tabSales Invoice` si ON si.name = v.docname
        WHERE v.ref_doctype = "Sales Invoice"
        AND v.owner = "Administrator"
        AND si.docstatus != 2
        """ , as_dict=1
    )

    # Sales invoices that had status change Cancelled -> Draft
    cancelled_to_draft_invoices = []
    repost_vouchers = []

    for v in versions:
        if not v.get("data") or not v.get("docname"):
            continue
        try:
            data = json.loads(v.data)
        except (TypeError, ValueError):
            continue
        changed = data.get("changed") or []
        for item in changed:
            if len(item) < 3:
                continue
            fieldname, old_val, new_val = item[0], item[1], item[2]
            if fieldname == "status" and old_val == "Cancelled" and new_val == "Draft":
                docname = v.get("docname")
                if docname and docname not in cancelled_to_draft_invoices:
                    cancelled_to_draft_invoices.append(docname)
                break

    repost_vouchers = list(cancelled_to_draft_invoices)
    if not repost_vouchers:
        print("No Sales Invoices found with status change Cancelled -> Draft.")
        return
    print("Sales Invoices (Cancelled -> Draft):", repost_vouchers)

    return

    cancelled_ok = []
    for voucher in repost_vouchers:
        if frappe.db.get_value("Sales Invoice", voucher, "docstatus") == 2:
            continue
        try:
            doc = frappe.get_doc("Sales Invoice", voucher)
            doc.cancel()
            doc.save()
            cancelled_ok.append(voucher)
        except Exception as e:
            print(f"Skip {voucher}: {e}")
            continue

    if not cancelled_ok:
        print("No vouchers were successfully cancelled. Skipping repost.")
        return

    repost_entry = frappe.get_doc({
        "doctype" : "Repost Accounting Ledger",
        "vouchers" : [
            {"voucher_type":"Sales Invoice","voucher_no" : v} for v in cancelled_ok],
        "delete_cancelled_entries":1
    })
    repost_entry.insert()
    repost_entry.submit()
    frappe.db.commit()
    

    for v in cancelled_ok:
        try:
            posting_date,posting_time = frappe.db.get_value("Sales Invoice", v, ["posting_date","posting_time"])
            repost_item_val = frappe.get_doc({
                "doctype" : "Repost Item Valuation",
                "based_on" : "Transaction",
                "posting_date" : posting_date,
                "posting_time" : posting_time,
                "allow_negative_stock":1,
                "recreate_stock_ledgers":1,
                "voucher_type":"Sales Invoice",
                "voucher_no":v
            })
            repost_item_val.insert()
            repost_item_val.submit()
        except Exception as e:
            print(f"Error processing {v}: {e}")
            continue

    print("Processed:", cancelled_ok)
    
def correct_stock_sl_invoices():
    import json
    from datetime import datetime

    start_time = datetime(2026, 2, 1)
    end_time = datetime(2026, 2, 4)

    invoices = frappe.get_all(
        "Sales Invoice",
        filters={
            "modified": ["between", [start_time, end_time]],
            "docstatus": 1
        },
        pluck="name"
    )
    
    

    relevant_invoices = {}

    for invoice in invoices:
        # if invoice != "TSFJ-2501-0294":
        #     continue

        versions = frappe.get_all(
            "Version",
            filters={
                "ref_doctype": "Sales Invoice",
                "docname": invoice,
                "owner": "Administrator"
            },
            fields=["creation", "data"],
            order_by="creation asc"
        )

        for v in versions:
            if not v.data:
                continue

            data = json.loads(v.data)
            changed = data.get("changed") or []

            for field, old, new in changed:
                if field == "posting_date":
                    relevant_invoices[invoice] = old
                    # date_changes.append({
                    #     "invoice": invoice,
                    #     "changed_on": v.creation,
                    #     "old_posting_date": old,
                    #     "new_posting_date": new
                    # })

    # frappe.msgprint(str(date_changes))

    for ri, invoice in enumerate(relevant_invoices):
        # print(f"Processing {ri+1}/{len(relevant_invoices)}: {invoice}")
        doc = frappe.get_doc("Sales Invoice", invoice)
        # if doc.name != "HKMA-2502-0025":
        #     continue
        if date_diff(doc.due_date, doc.posting_date) < 0:
            print(f"{invoice} | Due Date : {doc.due_date} | Posting Date : {doc.posting_date}")
            print("Due Date is less than Posting Date")
            doc.posting_date = doc.due_date
            doc.save()
        if doc.due_date == doc.posting_date:
            relevant_invoices.append(invoice)
    

  
    repost_entry = frappe.get_doc({
        "doctype" : "Repost Accounting Ledger",
        "vouchers" : [
            {"voucher_type":"Sales Invoice","voucher_no" : voucher} for voucher in repost_vouchers],
        "delete_cancelled_entries":1
    })
    repost_entry.insert()
    repost_entry.submit()

    for v in repost_vouchers:
        posting_date,posting_time = frappe.db.get_value("Sales Invoice", v, ["posting_date","posting_time"])
        repost_item_val = frappe.get_doc({
            "doctype" : "Repost Item Valuation",
            "based_on" : "Transaction",
            "posting_date" : posting_date,
            "posting_time" : posting_time,
            "allow_negative_stock":1,
            "recreate_stock_ledgers":1,
            "voucher_type":"Sales Invoice",
            "voucher_no":v
        })
        repost_item_val.insert()
        repost_item_val.submit()



from frappe.utils import date_diff
def correct_sl_invoices():
    from datetime import datetime

    start_time = datetime(2026, 2, 2)
    end_time = datetime(2026, 2, 2)
    invoices = frappe.get_all("Sales Invoice",
        filters={
            "modified": [">=", "2026-02-02"],
            "docstatus": 1
        }, 
        pluck="name")

    relevant_invoices = []

    for index, invoice in enumerate(invoices):
        # if index > 5:
        #     break
        
        # print(f"Processing {index+1}/{len(invoices)}: {invoice}")
        versions = frappe.get_all(
            "Version",
            filters={"ref_doctype": "Sales Invoice", "docname": invoice},
            fields=["name", "creation", "data", "owner"],
            order_by="creation asc"
        )
        for v in versions:
            if v["owner"] != "Administrator":
                continue
            data = json.loads(v["data"])
            if ['docstatus', 0, 1] in data['changed']:
                relevant_invoices.append(invoice)
                break
    repost_vouchers = []
    for ri, invoice in enumerate(relevant_invoices):
        # print(f"Processing {ri+1}/{len(relevant_invoices)}: {invoice}")
        doc = frappe.get_doc("Sales Invoice", invoice)
        # if doc.name != "HKMA-2502-0025":
        #     continue
        if date_diff(doc.due_date, doc.posting_date) < 0:
            print(f"{invoice} | Due Date : {doc.due_date} | Posting Date : {doc.posting_date}")
            print("Due Date is less than Posting Date")
            doc.posting_date = doc.due_date
            doc.save()
        if doc.due_date == doc.posting_date:
            repost_vouchers.append(invoice)
    

    print(repost_vouchers)
    return
    repost_entry = frappe.get_doc({
        "doctype" : "Repost Accounting Ledger",
        "vouchers" : [
            {"voucher_type":"Sales Invoice","voucher_no" : voucher} for voucher in repost_vouchers],
        "delete_cancelled_entries":1
    })
    repost_entry.insert()
    repost_entry.submit()

    for v in repost_vouchers:
        posting_date,posting_time = frappe.db.get_value("Sales Invoice", v, ["posting_date","posting_time"])
        repost_item_val = frappe.get_doc({
            "doctype" : "Repost Item Valuation",
            "based_on" : "Transaction",
            "posting_date" : posting_date,
            "posting_time" : posting_time,
            "allow_negative_stock":1,
            "recreate_stock_ledgers":1,
            "voucher_type":"Sales Invoice",
            "voucher_no":v
        })
        repost_item_val.insert()
        repost_item_val.submit()
            
            
            


        


from india_compliance.gst_india.overrides.transaction import (
        DOCTYPES_WITH_GST_DETAIL,
        ItemGSTDetails,
        ItemGSTTreatment,
        validate_item_tax_template,
    )
def update_gst_details(doc, method=None):
    ItemGSTTreatment().set(doc)
    if doc.doctype in DOCTYPES_WITH_GST_DETAIL:
        ItemGSTDetails().update(doc)
        # validate_item_tax_template(doc)



# def test_pos_closing_entry():
#     pos_closing_entry = frappe.get_doc("POS Closing Entry", "POS-CLO-2026-00397")
#     pos_closing_entry.submit()
#     return