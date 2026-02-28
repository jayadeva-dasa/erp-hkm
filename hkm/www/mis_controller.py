import frappe


def get_context(context):
    user = frappe.session.user
    if user == "Guest" or user == "guest":
        return frappe.throw("You need to be logged in to access this page")
    site_links = frappe.get_all(
        "ERP Domain"
        ,
        pluck = "erp_address"
    )
    mis_lists = [
        "general",
        "special",
    ]
    context.site_links = site_links
    context.mis_lists = mis_lists
    return context