# Group A deletion log (2026-10-10)

Backup taken first: sites/erp.hkmh.in/private/backups/20261010_111741-erp_hkmh_in-* (db + files).
Code snapshots: code_snapshot/A_empty_modules.tar.gz, A_extra_files.tar.gz. DB records: db_export/A_empty_modules.json.

## DB (via delete_group_A.py --run; all counts verified 0 afterwards)
- 89 DocTypes (all empty), 11 Module Defs, 5 Workspaces + Sidebars + Desktop Icons,
  8 Reports, 1 Dashboard Chart, 1 Web Form (bon-fire-registeration),
  8 Custom Fields (folk_residency x7, Sales Invoice.gh_room_booking), Custom DocPerms, 56 Property Setters,
  Scheduled Job Type hkm.divine_dishes.tasks.every_day_evening.
- Modules: Ashram Issue Counter, Ashraya Base, Bhakta Training, Divine Dishes, FOLK Base, FOLK Trip, Folk Trip, Guest House, FLEET, IT, Security.
- The script crashed on its final log-writing step after committing, so this log was written by hand. Per-item output was not saved.

## Code
- Deleted dirs: ashram_issue_counter, ashraya_base, bhakta_training, divine_dishes, folk_base, folk_trip, guest_house, fleet, it, security
- Deleted files: api/v1/guest_house.py, patches/jan_25/add_custom_field_sales_invoice_gh_booking.py, workspace_sidebar/{ashram_store,divine_dishes,folk}.json (the last three removed by Frappe)
- Edited: hooks.py, modules.txt, patches.txt

## Left alone (follow-ups)
- Stale refs: operations/operations*.py, constants/docperms.py, fixtures JSON, www/demo-content.html, dashboard frontend guest_house, dead log_sql_query.
- Pre-existing unresolved hooks (not group A): erpnext___custom cost_head_filter.list_filter, erpnext___custom.overrides.sales_invoice, expense_summary.jinja_filters.
- 124 Property Setters and 403 Custom DocPerms already point at non-existent doctypes (orphans, pre-existing).
- Firebase and SmartPing not touched.
