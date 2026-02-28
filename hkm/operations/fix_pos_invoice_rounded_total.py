"""
One-time fix: Set rounded_total = grand_total and base_rounded_total = base_grand_total
for POS Invoices where rounded_total is 0 but grand_total > 0 (e.g. when rounding was disabled).

Run via app runner (cursor folder is not importable):
  bench --site <site> execute hkm_jaipur.hkm_jaipur.patches.run_pos_rounded_total_fix.run_fix
  bench --site <site> execute hkm_jaipur.hkm_jaipur.patches.run_pos_rounded_total_fix.run_fix --kwargs '{"creation_date": "2025-02-09", "dry_run": true}'
"""
from __future__ import unicode_literals

import frappe
from frappe.utils import getdate, add_to_date


def run_fix(creation_date="2025-02-09", dry_run=True):
    """
    Fix POS Invoices with grand_total > 0 and rounded_total = 0.

    :param site: Optional site name (uses current if not set).
    :param creation_date: Optional date string (e.g. '2025-02-09') to limit to that day; None = all.
    :param dry_run: If True, only report what would be updated; if False, perform update.
    """
    filters = [
        ["rounded_total", "=", 0],
        ["grand_total", ">", 0],
        ["docstatus", "=", 1],
    ]
    # if creation_date:
    #     dt = getdate(creation_date)
    #     filters.append(["creation", ">=", dt])
    #     filters.append(["creation", "<", add_to_date(dt, days=1)])

    names = frappe.get_all(
        "POS Invoice",
        filters=filters,
        pluck="name",
    )
    if not names:
        frappe.msgprint("No POS Invoices found with rounded_total=0 and grand_total>0.")
        return {"updated": 0, "names": []}

    frappe.msgprint("Found {} POS Invoice(s) to fix. dry_run={}".format(len(names), dry_run))
    if dry_run:
        return {"would_update": names, "count": len(names)}

    updated = 0
    for name in names:
       
        frappe.db.set_value(
            "POS Invoice",
            name,
            {
                "rounded_total": frappe.db.get_value("POS Invoice", name, "grand_total"),
                "base_rounded_total": frappe.db.get_value("POS Invoice", name, "base_grand_total"),
            },
        )
        updated += 1
    frappe.db.commit()
    frappe.msgprint("Updated {} POS Invoice(s).".format(updated))
    return {"updated": updated, "names": names}
