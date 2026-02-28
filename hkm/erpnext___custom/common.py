import frappe


@frappe.whitelist()
def directly_mark_cancelled(doctype, docname):
    roles = frappe.get_roles(frappe.session.user)
    if "Accounts User" not in roles:
        frappe.throw(
            f"Only Accounts Person is allowed to mark a Draft {doctype} directly to Cancelled."
        )
    document = frappe.get_doc(doctype, docname)

    if document.docstatus != 0:
        frappe.throw("Only Draft document is allowed to be set as cancelled.")
    frappe.db.set_value(doctype, docname, "docstatus", 2)
    frappe.db.commit()  # v16: REVIEW - check if needed
