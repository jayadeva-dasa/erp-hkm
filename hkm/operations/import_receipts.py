import frappe
import re, json
from frappe.utils import validate_email_address, getdate
import dhananjaya.dhananjaya.doctype.dhananjaya_import_settings.constant_maps as maps
from dhananjaya.dhananjaya.doctype.dhananjaya_import_settings.utils import run_query
from datetime import datetime, timedelta
from frappe.model.workflow import apply_workflow


@frappe.whitelist()
def import_mode_of_payment():
    modes = json.loads(frappe.request.data)
    for d in modes:
        if not frappe.db.exists("DJ Mode of Payment", {"mode": d}):
            doc = frappe.get_doc(
                {"doctype": "DJ Mode of Payment", "enabled": 1, "mode": d}
            )
            doc.insert()
    return


@frappe.whitelist()
def upload_mode_of_payment():
    seva_types = json.loads(frappe.request.data)
    for s in seva_types:
        if not frappe.db.exists("Patron Seva Type", {"seva_code": s["SEVA_CODE"]}):
            doc = frappe.get_doc(
                {
                    "doctype": "Patron Seva Type",
                    "enabled": 1,
                    "seva_code": s["SEVA_CODE"],
                    "seva_name": s["SEVA_NAME"],
                    "seva_amount": s["SEVA_AMOUNT"],
                }
            )
            doc.insert()
    return


# @frappe.whitelist()
# def import_sevas(*args, **kwargs):
#     companies = {}
#     settings = frappe.get_cached_doc("Dhananjaya Import Settings")
#     for c in settings.companies_to_import:
#         companies.setdefault(c.old_trust_code, c.company)

#     data = run_query(
#         "select distinct TRUST_ID, DONATION_CODE from view_receipt_details"
#     )
#     for d in data:
#         if d["DONATION_CODE"] and d["TRUST_ID"] in companies:
#             seva_type = frappe.get_doc(
#                 doctype="Seva Type",
#                 seva_name=d["DONATION_CODE"],
#                 company=companies[d["TRUST_ID"]],
#             )
#             seva_type.insert(ignore_if_duplicate=True)


# @frappe.whitelist()
# def import_subsevas(*args, **kwargs):
#     data = run_query("select distinct SEVA_CODE from view_receipt_details")
#     for d in data:
#         if d["SEVA_CODE"]:
#             seva_subtype = frappe.get_doc(
#                 doctype="Seva Subtype", enabled=1, seva_name=d["SEVA_CODE"]
#             )
#             seva_subtype.insert(ignore_if_duplicate=True)


@frappe.whitelist()
def import_receipts():
    receipts = json.loads(frappe.request.data)
    companies_trust_code = {
        "200": "Hare Krishna Movement Vrindavan",
        "201": "Vrindavan Chandrodaya Mandir Trust",
    }

    donors = frappe.db.sql(
        """
                select old_trust_code,old_donor_id,name
                from `tabDonor`
                where 1
                """
    )
    patrons = frappe.db.sql(
        """
                select old_trust_code,old_patron_id,name
                from `tabPatron`
                where 1
                """
    )
    donor_map = {f"{r[0]}{r[1]}": str(r[2]) for r in donors}
    patron_map = {f"{r[0]}{r[1]}": str(r[2]) for r in patrons}
    for ind, r in enumerate(receipts):
        try:
            donor_id = donor_map[f"{r['TRUST_ID']}{r['DONOR_ID']}"]
        except:
            alternate = "201" if r["TRUST_ID"] == "200" else "200"
            donor_id = donor_map[f"{alternate}{r['DONOR_ID']}"]
        patron_id = None
        if r["PATRON_ID"]:
            patron_id = patron_map[f"{r['TRUST_ID']}{r['PATRON_ID']}"]
        # if not frappe.db.exists(
        #     "Donation Receipt",
        #     {
        #         "old_dr_no": r["DR_NUMBER"],
        #         "company": companies_trust_code[r["TRUST_ID"]],
        #     },
        # ):
        if r["PAYMENT_STATUS"] in ["TS", "ST"]:
            insert_a_receipt(
                r,
                donor_id=donor_id,
                company_trust=companies_trust_code,
                patron_id=patron_id,
            )
            # frappe.enqueue(
            #     insert_a_receipt,
            #     queue="short",
            #     job_name="Inserting Receipt",
            #     timeout=100000,
            #     r=r,
            #     erp_id=id,
            #     company_trust=companies_trust_code,
            # )
        elif r["PAYMENT_STATUS"] == "CL":
            insert_a_receipt(
                r,
                donor_id=donor_id,
                company_trust=companies_trust_code,
                patron_id=patron_id,
                status="Realized",
            )
            # frappe.enqueue(
            #     insert_a_receipt,
            #     queue="short",
            #     job_name="Inserting Receipt",
            #     timeout=100000,
            #     r=r,
            #     erp_id=id,
            #     company_trust=companies_trust_code,
            #     status="Realized",
            # )
        elif r["PAYMENT_STATUS"] == "BD":
            insert_a_receipt(
                r,
                donor_id=donor_id,
                company_trust=companies_trust_code,
                patron_id=patron_id,
                status="Cancelled",
            )
            # frappe.enqueue(
            #     insert_a_receipt,
            #     queue="short",
            #     job_name="Inserting Receipt",
            #     timeout=100000,
            #     r=r,
            #     erp_id=id,
            #     company_trust=companies_trust_code,
            #     status="Cancelled",
            # )


# In Realised Stage
def insert_a_receipt(r, donor_id, company_trust, patron_id, status=None):
    doc = frappe.new_doc("Donation Receipt")

    doc.company = company_trust[r["TRUST_ID"]]
    doc.company_abbreviation = frappe.get_cached_value("Company", doc.company, "abbr")
    doc.donor = donor_id
    if patron_id:
        doc.patron = patron_id
    doc.old_dr_no = r["DR_NUMBER"]
    doc.receipt_date = getdate(r["DR_DATE"])
    doc.amount = r["INS_AMOUNT"]
    doc.payment_method = r["PAYMENT_MODE"]
    ### Dyanamic Seva Type ###
    doc.seva_type = r["DONATION_CODE"]  ##+ " - " + company_trust[r["TRUST_ID"]]["abbr"]

    doc.seva_subtype = r["SEVA_CODE"]
    doc.preacher = r["PREACHER_CODE"]
    doc.remarks = r["DR_REMARKS"]

    # Cheque Details
    if r["PAYMENT_MODE"] == "CQ":
        doc.cheque_number = r["INS_NUMBER"]
        doc.cheque_date = getdate(r["PRESENTATION_DATE"])
        doc.bank_name = r["INS_BANK"]

    # OLD DATA
    doc.old_ar_no = r["AR_NUMBER"]
    doc.old_ar_date = getdate(r["AR_DATE"])
    doc.old_ins_bank = r["INS_BANK"]
    doc.old_ins_account_number = r["INS_ACCOUNT_NUMBER"]
    doc.old_ins_number = r["INS_NUMBER"]
    doc.old_ins_date = getdate(r["INS_DATE"])

    doc.insert(ignore_permissions=True, ignore_links=True, ignore_mandatory=True)
    if status is not None:
        # apply_workflow(doc, status)
        if status == "Cancelled":
            doc.db_set("docstatus", 2)
            doc.db_set("workflow_state", status)
        else:
            doc.db_set("docstatus", 1)
            if r["PAYMENT_MODE"] == "CH":
                doc.db_set("workflow_state", "Received by Cashier")
            else:
                doc.db_set("workflow_state", "Realized")
    else:
        doc.db_set("workflow_state", "Acknowledged")
    frappe.db.commit()  # v16: OK - operations script
