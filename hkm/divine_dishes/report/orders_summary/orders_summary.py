# Copyright (c) 2023, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    columns, data = [], []

    if not filters:
        filters = {}
    filters.update(
        {
            "from_date": filters.get("date_range") and filters.get("date_range")[0],
            "to_date": filters.get("date_range") and filters.get("date_range")[1],
        }
    )

    columns = get_columns(filters)

    conditions = get_condition(filters)
    data = frappe.db.sql(
        f"""
				select 
                	user_order.user as customer_id,
                    user_order.status as order_status,
                    customer.full_name as customer_name,
                    user_order.name as order_id,
                    GROUP_CONCAT(DISTINCT CONCAT(item.item_name,' : ',ROUND(item.qty,0),' (',item.sku,')') SEPARATOR ', ') as items,
                    GROUP_CONCAT(DISTINCT CONCAT('(Primary :',address.primary,') ', address.full_address,' | ',address.mobile_no) ORDER BY address.primary SEPARATOR ', ' ) as address,
                    user_order.total_amount as amount
                from `tabDD Order` user_order
				join `tabUser` customer on customer.name = user_order.user
                join `tabDD Order Item` item on item.parent = user_order.name
                left join `tabDD User Address` address on address.user = user_order.user
			   	where 1 {conditions}
				group by customer_id
				""",
        as_dict=1,
    )

    return columns, data


def get_condition(filters):
    conditions = ""
    conditions += f""" 
					and user_order.date <= '{filters.get('to_date')}' and user_order.date >= '{filters.get('from_date')}' """
    if filters.get("customer"):
        conditions += f" and user_order.user = '{filters.get('customer')}' "

    return conditions


def get_columns(filters):
    """return columns based on filters"""
    columns = [
        {"fieldname": "customer_id", "label": "Customer ID", "fieldtype": "Link", "options": "User", "width": 100},
        {
            "fieldname": "customer_name",
            "label": "Full Name",
            "fieldtype": "Data",
            "width": 140,
        },
        {
            "fieldname": "order_id",
            "label": "Order ID",
            "fieldtype": "Link",
            "options": "DD Order",
            "width": 140,
        },
        {
            "fieldname": "order_status",
            "label": "Order Status",
            "fieldtype": "Data",
            "width": 140,
        },
        {
            "fieldname": "items",
            "label": "Items",
            "fieldtype": "Data",
            "width": 300,
        },
        {
            "fieldname": "address",
            "label": "Address",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "fieldname": "amount",
            "label": "Amount",
            "fieldtype": "Currency",
            "width": 120,
        },
    ]
    return columns
