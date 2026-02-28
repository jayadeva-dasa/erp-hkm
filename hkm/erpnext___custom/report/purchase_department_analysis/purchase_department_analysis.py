# Copyright (c) 2022, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):

    if not filters:
        filters = {}
    filters.update(
        {
            "from_date": filters.get("date_range") and filters.get("date_range")[0],
            "to_date": filters.get("date_range") and filters.get("date_range")[1],
        }
    )
    # columns = get_columns(filters)
    conditions = get_condition(filters)

    if filters.get("based_on") == "Purchase Order":
        purchase_data = frappe.db.sql(
            """
							SELECT SUM(grand_total) as total, department, supplier
							FROM `tabPurchase Order` PO

							WHERE PO.docstatus = 1 %s
							GROUP BY PO.department, PO.supplier
							"""
            % (conditions),
            filters,
            as_dict=1,
        )
    elif filters.get("based_on") == "Purchase Invoice":
        purchase_data = frappe.db.sql(
            """
							SELECT SUM(grand_total) as total, department, supplier
							FROM `tabPurchase Invoice` PI

							WHERE PI.docstatus = 1 %s
							GROUP BY PI.department, PI.supplier
							"""
            % (conditions),
            filters,
            as_dict=1,
        )

    purchase_data_map = {}

    for i in purchase_data:
        key = str(i.department or "") + "-" + str(i.supplier or "")
        purchase_data_map.setdefault(key, i.total)

    unique_departments = list(set([row["department"] for row in purchase_data]))
    unique_suppliers = list(set([row["supplier"] for row in purchase_data]))

    # data = []
    columns = [
        {
            "fieldname": "supplier",
            "label": "Supplier",
            "fieldtype": "Link",
            "options": "Supplier",
            "width": 200,
        }
    ]
    for dept in unique_departments:
        columns.append(
            {"fieldname": dept, "label": dept, "fieldtype": "Currency", "width": 150}
        )

    avl_combs = purchase_data_map.keys()
    # data = [[0] * len(unique_departments)] * len(unique_suppliers)
    data = []
    for idx, supplier in enumerate(unique_suppliers):
        row_data = []
        row_data.append(supplier)
        for didx, department in enumerate(unique_departments):
            key = str(department or "") + "-" + str(supplier or "")
            if key in avl_combs:
                row_data.append(purchase_data_map[key])
            else:
                row_data.append(0)
        data.append(row_data)

    # columns, data = [], []
    return columns, data


def get_columns(filters):
    company = filters.get("company")

    departments = frappe.db.get_list(
        "Department",
        pluck="name",
        filters={"company": company},
    )
    columns = [
        {
            "fieldname": x,
            "label": x,
            "fieldtype": "Link",
            "options": "Department",
            "width": 150,
        }
        for x in departments
    ]
    return columns


def get_condition(filters):
    """Get Filter Items"""
    conditions = ""
    if filters.get("based_on") == "Purchase Order":
        for opts in (
            ("company", " and `PO`.company=%(company)s "),
            ("from_date", " and `PO`.transaction_date>=%(from_date)s "),
            ("to_date", " and `PO`.transaction_date<=%(to_date)s "),
        ):
            if filters.get(opts[0]):
                conditions += opts[1]
    elif filters.get("based_on") == "Purchase Invoice":
        for opts in (
            ("company", " and `PI`.company=%(company)s "),
            ("from_date", " and `PI`.posting_date>=%(from_date)s "),
            ("to_date", " and `PI`.posting_date<=%(to_date)s "),
        ):
            if filters.get(opts[0]):
                conditions += opts[1]

    return conditions
