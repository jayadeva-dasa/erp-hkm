"""Delete group A (empty modules). Usage (from frappe-bench/sites): ../env/bin/python <this> [--run]
Without --run it only reports what it would delete and aborts on any non-empty table."""
import os, sys, json, datetime
import frappe

MODULES = ["Ashram Issue Counter", "Ashraya Base", "Bhakta Training", "Divine Dishes",
           "FOLK Base", "FOLK Trip", "Folk Trip", "Guest House", "FLEET", "IT", "Security"]
RUN = "--run" in sys.argv
LOG = []

os.chdir("/home/ubuntu/frappe-bench/sites")
frappe.init(site="erp.hkmh.in", sites_path=".")
frappe.connect()

def log(kind, name, status="ok"):
    LOG.append((kind, name, status))
    print(f"{kind:22} {name}  [{status}]")

def rm(doctype, name):
    if not frappe.db.exists(doctype, name):
        return
    if RUN:
        try:
            frappe.delete_doc(doctype, name, force=True, ignore_permissions=True, ignore_missing=True)
            log(doctype, name)
        except Exception as e:
            log(doctype, name, f"ERROR {e}")
    else:
        log(doctype, name, "would delete")

doctypes = frappe.get_all("DocType", filters={"module": ["in", MODULES]},
                          fields=["name", "istable", "issingle", "custom"])
names = [d.name for d in doctypes]

# safety: abort if any data exists
blockers = []
for d in doctypes:
    if d.issingle:
        continue
    if frappe.db.table_exists(d.name) and frappe.db.count(d.name) > 0:
        blockers.append((d.name, frappe.db.count(d.name)))
cf = frappe.get_all("Custom Field", filters={"fieldname": ["in", ["folk_residency", "gh_room_booking"]]},
                    fields=["name", "dt", "fieldname"])
for c in cf:
    if frappe.db.has_column(c.dt, c.fieldname) and frappe.db.sql(
            f"select count(*) from `tab{c.dt}` where ifnull(`{c.fieldname}`,'')!=''")[0][0]:
        blockers.append((c.name, "custom field has data"))
if blockers:
    print("ABORT, data found:", blockers)
    sys.exit(1)
print(f"{len(names)} doctypes, no data. Mode: {'RUN' if RUN else 'DRY'}")

for dt in ["Workspace", "Report", "Dashboard Chart", "Web Form", "Dashboard Chart Source"]:
    if frappe.get_meta(dt).has_field("module"):
        for n in frappe.get_all(dt, filters={"module": ["in", MODULES]}, pluck="name"):
            if dt == "Workspace":
                for s in frappe.get_all("Workspace Sidebar", filters={"name": n}, pluck="name"):
                    rm("Workspace Sidebar", s)
                for i in frappe.get_all("Desktop Icon", filters={"label": n}, pluck="name"):
                    rm("Desktop Icon", i)
            rm(dt, n)

for c in cf:
    rm("Custom Field", c.name)
for n in frappe.get_all("Custom DocPerm", filters={"parent": ["in", names]}, pluck="name"):
    rm("Custom DocPerm", n)
for n in frappe.get_all("Property Setter", filters={"doc_type": ["in", names]}, pluck="name"):
    rm("Property Setter", n)
for n in frappe.get_all("Scheduled Job Type", filters={"method": ["like", "hkm.divine_dishes.%"]}, pluck="name"):
    rm("Scheduled Job Type", n)

# children first
for d in sorted(doctypes, key=lambda d: not d.istable):
    rm("DocType", d.name)
for m in MODULES:
    rm("Module Def", m)

if RUN:
    frappe.db.commit()
    with open("/home/ubuntu/frappe-bench/apps/hkm/cleanup_backup/02_modules/DELETION_LOG_A.md", "w") as f:
        f.write(f"# Group A deletion log, {datetime.datetime.now()}\n\n| Type | Name | Status |\n|---|---|---|\n")
        for k, n, s in LOG:
            f.write(f"| {k} | {n} | {s} |\n")
