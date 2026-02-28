import frappe
from hkm.erpnext___custom.doctype.extra_utils.sheet import get_data_from_google_sheets


def process_kanthi_mala():
    items = frappe.get_all(
        "Item",
        filters={
            "item_group": "Jap Mala",
        },
        pluck="name",
    )

    for item in items:
        item_doc = frappe.get_doc("Item", item)
        item_doc.taxes = []
        item_doc.save()

    frappe.db.commit()  # v16: OK - operations script


def process_hsn_code():
    hsn = ["441400"]
    not_have_tax_template = []
    having_zero_tax_template = []
    new_rate = "5%"
    
    for i in  frappe.get_all(
        "Item",
        filters={
            "gst_hsn_code": ["in", hsn],
        },
        pluck="name",
    ):
        item = frappe.get_doc("Item", i)

        if item.get("taxes"):
            if not new_rate or str(new_rate).strip("%") == "0":
                having_zero_tax_template.append(i)
                item.taxes = []
            else:
                for tax in item.get("taxes"):
                    taxes = tax.item_tax_template
                    tax.item_tax_template = replace_percentage(
                        taxes, str(new_rate).strip("%")
                    )
        else:
            tax_template = ["GST - 5% - TSFJ"]

            if not new_rate or str(new_rate).strip("%") == "0":
                item.taxes = []
                having_zero_tax_template.append(i)
            else:
                for i in tax_template:
                    item.append(
                        "taxes",
                        {
                            "item_tax_template": replace_percentage(
                                i, str(new_rate).strip("%")
                            ),
                        },
                    )

            not_have_tax_template.append(i)

        item.save()
        

        print("\n==== SUMMARY ====")  # move to next line after loop
        print("not_have_tax_template", not_have_tax_template)
        print("having_zero_tax_template", having_zero_tax_template)
    frappe.db.commit()  # v16: OK - operations script
    

def process():
    rows = get_data_from_google_sheets(
        "https://docs.google.com/spreadsheets/d/1GEVAezOs8AYZ-LKG8PqqWFpM-nAQGC1Q/edit?gid=1785919200#gid=1785919200"
    )

    not_have_tax_template = []
    having_zero_tax_template = []

    try:
        total = len(rows[1:])
        for idx, raw in enumerate(rows[1:], start=1):
            if not raw[0]:
                continue

            item_code = raw[0]
            new_rate = raw[1]

            if not item_code or not new_rate:
                continue

            # progress in same row
            print(f"Processing {idx}/{total} : {item_code} ({new_rate})", end="\r")

            item = frappe.get_doc("Item", item_code.strip())

            if item.get("taxes"):
                if not new_rate or str(new_rate).strip("%") == "0":
                    having_zero_tax_template.append(item_code)
                    item.taxes = []
                else:
                    for tax in item.get("taxes"):
                        taxes = tax.item_tax_template
                        tax.item_tax_template = replace_percentage(
                            taxes, str(new_rate).strip("%")
                        )
            else:
                tax_template = ["GST - 18% - TSFJ"]

                if not new_rate or str(new_rate).strip("%") == "0":
                    item.taxes = []
                    having_zero_tax_template.append(item_code)
                else:
                    for i in tax_template:
                        item.append(
                            "taxes",
                            {
                                "item_tax_template": replace_percentage(
                                    i, str(new_rate).strip("%")
                                ),
                            },
                        )

                not_have_tax_template.append(item_code)

            item.save()
            frappe.db.commit()  # v16: OK - operations script

        print("\n==== SUMMARY ====")  # move to next line after loop
        print("not_have_tax_template", not_have_tax_template)
        print("having_zero_tax_template", having_zero_tax_template)

    except Exception as e:
        frappe.log_error(e)
        print("\nError:", e)


import re


def replace_percentage(text, new_percentage):
    # Replace n% (where n is any number) with new_percentage
    new_text = re.sub(r"\d+%", f"{new_percentage}%", text)
    return new_text


# N-SEOT-0024-2	18%
