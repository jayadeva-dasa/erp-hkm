import re
import frappe
from dhananjaya.dhananjaya.api.v3.marketing.identify import identify_donor
from frappe.utils import validate_email_address

# Define pre-declared variables for dictionary keys
F_DONATION = "donation"
F_PREACHER = "preacher"
F_DEFAULT_MARKETING_PREACHER = "default_marketing_preacher"
F_PAN_NO = "pan_no"
F_AADHAR_NO = "aadhar_no"
F_MOBILE = "mobile"
F_DONOR_NAME = "donor_name"
F_ADDRESS = "address"
F_EMAIL = "email"
F_COMPANY = "company"
F_DATE = "date"
F_PAYMENT_METHOD = "payment_method"
F_AMOUNT = "amount"
F_REMARKS = "remarks"
F_SEVA_TYPE = "seva_type"
F_SEVA_SUBTYPE = "seva_subtype"
F_DR_NO = "dr_no"
F_ADDITIONAL_CHARGES = "additional_charges"
F_PRINT_REMARKS_ON_RECEIPT = "print_remarks_on_receipt"
F_ATG_REQUIRED = "atg_required"


# @frappe.whitelist(methods=["POST"])
def new_general_receipt(donation_raw):
    if not donation_raw.get("mobile", ""):
        return

    # validate(donation_raw)

    # Preacher Identify
    try:
        donation_raw[F_PREACHER] = donation_raw.get(F_PREACHER).strip()
        preacher = frappe.get_doc("LLP Preacher", donation_raw[F_PREACHER]).name
    except:
        preacher = frappe.db.get_single_value(
            "Dhananjaya Settings", F_DEFAULT_MARKETING_PREACHER
        )
        if preacher is None:
            frappe.throw(
                "Please set the default Marketing Preacher in Dhananajaya Settings first."
            )

    clean_contact = re.sub(r"\D", "", str(donation_raw.get(F_MOBILE, "")))[-10:]
    clean_email = None
    if "email" in donation_raw:
        rec_email = donation_raw.get(F_EMAIL, "")
        clean_email = rec_email if valid_email(rec_email) else None
        # except:
        # print(donation_raw.get(F_EMAIL, ""))
        # clean_email = None
    clean_pan = None
    if donation_raw.get(F_PAN_NO, ""):
        clean_pan = re.sub(r"\s+", "", donation_raw.get(F_PAN_NO, ""))
        if len(clean_pan) != 10:
            clean_pan = None

    donor = identify_donor(contact=clean_contact, email=None, pan=None, aadhar=None)

    if donor is None:
        donor_dict = {
            "doctype": "Donor",
            "first_name": donation_raw.get(F_DONOR_NAME),
            "llp_preacher": preacher,
        }

        if donation_raw.get("address") and donation_raw.get("address") != "\n":
            donor_dict.update(
                {
                    "addresses": [
                        {
                            "address_line_1": donation_raw.get("address")[:135],
                            "pin_code": donation_raw.get("pincode"),
                        }
                    ]
                }
            )

        if clean_email:
            donor_dict.update({"emails": [{"email": clean_email}]})

        if clean_contact:
            donor_dict.update({"contacts": [{"contact_no": clean_contact}]})

        if clean_pan:
            donor_dict.update({"pan_no": clean_pan})
        donor_doc = frappe.get_doc(donor_dict)

        donor_doc.insert(ignore_permissions=True)

        donor = donor_doc.name

    # Upload Receipt
    llp_preacher = frappe.db.get_value("Donor", donor, "llp_preacher")

    receipt_dict = {
        "doctype": "Donation Receipt",
        "company": donation_raw.get(F_COMPANY),
        "receipt_date": donation_raw.get(F_DATE),
        "realization_date": donation_raw.get(F_DATE),
        "preacher": llp_preacher,
        "donor": donor,
        "full_name": donation_raw["donor_name"],
        "contact": clean_contact,
        "address": donation_raw.get(F_ADDRESS),
        "payment_method": donation_raw.get(F_PAYMENT_METHOD),
        "amount": donation_raw.get(F_AMOUNT),
        "remarks": donation_raw.get(F_REMARKS),
        "user_remarks": donation_raw.get("user_remarks"),
        "seva_type": donation_raw.get(F_SEVA_TYPE),
        "seva_subtype": donation_raw.get(F_SEVA_SUBTYPE),
        "old_dr_no": donation_raw.get(F_DR_NO),
        # "additional_charges": donation_raw.get(F_ADDITIONAL_CHARGES),
        # "print_remarks_on_receipt": donation_raw.get(F_PRINT_REMARKS_ON_RECEIPT),
        # "atg_required": donation_raw.get(F_ATG_REQUIRED),
        "auto_generated": 1,
    }

    receipt_doc = frappe.get_doc(receipt_dict)
    receipt_doc.insert(ignore_permissions=True, ignore_links=True)

    # receipt_doc.db_set("workflow_state", "Acknowledged")
    # receipt_doc.db_set("docstatus", 0)

    # defaults = get_company_defaults(donation_raw.get(F_COMPANY))

    # if not defaults.auto_create_journal_entries:
    if donation_raw[F_PAYMENT_METHOD] == "Cash":
        receipt_doc.db_set("workflow_state", "Received by Cashier")
    else:
        receipt_doc.db_set("workflow_state", "Realized")

    receipt_doc.db_set("docstatus", 1)

    frappe.db.commit()  # v16: OK - operations script

    # receipt_token = encode_donation_id(receiptId=receipt_doc.name)

    # long_url = (
    #     "https://"
    #     + frappe.local.site
    #     + f"/api/method/dhananjaya.dhananjaya.utils.download_pdf_public?receiptToken={receipt_token}"
    # )

    # return frappe._dict(url=long_url)


# COMPULSORY_FIELDS = [
#     F_MOBILE,
#     F_DONOR_NAME,
#     # F_ADDRESS,
#     F_COMPANY,
#     F_DATE,
#     F_PAYMENT_METHOD,
#     # F_AMOUNT,
#     F_SEVA_TYPE,
# ]


# def validate(donation_raw):
#     for cf in COMPULSORY_FIELDS:
#         if not donation_raw.get(cf):
#             frappe.throw(f"API Request is incomplete. {cf} is a compulsory field.")
#     return


def valid_email(address):
    valid_email_regex = "^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$"
    if not re.search(valid_email_regex, address):
        return False
    return True
