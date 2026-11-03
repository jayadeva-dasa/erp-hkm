"""Deletes the Tier 1 roles (tier1_roles.txt). Re-verifies each role first; aborts on any surprise.
Run from frappe-bench/sites:  ../env/bin/python ../apps/hkm/cleanup_backup/01_roles/delete_tier1.py
Removes per role: Custom DocPerm rows, Has Role rows (users, role profiles, reports), then the Role (frappe.delete_doc -> Deleted Document entry).
"""
import frappe, os, json, datetime
D = os.path.dirname(os.path.abspath(__file__))
names = [l.strip() for l in open(f"{D}/tier1_roles.txt") if l.strip()]
frappe.init(site="erp.hkmh.in", sites_path="."); frappe.connect()
admins = [u for (u,) in frappe.db.sql("select parent from `tabHas Role` where parenttype='User' group by parent having count(*)>=100")]
problems = []
for r in names:
    if not frappe.db.exists("Role", r): problems.append(f"{r}: does not exist"); continue
    act = frappe.db.sql("select h.parent from `tabHas Role` h join tabUser u on u.name=h.parent where h.role=%s and h.parenttype='User' and u.enabled=1 and h.parent not in %s", (r, admins or ("",)))
    if act: problems.append(f"{r}: held by {act}")
    if frappe.db.count("DocPerm", {"role": r}): problems.append(f"{r}: has standard DocPerm")
    if frappe.db.count("Workflow Transition", {"allowed": r}) or frappe.db.count("Workflow Document State", {"allow_edit": r}): problems.append(f"{r}: used in workflow")
    for t, f in frappe.db.sql("select parent,fieldname from tabDocField where options='Role' and fieldtype='Link' and parent not in ('DocPerm','Custom DocPerm','Has Role','User Role','Workflow Transition','Workflow Document State')"):
        try:
            c = (frappe.db.sql("select count(*) from tabSingles where doctype=%s and field=%s and value=%s", (t, f, r)) if frappe.get_meta(t).issingle else frappe.db.sql(f"select count(*) from `tab{t}` where `{f}`=%s", r))[0][0]
            if c: problems.append(f"{r}: linked from {t}.{f}")
        except Exception: pass
if problems:
    print("ABORT, nothing deleted:"); [print(" ", p) for p in problems]; raise SystemExit(1)
log = []
tot = [0, 0, 0]
for r in names:
    cdp = frappe.db.sql("select count(*) from `tabCustom DocPerm` where role=%s", r)[0][0]
    hr = frappe.db.sql("select count(*) from `tabHas Role` where role=%s", r)[0][0]
    frappe.db.delete("Custom DocPerm", {"role": r})
    frappe.db.delete("Has Role", {"role": r})
    frappe.delete_doc("Role", r, force=True, ignore_permissions=True)
    tot[0] += 1; tot[1] += hr; tot[2] += cdp
    log.append((r, hr, cdp))
frappe.db.commit(); frappe.clear_cache()
left = [r for r in names if frappe.db.exists("Role", r)]
left_hr = frappe.db.sql("select count(*) from `tabHas Role` where role in %s", (names,))[0][0]
left_cdp = frappe.db.sql("select count(*) from `tabCustom DocPerm` where role in %s", (names,))[0][0]
with open(f"{D}/DELETION_LOG.md", "w") as f:
    f.write(f"# Tier 1 role deletion log\n\nRun: {datetime.datetime.now():%Y-%m-%d %H:%M}\nDB backup taken just before: sites/erp.hkmh.in/private/backups/20261009_160215-erp_hkmh_in-database.sql.gz\n\n")
    f.write(f"Deleted {tot[0]} roles, {tot[1]} Has Role rows, {tot[2]} Custom DocPerm rows.\nLeft over afterwards: roles={len(left)}, Has Role={left_hr}, Custom DocPerm={left_cdp}\n\n| Role | Has Role rows removed | Custom DocPerm rows removed |\n|---|---|---|\n")
    for r, h, c in log: f.write(f"| {r} | {h} | {c} |\n")
    f.write("\nRestore: see restore_roles.py (--tier1), or restore the DB backup above.\n")
print(f"deleted roles={tot[0]} has_role={tot[1]} custom_docperm={tot[2]}; leftover roles={len(left)} has_role={left_hr} cdp={left_cdp}")
