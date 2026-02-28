import frappe
from frappe import _
from frappe.utils.csvutils import get_csv_content_from_google_sheets, read_csv_content




def read_content(content, extension):
    error_title = _("Template Error")
    if extension not in ("csv", "xlsx", "xls"):
        frappe.throw(
            _("Import template should be of type .csv, .xlsx or .xls"),
            title=error_title,
        )

    if extension == "csv":
        data = read_csv_content(content)
    return data

def get_data_from_google_sheets(url):
    content = None
    extension = None

    if url:
        content = get_csv_content_from_google_sheets(url)
        extension = "csv"
    else:
        frappe.throw("Please put the link of Google Sheets First.")

    if not content:
        frappe.throw(_("Invalid or corrupted content for import"))

    if content:
        return read_content(content, extension)