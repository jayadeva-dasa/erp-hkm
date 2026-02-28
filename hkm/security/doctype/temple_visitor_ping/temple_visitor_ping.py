# Copyright (c) 2023, Narahari Dasa and contributors
# For license information, please see license.txt

from datetime import datetime
import frappe
from frappe.model.document import Document
from frappe.utils.data import today


class TempleVisitorPing(Document):
    pass


@frappe.whitelist()
def get_today_count():
    results = frappe.get_all(
        "Temple Visitor Ping",
        fields=[{frappe.qb.functions.Sum: "count", "as": "count"}],  # v16: Converted to dict syntax
        filters=[["date", "=", datetime.today().strftime("%Y-%m-%d")]],
        group_by="date",
    )
    if len(results) == 0:
        return 0
    return results[0]["count"]
