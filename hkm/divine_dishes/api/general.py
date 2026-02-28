import json
import frappe


@frappe.whitelist()
def get_user_profile():
    return frappe.get_doc("User", frappe.session.user).as_dict()


@frappe.whitelist()
def set_primary_address(address_id):
    address_doc = frappe.get_doc("DD User Address", address_id)
    address_doc.primary = 1
    address_doc.save(ignore_permissions=True)


@frappe.whitelist()
def wallet_final_balance():
    txs = frappe.get_list("DD Wallet Tx", fields=["final_balance"], order_by="creation desc")
    if len(txs) == 0:
        return 0
    return txs[0].final_balance


@frappe.whitelist(allow_guest=True)
def get_items(filters, order_by=None, limit_start=None, limit=None):
    filters = json.loads(filters)
    limit_string = " LIMIT 20 "
    if limit_start:
        limit_string = f" LIMIT {limit_start}, {limit} "

    order_by_string = " ORDER BY item_name desc"

    return frappe.db.sql(f"""
                select *
                from `tabDD Item`
                where enabled = 1
                {order_by_string}
                {limit_string}
                  """,as_dict=1)

    # return frappe.db.sql(
    #     f"""
    #                 select 
    #                     twi.web_item_name as item_name, 
    #                     twi.name as web_item_id, 
    #                     twi.item_code as item_code,
    #                     twi.stock_uom as uom,
    #                     twi.website_image,
    #                     twi.description,
    #                     tip.price_list_rate
    #                 from `tabWebsite Item` twi
    #                 join `tabItem Price` tip
    #                 on twi.item_code = tip.item_code and tip.price_list = "{settings.price_list}"
    #                 where published = 1
    #                 {order_by_string}
    #                 {limit_string}
    #                 """,
    #     as_dict=1,
    # )
