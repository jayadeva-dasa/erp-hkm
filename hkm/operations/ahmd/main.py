# from dhananjaya.api.v3.marketing.identify import identify_donor
from hkm.operations.ahmd.old_db import run_query
from hkm.operations.ahmd.queries import (
    fetch_donor_query,
    seva_subtype_fetch,
    upload_receipts_query,
    patron_seva_ids,
    festival_parent_ids,
    relation_company_patron,
    avoid_to_make_patrons,
    upload_general_receipts_query,
)
from hkm.operations.ahmd.new_receipt_donor import new_general_receipt
import frappe
import json, requests, re
from frappe.utils.file_manager import save_file
from pathlib import Path

DOMAIN = "https://hkm-tapf.azurewebsites.net"


def upload_preachers():
    users = run_query("SELECT * FROM `users` WHERE 1")
    for u in users:
        if not frappe.db.exists("User", u["email"]):
            doc = frappe.get_doc(
                {"doctype": "User", "first_name": u["name"], "email": u["email"]}
            )
            doc.insert()
        else:
            doc = frappe.get_doc("User", u["email"])

        if u["profile"]:
            public_image_url = f"{DOMAIN}{u['profile']}"
            response = requests.get(public_image_url)
            file_doc = save_file(
                f"{u['code']}_profile.jpg",
                response.content,
                "User",
                doc.name,
                None,
                is_private=0,
                df="user_image",
            )
            doc.user_image = file_doc.file_url
        doc.save()

        # LLP Preacher Creation

        if not frappe.db.exists("LLP Preacher", u["code"]):
            doc = frappe.get_doc(
                {
                    "doctype": "LLP Preacher",
                    "full_name": u["name"],
                    "initial": u["code"],
                    "whatsapp_no": u["phone"],
                    "allowed_users": [{"user": u["email"]}],
                }
            )
            doc.insert()
    frappe.db.commit()  # v16: OK - operations script


def upload_salutations():
    salutations = run_query("SELECT name FROM `salutations` WHERE 1")
    for s in salutations:
        if not frappe.db.exists("Salutation", s["name"]):
            doc = frappe.get_doc({"doctype": "Salutation", "salutation": s["name"]})
            doc.insert()
    frappe.db.commit()  # v16: OK - operations script


def upload_countries():
    countries = run_query("SELECT * FROM `countries` WHERE 1")
    for c in countries:
        if not frappe.db.exists("Country", c["country_name"]):
            doc = frappe.get_doc(
                {
                    "doctype": "Country",
                    "country_name": c["country_name"],
                    "code": c["country_code"].lower(),
                }
            )
            doc.insert()
    frappe.db.commit()  # v16: OK - operations script


def set_patron_levels():
    levels = run_query(
        """
            SELECT name,amount
            FROM sevas
            WHERE is_benefits_to_patron = 1
                """
    )
    for l in levels:
        doc = frappe.get_doc(
            {
                "doctype": "Patron Seva Type",
                "seva_code": l["name"],
                "seva_name": l["name"],
                "seva_amount": l["amount"],
            }
        )
        doc.insert()
    frappe.db.commit()  # v16: OK - operations script


def upload_donors():
    # ## Temp
    # dids = list(relation_company_patron.values())
    # ## Temp
    donors = run_query(fetch_donor_query)
    length = len(donors)
    for index, d in enumerate(donors):
        # if index < 8643:
        #     continue
        # if d["old_donor_id"] != "69":
        #     continue
        # ## Temp
        # # print(d["old_donor_id"])
        # if str(d["old_donor_id"]) not in dids:
        #     continue
        # ## Temp
        if frappe.db.exists("Donor", {"old_donor_id": d["old_donor_id"]}):
            continue
        try:
            print("------------")
            print("------------")
            print(f"Running Donor Upload Task {index+1}/{length}")
            document_dict = {
                "doctype": "Donor",
                "salutation": d["salutation"],
                "first_name": d["first_name"],
                "last_name": d["last_name"],
                "date_of_birth": d["date_of_birth"],
                "llp_preacher": d["llp_preacher"],
                "pan_no": d["pan_no"],
                "addresses": [],
                "contacts": [],
                "emails": [],
                "old_donor_id": d["old_donor_id"],
            }
            if d["occupation"] != "occupation-required":
                document_dict["occupation"] = d["occupation"]

            if d["primary_address_type"]:
                preferred = 1 if d["pref_address"] == d["primary_address_type"] else 0
                if d["primary_address_type"] == "Residence":
                    d["primary_address_type"] = "Residential"
                if d["primary_address_type"] == "Office & Factory":
                    d["primary_address_type"] = "Other"
                document_dict["addresses"].append(
                    {
                        "preferred": preferred,
                        "type": d["primary_address_type"],
                        "address_line_1": d["primary_address_1"],
                        "address_line_2": d["primary_address_2"],
                        "city": d["primary_city"],
                        "state": d["primary_state"],
                        "country": d["primary_country"],
                        "pin_code": resolve_pin(d["primary_pincode"]),
                        "latitude": d["primary_lat"],
                        "longitude": d["primary_long"],
                    }
                )
            if d["secondary_address_type"]:
                preferred = 1 if d["pref_address"] == d["secondary_address_type"] else 0
                if d["secondary_address_type"] == "Residence":
                    d["secondary_address_type"] = "Residential"
                if d["secondary_address_type"] == "Office & Factory":
                    d["secondary_address_type"] = "Other"
                document_dict["addresses"].append(
                    {
                        "preferred": preferred,
                        "type": d["secondary_address_type"],
                        "address_line_1": d["secondary_address_1"],
                        "address_line_2": d["secondary_address_2"],
                        "city": d["secondary_city"],
                        "state": d["secondary_state"],
                        "country": d["secondary_country"],
                        "pin_code": resolve_pin(d["secondary_pincode"]),
                        "latitude": d["secondary_lat"],
                        "longitude": d["secondary_long"],
                    }
                )

            ## Contacts
            contacts = []
            if d["other_phone"]:
                other_phone = json.loads(json.loads(d["other_phone"]))
                for en in other_phone:
                    # phone_code = "".join(re.findall(r"\d", en["phonecodevalue"]))
                    contacts.append(str(en["phoneno"]))
            contacts.append(extract_last_10_digits(d["mobile1"]))
            contacts.append(extract_last_10_digits(d["whatsapp1"]))
            contacts = list(set(contacts))
            for contact in contacts:
                document_dict["contacts"].append({"contact_no": contact})

            ## Emails
            emails = []
            if d["other_email"]:
                other_email = json.loads(json.loads(d["other_email"]))
                for en in other_email:
                    emails.append(en["email"])
            if d["email1"]:
                emails.append(d["email1"])
            emails = list(set(emails))
            for email in emails:
                if "@hkm.org" in email:
                    continue
                email = re.sub(r"[^a-zA-Z0-9.@]", "", email)
                document_dict["emails"].append({"email": email})
            ## Donor Creation
            doc = frappe.get_doc(document_dict)
            doc.insert()

            ## Profile Photo
            if d["profile"]:
                print("Also Creating Patron")
                public_image_url = f"{DOMAIN}{d['profile']}"
                extension = Path(d["profile"]).suffix
                response = requests.get(public_image_url)
                file_doc = save_file(
                    f"profile_{index}.{extension}",
                    response.content,
                    "Donor",
                    doc.name,
                    None,
                    is_private=0,
                    df="profile_image",
                )
                doc.profile_image = file_doc.file_url
            doc.save()

            ## Patron Creation
            if (
                d["is_patron"]
                and d["patron_code"] not in avoid_to_make_patrons
                and not frappe.db.exists("Patron", {"old_patron_id": d["old_donor_id"]})
            ):
                document_dict["doctype"] = "Patron"
                del document_dict["old_donor_id"]
                document_dict["old_patron_id"] = (d["old_donor_id"],)
                document_dict["seva_type"] = d["seva_name"]
                patron_doc = frappe.get_doc(document_dict)
                patron_doc.insert()

                ## Profile Photo

                if d["profile"]:
                    extension = Path(d["profile"]).suffix
                    public_image_url = f"{DOMAIN}{d['profile']}"
                    response = requests.get(public_image_url)
                    file_doc = save_file(
                        f"patron_profile_{index}.{extension}",
                        response.content,
                        "Patron",
                        patron_doc.name,
                        None,
                        is_private=0,
                        df="profile_image",
                    )
                    patron_doc.profile_image = file_doc.file_url

                if d["patron_form"]:
                    extension = Path(d["patron_form"]).suffix.lower()
                    public_image_url = f"{DOMAIN}{d['patron_form']}"
                    response = requests.get(public_image_url)
                    file_doc = save_file(
                        f"patron_form_{index}.{extension}",
                        response.content,
                        "Patron",
                        patron_doc.name,
                        None,
                        is_private=0,
                    )

                if d["corpus_form"]:
                    extension = Path(d["corpus_form"]).suffix.lower()
                    public_image_url = f"{DOMAIN}{d['corpus_form']}"
                    response = requests.get(public_image_url)
                    file_doc = save_file(
                        f"corpus_form_{index}.{extension}",
                        response.content,
                        "Patron",
                        patron_doc.name,
                        None,
                        is_private=0,
                    )

                patron_doc.save()

            frappe.db.commit()  # v16: OK - operations script
        except:
            print(index)
            print(d)
            raise


def extract_last_10_digits(input_string):
    # Use a regular expression to find all digits in the string
    digits = re.findall(r"\d", input_string)

    # Take the last 10 digits using string slicing
    last_10_digits = "".join(digits[-10:])

    return last_10_digits


def resolve_pin(pin_code):
    if pin_code and pin_code != "100001":
        return pin_code
    return None


def upload_seva_subtypes():
    types = run_query(seva_subtype_fetch)
    for t in types:
        if not frappe.db.exists("Seva Subtype", t["seva"]):
            doc = frappe.get_doc(
                {
                    "doctype": "Seva Subtype",
                    "seva_name": t["seva"],
                    "amount": t["amount"],
                    "parent_seva_subtype": t["parent"],
                }
            )
            doc.insert()

        if t["parent"]:
            frappe.db.set_value("Seva Subtype", t["parent"], "is_group", 1)

    frappe.db.commit()  # v16: OK - operations script


def upload_payment_modes():
    data = run_query(
        """
                select name from payments
                """
    )
    for d in data:
        if not frappe.db.exists("DJ Mode of Payment", d["name"]):
            doc = frappe.get_doc({"doctype": "DJ Mode of Payment", "mode": d["name"]})
            doc.insert()
    frappe.db.commit()  # v16: OK - operations script


def upload_receipts():
    donors_dict = {}
    patrons_dict = {}
    for d in frappe.get_all("Donor", fields=["name", "old_donor_id"]):
        donors_dict.setdefault(d["old_donor_id"], d["name"])
    for p in frappe.get_all("Patron", fields=["name", "old_patron_id"]):
        patrons_dict.setdefault(p["old_patron_id"], p["name"])

    receipts = run_query(upload_receipts_query)

    total_receipts = len(receipts)
    for index, receipt in enumerate(receipts):
        # if index <= 1000:
        #     continue
        print(f"Processing Receipt : {index} / {total_receipts}")
        try:
            donation_dict = {
                "doctype": "Donation Receipt",
                "company": "Hare Krishna Movement Ahmedabad",
                "receipt_date": receipt["receipt_date"],
                "realization_date": receipt["receipt_date"],
                "preacher": receipt["preacher"],
                "donor": donors_dict[str(receipt["donor_id"])],
                "sevak_name": receipt["sevak_name"],
                "payment_method": receipt["payment_method"],
                "amount": receipt["amount"],
                "remarks": receipt["remarks"],
                "user_remarks": receipt["user_remarks"],
                "seva_type": get_seva_type(
                    receipt["seva_id"], receipt["parent_seva_id"]
                ),
                "atg_required": receipt["atg_required"],
                "seva_subtype": get_seva_subtype(
                    receipt["seva_id"], receipt["seva_subtype"]
                ),
                "cheque_number": receipt["cheque_number"],
                "cheque_date": receipt["cheque_date"],
                "ifsc_code": receipt["ifsc_code"],
                "bank_name": receipt["bank_name"],
                "old_dr_no": receipt["old_dr_no"],
            }

            if receipt["seva_id"] in patron_seva_ids:
                try:
                    if str(receipt["donor_id"]) in relation_company_patron:
                        donation_dict["patron"] = patrons_dict[
                            relation_company_patron[str(receipt["donor_id"])]
                        ]
                    elif receipt["tag_id"]:
                        donation_dict["patron"] = patrons_dict[str(receipt["tag_id"])]
                    else:
                        donation_dict["patron"] = patrons_dict[str(receipt["donor_id"])]
                except:
                    print(f'Patron ID not found : {receipt["donor_id"]}')
                    pass

            doc = frappe.get_doc(donation_dict)
            doc.insert()

            if receipt["payment_screenshot"]:
                extension = Path(receipt["payment_screenshot"]).suffix
                public_image_url = f"{DOMAIN}{receipt['payment_screenshot']}"
                response = requests.get(public_image_url)
                file_doc = save_file(
                    f"receipt_{index}.{extension}",
                    response.content,
                    "Donation Receipt",
                    doc.name,
                    None,
                    is_private=0,
                    df="payment_screenshot",
                )
                doc.payment_screenshot = file_doc.file_url
            doc.save()
            if receipt["cancelled"]:
                doc.db_set("workflow_state", "Cancelled")
                doc.db_set("docstatus", 2)
            else:
                if doc.payment_method.lower() == "cash":
                    doc.db_set("workflow_state", "Received by Cashier")
                else:
                    doc.db_set("workflow_state", "Realized")
                doc.db_set("docstatus", 1)
        except Exception as e:
            print(receipt)
            raise
        if index % 100 == 0:
            frappe.db.commit()  # v16: OK - operations script
    frappe.db.commit()  # v16: OK - operations script


def get_seva_subtype(seva_id, received):
    if seva_id in patron_seva_ids:
        return "Patronship Donation"
    else:
        if frappe.db.exists("Seva Subtype", received):
            return received
        return "General Donation"


def get_seva_type(seva_id, parent_seva_id):
    # Patronship
    if parent_seva_id in patron_seva_ids:
        return "Corpus - HKMA"

    # Corpus
    if parent_seva_id in [163, 164]:
        return "Corpus - HKMA"

    # Festival
    if parent_seva_id in festival_parent_ids:
        return "Cultural Promotion - HKMA"

    if seva_id == 207:
        return "Kind - HKMA"

    if parent_seva_id == 292:
        return "CSR - HKMA"

    return "General - HKMA"


def upload_general_receipts():
    receipts = run_query(upload_general_receipts_query)
    total_receipts = len(receipts)
    # test = 0
    for index, receipt in enumerate(receipts):
        if receipt["original_id"] < 19512:
            continue
        # test += 1
        # if test == 5:
        #     break
        print(f"Processing Receipt {index}/{total_receipts}")
        try:
            receipt["company"] = "Hare Krishna Movement Ahmedabad"
            receipt["seva_type"] = (
                get_seva_type(receipt["seva_id"], receipt["parent_seva_id"]),
            )

            receipt["seva_subtype"] = (
                get_seva_subtype(receipt["seva_id"], receipt["seva_subtype"]),
            )

            del receipt["seva_id"]
            del receipt["parent_seva_id"]

            new_general_receipt(receipt)
        except:
            print(index)
            print(receipt)
            raise


def upload_pujas():
    month_dict = {
        1: "January",
        2: "February",
        3: "March",
        4: "April",
        5: "May",
        6: "June",
        7: "July",
        8: "August",
        9: "September",
        10: "October",
        11: "November",
        12: "December",
    }
    pujas = run_query(
        """
                select
                    p.donor_id as old_patron_id,
                    day(p.`date`) as day,
                    month(p.`date`)as month,
                    Concat(if(p.occasion = 1, "Birthday", if(p.occasion = 2, "Aniversary", "Other")), ' - ', fm.name) as occasion
                from
                    poojayagnas p
                join family_members fm
                on
                    fm.id = p.femmem_id
                where
                    1
                """
    )

    patrons_dict = {}
    for p in frappe.get_all("Patron", fields=["name", "old_patron_id"]):
        patrons_dict.setdefault(p["old_patron_id"], p["name"])

    print(patrons_dict)
    error_pids = []
    for p in pujas:
        try:
            doc = frappe.get_doc(
                {
                    "doctype": "Patron Privilege Puja",
                    "patron": patrons_dict[str(p["old_patron_id"])],
                    "day": p["day"],
                    "month": month_dict[p["month"]],
                    "occasion": p["occasion"],
                }
            )
            doc.insert()
        except Exception as e:
            print(e)
            error_pids.append(str(p["old_patron_id"]))
    frappe.db.commit()  # v16: OK - operations script
    print(error_pids)


def update_pan():
    from hkm.operations.ahmd.constants import mobile_pans

    for mp in mobile_pans:
        words = mp.split()
        if len(words) == 2:
            clean_contact = re.sub(r"\D", "", str(words[0]))[-10:]
            donor = identify_donor(
                contact=clean_contact, email=None, pan=None, aadhar=None
            )
            if donor and not frappe.db.get_value("Donor", donor, "pan_no"):
                print(f"Updating PAN No. in {donor}")
                frappe.db.set_value("Donor", donor, "pan_no", words[1])
        frappe.db.commit()  # v16: OK - operations script


# def set_api_data():
#     # states = run_query(
#     #     """
#     #                 SELECT states.state_name, countries.country_name
#     #                 FROM `states`
#     #                 JOIN `countries` ON states.country_id = countries.id
#     #                 WHERE 1"""
#     # )
#     # for s in states:
#     #     if not frappe.db.exists(
#     #         "API State", {"state_name": s["state_name"], "country": s["country_name"]}
#     #     ):
#     #         doc = frappe.get_doc(
#     #             {
#     #                 "doctype": "API State",
#     #                 "state_name": s["state_name"],
#     #                 "country": s["country_name"],
#     #             }
#     #         )
#     #         doc.insert()
#     cities = run_query(
#         """
#                     SELECT cities.city_name, states.state_name, states.id as state_id
#                     FROM `cities`
#                     JOIN `states` ON cities.state_id = states.id
#                     WHERE 1"""
#     )
#     states = {}
#     for st in frappe.get_all("API State", fields=["name", "old_ref"]):
#         states.setdefault(st["old_ref"], st["name"])

#     for s in cities:
#         if s["city_name"] == "":
#             continue

#         if str(s["state_id"]) not in states:
#             print(s)
#             continue
#         # if not frappe.db.exists(
#         #     "API City", {"state_name": s["state_name"], "country": s["country_name"]}
#         # ):

#         try:
#             doc = frappe.get_doc(
#                 {
#                     "doctype": "API City",
#                     "city_name": s["city_name"],
#                     "state": states[str(s["state_id"])],
#                 }
#             )
#             doc.insert()
#         except frappe.MandatoryError:
#             print(s)
#             continue
#     frappe.db.commit()


# def set_api_data2():
#     states = run_query(
#         """
#                     SELECT states.state_name,states.id as state_id, countries.country_name
#                     FROM `states`
#                     JOIN `countries` ON states.country_id = countries.id
#                     WHERE 1"""
#     )
#     for s in states:
#         if not frappe.db.exists(
#             "API State", {"state_name": s["state_name"], "country": s["country_name"]}
#         ):
#             doc = frappe.get_doc(
#                 {
#                     "doctype": "API State",
#                     "state_name": s["state_name"],
#                     "country": s["country_name"],
#                     "old_ref": s["state_id"],
#                 }
#             )
#             doc.insert()
#     frappe.db.commit()


def close_pos():
    doc = frappe.get_doc("POS Closing Entry", "POS-CLO-2026-00327")
    doc.submit()
    
