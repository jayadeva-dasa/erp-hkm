import frappe


def get_context(context):
    redirect = frappe.get_doc("HKM Redirect", frappe.form_dict.short_url)
    frappe.redirect(redirect.redirect_to)
