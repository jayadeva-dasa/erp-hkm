import json, re
import frappe
import dhananjaya.dhananjaya.doctype.dhananjaya_import_settings.constant_maps as maps
from frappe.utils import validate_email_address


@frappe.whitelist()
def upload_preachers():
    preachers = json.loads(frappe.request.data)
    for p in preachers:
        if not frappe.db.exists("LLP Preacher", p):
            doc = frappe.get_doc(
                {"doctype": "LLP Preacher", "full_name": p, "initial": p}
            )
            doc.insert()
    return


@frappe.whitelist()
def upload_address_states():
    states = json.loads(frappe.request.data)
    for s in states:
        if not frappe.db.exists("Donor Address State", s):
            doc = frappe.get_doc({"doctype": "Donor Address State", "title": s})
            doc.insert()
    return


@frappe.whitelist()
def upload_countries():
    countries = json.loads(frappe.request.data)
    for s in countries:
        if not frappe.db.exists("Country", s):
            doc = frappe.get_doc({"doctype": "Country", "country_name": s})
            doc.insert()
    return


@frappe.whitelist()
def upload_salutations():
    salutations = json.loads(frappe.request.data)
    for s in salutations:
        if not frappe.db.exists("Salutation", s):
            doc = frappe.get_doc({"doctype": "Salutation", "salutation": s})
            doc.insert()
    return


@frappe.whitelist()
def upload_donors():
    donor_chunk = json.loads(frappe.request.data)
    ind = 0
    for ind, d in enumerate(donor_chunk):
        if frappe.db.exists("Donor", {"old_donor_id": d["DONOR_ID"],"old_trust_code":d["TRUST_ID"]}):
            continue
        frappe.enqueue(
            insert_a_donor,
            queue="short",
            job_name="Inserting Donor",
            timeout=100000,
            d=d,
        )
        ind += 1


def insert_a_donor(d):
    doc = frappe.new_doc("Donor")
    doc.old_donor_id = d["DONOR_ID"]
    doc.old_trust_code = d["TRUST_ID"]
    doc.salutation = d["SALUTATION"]
    doc.first_name = d["FIRST_NAME"]
    doc.last_name = d["LAST_NAME"]
    doc.spouse_name = d["SPOUSE_NAME"]
    if d["DATE_OF_BIRTH"]:
        doc.date_of_birth = d["DATE_OF_BIRTH"]
    doc.llp_preacher = d["PREACHER_CODE"]

    contact_nos = []
    emails = []

    mail_pref = None
    if d["MAILING_PREF"] in ["O", "R"]:
        mail_pref = "RES" if d["MAILING_PREF"] == "R" else "OFF"
    for atype in maps.ADDRESS_TYPES:
        if (
            d.get(f"{atype}_ADDR_LINE_1")
            and (str(d.get(f"{atype}_ADDR_LINE_1")) or "").strip()
        ):
            doc.append(
                "addresses",
                {
                    "preferred": 1 if (atype == mail_pref) else 0,
                    "type": maps.ADDRESS_TYPES[f"{atype}"],
                    "address_line_1": (d.get(f"{atype}_ADDR_LINE_1") or "")
                    + (d.get(f"{atype}_ADDR_LINE_2") or "")
                    or "",
                    "address_line_2": (d.get(f"{atype}_ADDR_LINE_3") or "")
                    + (d.get(f"{atype}_ADDR_LINE_4") or "")
                    or "",
                    "city": d.get(f"{atype}_CITY") or "",
                    "state": get_state(d[f"{atype}_STATE"]),
                    "country": d[f"{atype}_COUNTRY"],
                    "pin_code": d[f"{atype}_PINCODE"]
                    if (d[f"{atype}_PINCODE"] and is_valid_pin(d[f"{atype}_PINCODE"]))
                    else None,
                },
            )
        if d[f"{atype}_PHONE"] is not None:
            if not isinstance(d[f"{atype}_PHONE"], str):
                d[f"{atype}_PHONE"] = str(d[f"{atype}_PHONE"])
            if d[f"{atype}_PHONE"].strip():
                contact_nos.append(d[f"{atype}_PHONE"])
    contact_nos.append(d["MOBILE_1"])
    contact_nos.append(d["MOBILE_2"])
    contact_nos.append(d["PHONE_1"])
    contact_nos.append(d["PHONE_2"])
    if not isinstance(d["EMAIL_1"], str):
        d["EMAIL_1"] = str(d["EMAIL_1"])
    if not isinstance(d["EMAIL_2"], str):
        d["EMAIL_2"] = str(d["EMAIL_2"])
    emails.append(validate_email_address(d["EMAIL_1"]))
    emails.append(validate_email_address(d["EMAIL_2"]))
    contact_nos = list(
        set(
            [
                str(x).replace(" ", "")
                for x in contact_nos
                if (x is not None and str(x).strip() != "")
            ]
        )
    )
    emails = list(
        set(
            [
                str(x).replace(" ", "")
                for x in emails
                if (x is not None and str(x).strip() != "")
            ]
        )
    )

    for contact in contact_nos:
        doc.append("contacts", {"contact_no": contact})
    for email in emails:
        doc.append("emails", {"email": email})
    fax_data_resolver(d, doc)
    try:
        doc.insert(
            ignore_links=True,
        )
    except frappe.exceptions.ValidationError:
        doc.pan_no = None
        doc.insert(
            ignore_links=True,
        )


def fax_data_resolver(val, doc):
    if val["PAN_NUMBER"] is None:
        return
    if val["PAN_NUMBER"] is not None and val["PAN_NUMBER"].strip() != "":
        doc.pan_no = val["PAN_NUMBER"]
    elif re.search("pan", val["FAX_NUMBER"], re.IGNORECASE):
        s = re.sub("[PpAaNn].*[NnOo].*-", "", val["FAX_NUMBER"])
        s = re.sub("[\s\W]", "", s)
        doc.pan_no = s
    elif re.search("AADHAR", val["FAX_NUMBER"], re.IGNORECASE):
        s = re.sub("[AADHARaadhar]\D", "", val["FAX_NUMBER"])
        s = re.sub("[\s\W]", "", s)
        doc.aadhar_no = s
    else:
        doc.unresolved_fax_column = val["FAX_NUMBER"]


def get_state(val):
    if val is None:
        return None
    if not isinstance(val, str):
        val = str(val)
    return val
    # if val.title() in maps.STATES:
    #     return val.title()
    # return None


def is_valid_pin(pin):
    if not isinstance(pin, str):
        pin = str(pin)
    # Remove any extra spaces
    pin = pin.replace(" ", "")

    if len(pin) != 6:
        return False
    if not pin.isdigit():
        return False
    if int(pin[0]) not in range(1, 10):
        return False
    return True
