# Copyright (c) 2023, Narahari Dasa and contributors
# For license information, please see license.txt

from datetime import datetime
import frappe
from erpnext.stock.utils import get_stock_balance
from frappe.utils.data import flt
from erpnext.stock.report.stock_balance.stock_balance import StockBalanceReport

TRANSFER_TO_TITLE = "TW-"
SALES_TITLE = "SL-"
EXPENSE_TITLE = "EX-"


def get_date_time(
    input_string,
):
    datetime_obj = datetime.strptime(input_string, "%Y-%m-%d %H:%M:%S")
    # Extract the time part as a string
    time_string = datetime_obj.strftime("%H:%M")
    date_string = datetime_obj.strftime("%Y-%m-%d")
    return date_string, time_string


def execute(filters=None):
    # filters["from_date"], filters["from_time"] = get_date_time(filters.get("from_date"))
    # filters["to_date"], filters["to_time"] = get_date_time(filters.get("to_date"))

    sle_entries = get_sle_entries(filters)

    stock_entries = get_stock_entries(sle_entries)

    sales_entries = get_sales_entries(sle_entries)

    items = {}
    transfer_to_warehouses = []
    expense_heads = []
    customer_heads = []

    for s in sle_entries:
        item_code = s["item_code"]

        if item_code not in items:
            items[item_code] = get_item_map(item_code, filters)

        items[item_code]["sle_entries"].append(s["name"])

        if s["voucher_type"] == "Purchase Receipt":
            items[item_code]["total_purchase_income"] += s["actual_qty"]

        elif s["voucher_type"] == "Stock Entry":
            if stock_entries[s["voucher_no"]]["stock_entry_type"] == "Material Transfer":
                if s["actual_qty"] > 0:
                    # This has been received from some Warehouse
                    items[item_code]["total_transfer_income"] += s["actual_qty"]
                else:
                    # This has been transferred to some Warehouse
                    target_warehouse = get_target_warehouse(s["voucher_detail_no"])
                    transaction_title = TRANSFER_TO_TITLE + target_warehouse
                    if transaction_title not in items[item_code]:
                        transfer_to_warehouses.append(target_warehouse)
                        items[item_code][transaction_title] = s["actual_qty"]
                    else:
                        items[item_code][transaction_title] += s["actual_qty"]
            elif stock_entries[s["voucher_no"]]["stock_entry_type"] == "Material Issue":
                ## Expense has been made.
                expense_head = get_expense_head(s["voucher_detail_no"])
                transaction_title = EXPENSE_TITLE + expense_head
                if transaction_title not in items[item_code]:
                    expense_heads.append(expense_head)
                    items[item_code][transaction_title] = s["actual_qty"]
                else:
                    items[item_code][transaction_title] += s["actual_qty"]

        elif s["voucher_type"] == "Sales Invoice":
            transaction_title = SALES_TITLE + sales_entries[s["voucher_no"]]["customer"]
            if transaction_title not in items[item_code]:
                customer_heads.append(sales_entries[s["voucher_no"]]["customer"])
                items[item_code][transaction_title] = s["actual_qty"]
                items[item_code][transaction_title + "-amt"] = calculate_sale_amount(s["voucher_detail_no"])
            else:
                items[item_code][transaction_title] += s["actual_qty"]
                items[item_code][transaction_title + "-amt"] += calculate_sale_amount(s["voucher_detail_no"])

            # items[item_code]["total_sales_amount"] += items[item_code][transaction_title + "-amt"]

    transfer_to_warehouses = list(set(transfer_to_warehouses))
    expense_heads = list(set(expense_heads))
    customer_heads = list(set(customer_heads))

    ## Include Unconsolidated POS Invoices
    items = get_pos_invoices(filters, items)

    ## Get Extra Untransacated Items
    items = get_untransacted_items(filters, items)

    columns = get_columns(filters, transfer_to_warehouses, expense_heads, customer_heads)

    data = list(items.values())

    return columns, data, None, None, get_report_summary(sales_entries)


def get_report_summary(sales_invoices):
    sales_summary_map = {}

    for s, v in sales_invoices.items():
        if v["customer"] not in sales_summary_map:
            sales_summary_map.setdefault(
                v["customer"],
                dict(
                    label=v["customer"],
                    value=v["rounded_total"],
                    datatype="Currency",
                    indicator="Blue",
                ),
            )
        else:
            sales_summary_map[v["customer"]]["value"] += v["rounded_total"]

    return list(sales_summary_map.values())


def get_pos_invoices(filters, items):
    for p in frappe.get_all(
        "POS Invoice",
        filters=[
            ["set_warehouse", "=", filters.get("warehouse")],
            ["posting_date", "<=", filters.get("to_date")],
            # ["posting_time", "<=", filters.get("to_time")],
            ["docstatus", "=", 1],
            ["status", "!=", "Consolidated"],
        ],
        fields=[
            "name",
        ],
    ):
        for i in frappe.get_all("POS Invoice Item", filters={"parent": p["name"]}, fields=["item_code", "qty"]):
            if i["item_code"] not in items:
                items.setdefault(i["item_code"], get_item_map(i["item_code"], filters))
            if "unconsolidated_pos_qty" not in items[i["item_code"]]:
                items[i["item_code"]]["unconsolidated_pos_qty"] = i["qty"]
            else:
                items[i["item_code"]]["unconsolidated_pos_qty"] += i["qty"]
    return items


def get_untransacted_items(filters, items):
    _, data = StockBalanceReport(filters).run()
    for d in data:
        if d["item_code"] not in items:
            item_map = {
                "item_code": d["item_code"],
                "item_name": d["item_name"],
                "item_group": d["item_group"],
                "uom": d["stock_uom"],
                "opening_balance": d["opening_qty"],
                "closing_balance": d["bal_qty"],
            }
            items.setdefault(d["item_code"], get_item_map(d["item_code"], filters))
    return items


def get_stock_entries(sle_entries):
    filtered_stock_entries = [sle["voucher_no"] for sle in sle_entries if sle["voucher_type"] == "Stock Entry"]
    unique_stock_entries = list(set(filtered_stock_entries))
    entries = {}

    for e in frappe.get_all(
        "Stock Entry",
        filters={"name": ["in", unique_stock_entries], "docstatus": 1},
        fields=["name", "stock_entry_type"],
    ):
        entries.setdefault(e["name"], e)

    return entries


def get_sales_entries(sle_entries):
    filtered_sales_entries = [sle["voucher_no"] for sle in sle_entries if sle["voucher_type"] == "Sales Invoice"]
    unique_sales_entries = list(set(filtered_sales_entries))
    entries = {}

    for e in frappe.get_all(
        "Sales Invoice",
        filters={"name": ["in", unique_sales_entries], "docstatus": 1},
        fields=["name", "customer", "rounded_total"],
    ):
        entries.setdefault(e["name"], e)
    return entries


def get_sle_entries(filters):
    return frappe.get_all(
        "Stock Ledger Entry",
        filters=[
            ["warehouse", "=", filters.get("warehouse")],
            ["posting_date", ">=", filters.get("from_date")],
            # ["posting_time", ">=", filters.get("from_time")],
            ["posting_date", "<=", filters.get("to_date")],
            # ["posting_time", "<=", filters.get("to_time")],
            ["is_cancelled", "=", 0],
        ],
        fields=[
            "name",
            "item_code",
            "actual_qty",
            "posting_date",
            "posting_time",
            "voucher_type",
            "voucher_no",
            "voucher_detail_no",
        ],
    )


def get_item_map(item_code, filters):
    name, group, uom = frappe.db.get_value("Item", item_code, ["item_name", "item_group", "stock_uom"])
    return {
        "item_code": item_code,
        "item_name": name,
        "item_group": group,
        "uom": uom,
        "total_purchase_income": 0,
        "total_transfer_income": 0,
        "total_sales_amount": 0,
        "opening_balance": get_stock_balance(
            item_code=item_code,
            warehouse=filters.get("warehouse"),
            posting_date=filters.get("from_date"),
            posting_time="00:00",
            # posting_time=filters.get("from_time"),
        ),
        "closing_balance": get_stock_balance(
            item_code=item_code,
            warehouse=filters.get("warehouse"),
            posting_date=filters.get("to_date"),
            posting_time="23:59",
            # posting_time=filters.get("to_time"),
        ),
        "sle_entries": [],
    }


def get_target_warehouse(voucher_detail):
    return frappe.get_value("Stock Entry Detail", voucher_detail, "t_warehouse")


def get_expense_head(voucher_detail):
    return frappe.get_value("Stock Entry Detail", voucher_detail, "expense_account")


def calculate_sale_amount(sale_item_detail):
    sale_item_doc = frappe.get_doc("Sales Invoice Item", sale_item_detail)
    tax = frappe.get_value("Item Tax Template", sale_item_doc.item_tax_template, "cumulative_tax")
    if tax is None:
        return sale_item_doc.amount
    else:
        return sale_item_doc.amount * (1 + (tax / 100))


def get_columns(filters, transfer_to_warehouses, expense_heads, customer_heads):
    columns = [
        {
            "label": "Item Code",
            "fieldname": "item_code",
            "fieldtype": "Data",
            "width": 250,
        },
        {
            "label": "Item Name",
            "fieldname": "item_name",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": "Item Group",
            "fieldname": "item_group",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": "UOM",
            "fieldname": "uom",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": "Opening Balance",
            "fieldname": "opening_balance",
            "fieldtype": "Float",
            "width": 200,
        },
        {
            "label": "Purchased",
            "fieldname": "total_purchase_income",
            "fieldtype": "Float",
            "width": 200,
        },
        {
            "label": "Received (From Warehouse) ",
            "fieldname": "total_transfer_income",
            "fieldtype": "Float",
            "width": 200,
        },
    ]
    for ttw in transfer_to_warehouses:
        columns.append(
            {
                "label": ttw,
                "fieldname": TRANSFER_TO_TITLE + ttw,
                "fieldtype": "Float",
                "width": 200,
            },
        )

    for eh in expense_heads:
        columns.append(
            {
                "label": eh,
                "fieldname": EXPENSE_TITLE + eh,
                "fieldtype": "Float",
                "width": 200,
            },
        )

    for ch in customer_heads:
        columns.append(
            {
                "label": ch,
                "fieldname": SALES_TITLE + ch,
                "fieldtype": "Float",
                "width": 200,
            },
        )
    columns.extend(
        [
            {
                "label": "Closing Balance",
                "fieldname": "closing_balance",
                "fieldtype": "Float",
                "width": 200,
            },
            {
                "label": "POS Unconsolidated",
                "fieldname": "unconsolidated_pos_qty",
                "fieldtype": "Float",
                "width": 200,
            },
        ]
    )

    if filters.get("show_for_pos_closing"):
        columns = [
            {
                "label": "Item Name",
                "fieldname": "item_name",
                "fieldtype": "Data",
                "width": 200,
            },
            {
                "label": "Closing Balance",
                "fieldname": "closing_balance",
                "fieldtype": "Float",
                "width": 200,
            },
            {
                "label": "POS Unconsolidated",
                "fieldname": "unconsolidated_pos_qty",
                "fieldtype": "Float",
                "width": 200,
            },
        ]

    return columns
