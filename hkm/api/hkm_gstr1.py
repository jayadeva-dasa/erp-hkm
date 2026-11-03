import frappe
from frappe import _
from frappe.utils import flt, getdate

from india_compliance.gst_india.doctype.gst_return_log.generate_gstr_1 import (
    GenerateGSTR1,
    SummarizeGSTR1,
)
from india_compliance.gst_india.doctype.gstr_1.gstr_1 import (
    get_gstr_1_from_and_to_date,
)
from india_compliance.gst_india.utils import get_gstin_list
from india_compliance.gst_india.utils.gstr_1 import CATEGORY_SUB_CATEGORY_MAPPING
from india_compliance.gst_india.utils.gstr_1.gstr_1_json_map import GSTR1BooksData

SUB_TO_CATEGORY = {
    sub.value: cat.value
    for cat, subs in CATEGORY_SUB_CATEGORY_MAPPING.items()
    for sub in subs
}
AMOUNTS = (
    "total_taxable_value",
    "total_igst_amount",
    "total_cgst_amount",
    "total_sgst_amount",
    "total_cess_amount",
)
DETAIL_FIELDS = (
    "document_type",
    "document_number",
    "document_date",
    "transaction_type",
    "customer_gstin",
    "customer_name",
    "place_of_supply",
    "reverse_charge",
    "diff_percentage",
    "ecommerce_gstin",
    "shipping_bill_number",
    "shipping_bill_date",
    "shipping_port_code",
    "hsn_code",
    "description",
    "uom",
    "quantity",
    "tax_rate",
    "exempted_amount",
    "nil_rated_amount",
    "non_gst_amount",
    "from_sr_no",
    "to_sr_no",
    "total_count",
    "draft_count",
    "cancelled_count",
    "document_value",
)


@frappe.whitelist()
def get_report(filters=None):
    frappe.has_permission("Sales Invoice", "read", throw=True)
    if isinstance(filters, str):
        filters = frappe.parse_json(filters)
    filters = frappe._dict(filters or {})
    companies = as_list(filters.companies)
    if not companies:
        frappe.throw(_("Please select at least one Company"))

    pref = filters.filing_preference or "Monthly"
    from_date, to_date = get_gstr_1_from_and_to_date(
        filters.month_or_quarter, filters.year, pref
    )
    filing_from = getdate(f"01-{filters.month_or_quarter}-{filters.year}")

    books_by_gstin = {}
    for company, gstin in get_pairs(companies, as_list(filters.company_gstins)):
        data = GSTR1BooksData(
            frappe._dict(
                company=company,
                company_gstin=gstin,
                from_date=from_date,
                to_date=to_date,
                month_or_quarter=filters.month_or_quarter,
                year=filters.year,
                filing_preference=pref,
            )
        ).prepare_mapped_data()
        data["aggregate_data"] = GenerateGSTR1.get_aggregate_data(data)
        books_by_gstin[(company, gstin)] = GenerateGSTR1.normalize_data(data)

    if filters.view == "Detailed":
        return list(detailed(books_by_gstin, filters))

    return list(summary(books_by_gstin, filters, filing_from))


# ------------------------------------------------------------------- summary
def summary(books_by_gstin, filters, filing_from):
    summarizer = SummarizeGSTR1()
    split = int(filters.split_by_gstin or 0)
    groups = (
        {k: [v] for k, v in books_by_gstin.items()}
        if split
        else {("", ""): list(books_by_gstin.values())}
    )

    data = []
    for (company, gstin), books_list in groups.items():
        books = {}
        for b in books_list:
            merge(books, b)

        rows = summarizer.get_summarized_data(books, filing_from)
        for row in rows:
            data.append(
                {
                    "company": company,
                    "company_gstin": gstin,
                    "description": row["description"],
                    "no_of_records": row.get("no_of_records"),
                    "indent": row.get("indent", 0),
                    **{f: flt(row.get(f)) for f in AMOUNTS},
                }
            )

        data.append(get_total_liability_row(rows, company, gstin))

    columns = []
    if split:
        columns += [
            col("company", "Company", "Link", 160, "Company"),
            col("company_gstin", "Company GSTIN", width=150),
        ]
    columns += [
        col("description", "Description", width=330),
        col("no_of_records", "Total Docs", "Int", 110),
    ]
    columns += amount_columns()
    return columns, data


def get_total_liability_row(rows, company, gstin):
    """Same logic as the 'Total Liability' row of GSTR-1."""
    total = {f: 0 for f in ("no_of_records", *AMOUNTS)}
    for row in rows:
        for field in total:
            if row.get("consider_in_total_taxable_value") and field in (
                "no_of_records",
                "total_taxable_value",
            ):
                total[field] += flt(row.get(field))
            elif row.get("consider_in_total_tax"):
                total[field] += flt(row.get(field))

    return {
        "company": company,
        "company_gstin": gstin,
        "description": "Total Liability",
        "indent": 0,
        "is_total": 1,
        **{f: flt(v, 2) for f, v in total.items()},
    }


def detailed(books_by_gstin, filters):
    data = []
    for (company, gstin), books in books_by_gstin.items():
        for sub_category, rows in books.items():
            if sub_category in ("rounding_difference", "aggregate_data"):
                continue

            category = SUB_TO_CATEGORY.get(sub_category, sub_category)
            if filters.category and category != filters.category:
                continue

            for row in rows:
                data.append(
                    {
                        "company": company,
                        "company_gstin": gstin,
                        "category": category,
                        "sub_category": sub_category,
                        **{f: row.get(f) for f in DETAIL_FIELDS},
                        **{f: flt(row.get(f)) for f in AMOUNTS},
                    }
                )

    columns = [
        col("company", "Company", "Link", 160, "Company"),
        col("company_gstin", "Company GSTIN", width=150),
        col("category", "Category", width=170),
        col("sub_category", "Sub Category", width=170),
        col("document_type", "Document Type", width=130),
        col("document_number", "Document No", width=150),
        col("document_date", "Date", "Date", 100),
        col("transaction_type", "Transaction Type", width=110),
        col("customer_gstin", "Customer GSTIN", width=150),
        col("customer_name", "Customer Name", width=180),
        col("place_of_supply", "Place of Supply", width=130),
        col("reverse_charge", "Reverse Charge", width=90),
        col("diff_percentage", "Diff %", "Float", 70),
        col("ecommerce_gstin", "E-Commerce GSTIN", width=150),
        col("shipping_bill_number", "Shipping Bill No", width=120),
        col("shipping_bill_date", "Shipping Bill Date", "Date", 110),
        col("shipping_port_code", "Port Code", width=90),
        col("hsn_code", "HSN Code", width=100),
        col("description", "Description", width=200),
        col("uom", "UOM", width=100),
        col("quantity", "Quantity", "Float", 90),
        col("tax_rate", "Tax Rate", "Float", 80),
        col("document_value", "Document Value", "Currency", 120),
        col("exempted_amount", "Exempted", "Currency", 100),
        col("nil_rated_amount", "Nil Rated", "Currency", 100),
        col("non_gst_amount", "Non-GST", "Currency", 100),
        col("from_sr_no", "From Sr No", width=140),
        col("to_sr_no", "To Sr No", width=140),
        col("total_count", "Total Count", "Int", 90),
        col("draft_count", "Draft Count", "Int", 90),
        col("cancelled_count", "Cancelled Count", "Int", 100),
    ] + amount_columns()
    return columns, data


# ------------------------------------------------------------------- helpers
def amount_columns():
    return [
        col("total_taxable_value", "Taxable Value", "Currency", 130),
        col("total_igst_amount", "IGST", "Currency", 110),
        col("total_cgst_amount", "CGST", "Currency", 110),
        col("total_sgst_amount", "SGST", "Currency", 110),
        col("total_cess_amount", "CESS", "Currency", 100),
    ]


def col(fieldname, label, fieldtype="Data", width=120, options=None):
    return {
        "fieldname": fieldname,
        "label": _(label),
        "fieldtype": fieldtype,
        "width": width,
        "options": options,
    }


def as_list(value):
    if not value:
        return []
    if isinstance(value, str):
        value = frappe.parse_json(value) if value.startswith("[") else [value]
    return list(value)


def merge(target, source):
    for key, rows in source.items():
        if key == "aggregate_data":
            merge(target.setdefault(key, {}), rows)

        elif key == "rounding_difference":
            current = target.setdefault(key, [{}])[0]
            for row in rows:
                for field, value in row.items():
                    current[field] = current.get(field, 0) + value

        else:
            target.setdefault(key, []).extend(rows)


def get_pairs(companies, gstins):
    pairs = []
    for company in companies:
        frappe.has_permission("Company", doc=company, throw=True)
        company_gstins = get_gstin_list(company)
        for gstin in gstins or company_gstins:
            if gstin in company_gstins:
                pairs.append((company, gstin))
    return pairs


@frappe.whitelist()
def get_company_gstins(companies):
    gstins = []
    for company in as_list(companies):
        gstins += get_gstin_list(company)
    return sorted(set(gstins))
