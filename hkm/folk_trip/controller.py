import frappe
from frappe.desk.reportview import get_filters_cond, get_match_cond
@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def lead_query(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql("""
        SELECT name, full_name
        FROM `tabFOLK Student`
        WHERE 1
            AND {key} LIKE %(txt)s
                -- OR lead_name LIKE %(txt)s
                -- OR company_name LIKE %(txt)s)
            {mcond}
        LIMIT %(start)s, %(page_len)s
    """.format(**{
            'key': searchfield,
            'mcond':get_match_cond(doctype)
        }), {
        'txt': "%{}%".format(txt),
        '_txt': txt.replace("%", ""),
        'start': start,
        'page_len': page_len
    })