import frappe


def _get_restricted_doctypes():
    if not hasattr(frappe.local, "_hkm_restricted_dt"):
        try:
            rows = frappe.get_all(
                "HKM Restricted DocType",
                pluck="doctype_name",
                ignore_permissions=True,
            )
            frappe.local._hkm_restricted_dt = set(r for r in rows if r)
        except Exception:
            frappe.local._hkm_restricted_dt = set()
    return frappe.local._hkm_restricted_dt


def _get_user_companies(user):
    if not hasattr(frappe.local, "_hkm_user_co"):
        frappe.local._hkm_user_co = {}
    cache = frappe.local._hkm_user_co
    if user in cache:
        return cache[user]
    if user in ("Administrator", "Guest"):
        cache[user] = None
        return None
    try:
        exists = frappe.db.get_value(
            "HKM User Company Access",
            {"user": user},
            "name",
        )
    except Exception:
        cache[user] = None
        return None
    if not exists:
        cache[user] = None
        return None
    try:
        rows = frappe.get_all(
            "HKM User Company Access",
            filters={"user": user},
            pluck="company",
            ignore_permissions=True,
        )
        companies = list(set(c for c in rows if c))
        if not companies:
            cache[user] = None
            return None
    except Exception:
        cache[user] = None
        return None
    cache[user] = companies
    return companies


# Doctypes where the company value lives in a field other than `company`
_COMPANY_FIELD = {
    "Company": "name",
}


def _build_list_condition(user, doctype):
    if doctype not in _get_restricted_doctypes():
        return ""
    companies = _get_user_companies(user)
    if not companies:
        return ""
    field = _COMPANY_FIELD.get(doctype, "company")
    escaped = ", ".join(frappe.db.escape(c) for c in companies)
    return "`tab{0}`.`{1}` in ({2})".format(doctype, field, escaped)


def _make_pqc(doctype):
    def pqc(user=None):
        try:
            return _build_list_condition(user or frappe.session.user, doctype)
        except Exception:
            return ""
    return pqc


pqc_purchase_order   = _make_pqc("Purchase Order")
pqc_purchase_invoice = _make_pqc("Purchase Invoice")
pqc_sales_order      = _make_pqc("Sales Order")
pqc_sales_invoice    = _make_pqc("Sales Invoice")
pqc_payment_entry    = _make_pqc("Payment Entry")
pqc_purchase_receipt = _make_pqc("Purchase Receipt")
pqc_delivery_note    = _make_pqc("Delivery Note")
pqc_journal_entry    = _make_pqc("Journal Entry")
pqc_stock_entry      = _make_pqc("Stock Entry")
pqc_company          = _make_pqc("Company")


def has_permission(doc, user=None, permission_type=None):
    try:
        doctype = doc.doctype if hasattr(doc, "doctype") else doc
        if doctype not in _get_restricted_doctypes():
            return True
        companies = _get_user_companies(user or frappe.session.user)
        if not companies:
            return True
        field = _COMPANY_FIELD.get(doctype, "company")
        company = getattr(doc, field, None)
        if not company:
            return True
        return company in companies
    except Exception:
        return True
