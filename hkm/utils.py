import frappe
from frappe.utils import flt
from frappe import _
import json


def validate_child_single_field_duplicacy(doc, child_table, child_field):
    documents = []
    for d in doc.get(child_table):
        field_value = d.get(child_field, None)
        if field_value and (field_value in documents):
            frappe.throw(
                "Row#{0} Duplicate record not allowed for {1}".format(
                    d.idx, field_value
                )
            )
        documents.append(field_value)


@frappe.whitelist()
def get_absolute_path(file_name):
    if file_name.startswith("/files/"):
        file_path = f"{frappe.utils.get_bench_path()}/sites/{frappe.utils.get_site_base_path()[2:]}/public{file_name}"
    if file_name.startswith("/private/"):
        file_path = f"{frappe.utils.get_bench_path()}/sites/{frappe.utils.get_site_base_path()[2:]}{file_name}"
    return file_path




def is_null_or_blank(value):
    """
    Check if a value is None, empty, blank, or contains only empty/blank elements.
    Supports:
        - None
        - Blank strings
        - Empty lists
        - Empty dicts
        - Lists of dicts or nested structures

    Args:
        value: Any Python object.

    Returns:
        bool: True if value is None/empty/blank; otherwise, False.
    """

    # Case 1: None
    if value is None:
        return True

    # Case 2: String
    if isinstance(value, str):
        return value.strip() == ""

    # Case 3: Dict → True if empty OR all values inside are null/blank
    if isinstance(value, dict):
        if not value:
            return True
        return all(is_null_or_blank(v) for v in value.values())

    # Case 4: List or Tuple → True if empty OR each element is null/blank
    if isinstance(value, (list, tuple)):
        if not value:
            return True
        return all(is_null_or_blank(v) for v in value)

    # Other types (int, float, bool, object) → Count as NOT blank
    return False
