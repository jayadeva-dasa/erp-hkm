import frappe

EXEMPT_DOCTYPES = ["POS Invoice"]


def letterhead_query(self, method=None):
    if self.doctype in EXEMPT_DOCTYPES:
        return
    if hasattr(self, "letter_head") and self.get("company"):
        frappe.db.set_value(
            self.doctype,
            self.name,
            "letter_head",
            frappe.db.get_value("Company", self.get("company"), "default_letter_head"),
        )
