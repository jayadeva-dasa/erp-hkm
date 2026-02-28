import frappe
from frappe.utils.background_jobs import enqueue
from frappe.utils import time_diff_in_hours, time_diff_in_seconds, date_diff, flt
from frappe.model.workflow import apply_workflow


@frappe.whitelist()
def fetch_item_code(item_group):
    if frappe.db.exists("Item Group", item_group):
        item_grp_doc = frappe.get_doc("Item Group", item_group)
        series = item_grp_doc.get("item_code_series")
        if series is not None and series.strip() != "":
            codes = frappe.db.sql(
                """
						select CAST(TRIM(LEADING '{}-' FROM item_code ) AS int) AS new_code 
						from `tabItem`
						where item_code LIKE '{}-%'
						order by new_code DESC
							""".format(
                    series, series
                ),
                as_dict=1,
            )

            last_code = codes[0]["new_code"] if len(codes) > 0 else 1
            last_code = str(last_code + 1).zfill(4)
            return series + "-" + last_code
    return 0


def item_taxes_and_income_account_set(self, method):
    if self.get("item_creation_request"):
        ic_request = frappe.get_doc(
            "Item Creation Request", self.get("item_creation_request")
        )
        if ic_request.is_sales_item:
            tax = ic_request.tax_category
            if not (tax is None or tax == ""):
                self.append(
                    "taxes",
                    {
                        "item_tax_template": tax,
                    },
                )
            if ic_request.default_company:
                self.append(
                    "item_defaults",
                    {
                        "company": ic_request.default_company,
                        "income_account": ic_request.default_sales_income_account,
                    },
                )


def update_item_code_in_barcodes(self, method):
    # Only add barcode if item_code is available
    # During before_insert, item_code may not be set yet
    if hasattr(self, 'item_code') and self.item_code:
        # Check if this barcode already exists to avoid duplicates
        existing_barcodes = [d.barcode for d in self.barcodes if hasattr(d, 'barcode')]
        if self.item_code not in existing_barcodes:
            self.append(
                "barcodes",
                {
                    "barcode": self.item_code,
                }
            )
