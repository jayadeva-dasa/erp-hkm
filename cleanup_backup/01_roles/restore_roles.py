"""Re-insert deleted roles from roles_full_backup.json (NOT run automatically).

Usage (from frappe-bench/sites):
  ../env/bin/python ../apps/hkm/cleanup_backup/01_roles/restore_roles.py --tier1
  ../env/bin/python ../apps/hkm/cleanup_backup/01_roles/restore_roles.py --all
  ../env/bin/python ../apps/hkm/cleanup_backup/01_roles/restore_roles.py "DD Manager" "Task Giver"
Restores Role, Has Role and Custom DocPerm rows (skips ones that already exist).
Custom DocPerm rows are only restored when their doctype still exists.
Standard DocPerm rows come back from doctype JSON on `bench migrate`.
"""
import sys, json, os, frappe
D = os.path.dirname(os.path.abspath(__file__))
info = json.load(open(f"{D}/roles_full_backup.json"))
args = sys.argv[1:]
if "--all" in args: names = list(info)
elif "--tier1" in args: names = [l.strip() for l in open(f"{D}/tier1_roles.txt") if l.strip()]
elif "--tier2" in args: names = [l.strip() for l in open(f"{D}/tier2_roles.txt") if l.strip()]
else: names = args
frappe.init(site="erp.hkmh.in", sites_path="."); frappe.connect()
def put(doctype, row):
    row = dict(row); row["doctype"] = doctype
    if frappe.db.exists(doctype, row["name"]): return 0
    frappe.get_doc(row).db_insert(); return 1
n = [0, 0, 0]
for r in names:
    i = info[r]
    n[0] += put("Role", i["doc"])
    for h in i["has_role"]: n[1] += put("Has Role", h)
    for c in i["custom_docperm"]:
        if frappe.db.exists("DocType", c["parent"]): n[2] += put("Custom DocPerm", c)
frappe.db.commit(); frappe.clear_cache()
print(f"restored roles={n[0]} has_role={n[1]} custom_docperm={n[2]}")
