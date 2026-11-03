"""Re-insert Custom Fields, Property Setters, Custom DocPerms and Scheduled Job Types of a group from db_export/<group>.json.
NOT run automatically. From frappe-bench/sites:
  ../env/bin/python ../apps/hkm/cleanup_backup/02_modules/restore_db_extras.py A_empty_modules
DocTypes/Reports/Pages/Workspaces themselves come back from the code (git or code_snapshot tar) + `bench migrate`.
"""
import sys, os, json, frappe
D = os.path.dirname(os.path.abspath(__file__))
exp = json.load(open(f"{D}/db_export/{sys.argv[1]}.json"))
frappe.init(site="erp.hkmh.in", sites_path="."); frappe.connect()
n = {}
for key, dt in [("custom_fields", "Custom Field"), ("property_setters", "Property Setter"), ("custom_docperms", "Custom DocPerm"), ("scheduled_job_types", "Scheduled Job Type")]:
    n[dt] = 0
    for row in exp.get(key, []):
        if frappe.db.exists(dt, row["name"]): continue
        row = dict(row); row["doctype"] = dt
        frappe.get_doc(row).db_insert(); n[dt] += 1
frappe.db.commit(); frappe.clear_cache(); print("restored", n)
