# Step 2 - Modules cleanup: backup & review (site erp.hkmh.in)

Generated 2026-10-09 11:59. **Nothing has been deleted.** Read-only snapshot taken after the Tier 1 role deletion.
Fresh DB backup taken just before this snapshot: `sites/erp.hkmh.in/private/backups/20261009_172714-erp_hkmh_in-database.sql.gz`.

## What is in this folder
| Path | Content |
|---|---|
| `MODULES_REVIEW.md` | This document |
| `db_export/<group>.json` | Everything the DB holds about the group: DocType docs (fields, permissions), CREATE TABLE statements, table rows (none have data), singles values, reports / pages / workspaces / charts / web forms, custom fields, property setters, custom docperms, scheduled jobs, module defs |
| `code_snapshot/<group>.tar.gz` | Copy of every file that would be removed (module directories, doctype/report/page folders, extra files), paths relative to the repo root |
| `restore_db_extras.py` | Re-inserts the Custom Fields / Property Setters / Custom DocPerms / Scheduled Job Types of a group from its JSON |

## Groups (you asked for everything to be documented)
| Group | DocTypes | Rows of data | Reports | Scheduled jobs | hooks.py lines | Files to snapshot | Code files that need editing first |
|---|---|---|---|---|---|---|---|
| A. Empty modules | 95 | 0 | 8 | 2 | 8 | 553 | 13 |
| B. Dead parts of ERPNext - Custom | 43 | 0 | 1 | 2 | 21 | 215 | 22 |
| C. HKM Integration + HKM Pay | 14 | 0 | 0 | 11 | 12 | 78 | 4 |
| E. OPTIONAL never-opened reports (not selected) | 0 | 0 | 9 | 0 | 1 | 74 | 1 |

Every doctype table in groups A, B and C has **0 rows**, so no business data is lost by deleting them. The risk is entirely in code that still references them.

## Read this before deleting - things that are NOT safe to just delete

**Group A**
- **SmartPing Settings (module SmartPing):** `hkm_approval_matrix/utils/notification_services.py` (`send_via_smartPing`, used for Purchase Order WhatsApp approvals - an in-use feature) and `hkm_general_settings` reference it. Its saved settings are empty here, but other sites may use it. Keep SmartPing unless you edit those two files first.
- **Firebase module:** used by HKM Pay and `operations/operations.py`; safe only if group C goes too (the "covered by another group" list shows this).
- Custom fields to delete with it: `folk_residency` on Asset and 6 item/transaction doctypes, and `gh_room_booking` on Sales Invoice (a patch also creates the latter: `patches/jan_25/add_custom_field_sales_invoice_gh_booking.py`).
- `hooks.py`: 5 permission-query entries, `website_generators`, 2 scheduled jobs.
- `api/__init__.py` and `hkm_dashboard/src/modules/guest_house` still import the Guest House API.

**Group B (most entangled - needs code edits, not only deletion)**
- **Freeze Transaction Settings:** wired into `doc_events["*"]` (every document's before_cancel) and `hooks_extend.on_update`.
- **HKM Budget:** `budget_utilization` hooks on Purchase Order, Purchase Invoice, Payment Entry and GL Entry, plus `extend/gl_entry.py`, plus `accounting_dimension_doctypes`.
- **MRN Usability Settings:** Stock Entry `before_insert` hook. **Block GST Entry Settings:** `extend/accounts_controller.py` (Sales/Purchase Invoice before_submit). **Work Request Head:** `overrides/HKMMaterialRequest.py`. **HKM Debug:** imported by `overrides/purchase_order/workflow_action.py`. **HKM Asset Movement / Specification:** `extend/asset.py` (Asset validate/submit) and the `Asset.specifications` custom field.
- **Internal Adjustment + Internal Adjustment Type:** queried by the HKM Eagle View report, `api/hkm_dashboard/eagle_view.py`, `expense_summary/main.py` and the dashboard Eagle View screen. Eagle View is not part of this selection, so I recommend keeping this family until you decide on Eagle View.
- Workspaces `HKM` and `Sales` and `workspace_sidebar/sales.json` link to Item Price Update, Block GST Entry Settings, Freeze/MRN settings and Work Request Head.
- Not in this group on purpose (in use): Cost Head family, HKM Active Company, HKM General Settings, HKM Redirect, Stock Check, Execution Department (+ Concern Person), Devotee, ALM, Approval Matrix, Item/Supplier Creation Request, HKM User Company Access, HKM Restricted DocType.

**Group C**
- `tasks.py` imports `hkm.hkm_pay.notify_user` at the top, and that file also holds the in-use jobs `mrn_close`, `summary_report_expenses_monthly`, `correct_item_tax_rate`. Delete HKM Pay without editing `tasks.py` and **all** of them fail to import.
- 11 scheduled jobs (see below) must be removed from `hooks.py` first (they run every minute / every 2 minutes today). `AU Bank Integration` was modified yesterday by the token refresh job, so someone configured it at some point; check other sites first.
- Dashboard frontend (`hkm_dashboard/src/modules/hkm_pay_user_management`) calls `hkm.api.hkm_dashboard.hkmp_user`.

**Group D - Module Definitions** (details in section D below)

## Suggested order
1. Group A without SmartPing (cleanest, biggest). 2. Group C (after editing `tasks.py` and `hooks.py`). 3. Group B piece by piece, starting with the standalone doctypes (QZ Printer, Suspense Tool, HKM Voucher*, HKM Expense Voucher*, Additional Cost Center, Item Price Update, RTL*, HKM HR/Attendance), leaving the entangled ones for last. 4. Tier 2 roles (they are listed per group as they become free).
After each group: edit `hooks.py` / `modules.txt` / `patches.txt` -> delete files -> `bench --site erp.hkmh.in migrate` on a copy -> delete the leftover DocType/Report/Page/Workspace records and their tables from Desk (migrate does not delete removed doctypes) -> custom fields / property setters / custom docperms listed above.

**Restore:** code from `code_snapshot/<group>.tar.gz` (or git) + `bench migrate` recreates the doctypes and empty tables; `restore_db_extras.py <group>` re-adds the custom fields etc.; the DB backup above restores everything.

---

## A. Empty modules (12 Module Defs + the 'Folk Trip' duplicate)

- DocTypes: **95** (rows of data in all their tables: **0**)
- Code snapshot: `code_snapshot/A_empty_modules.tar.gz` (553 files, 416 KB uncompressed)
- Full DB export: `db_export/A_empty_modules.json` (DocType docs incl. fields/permissions, CREATE TABLE statements, table rows, singles values, reports/pages/workspaces etc., custom fields, property setters, custom docperms, scheduled jobs, module defs)


### DocTypes
| DocType | Module | Type | Rows | Desk visits (3 mo) | Code folder |
|---|---|---|---|---|---|
| App Notification | Firebase | Doc | 0 | 0 | firebase/doctype/app_notification |
| Ashram Library Book | Ashram Issue Counter | Doc | 0 | 0 | ashram_issue_counter/doctype/ashram_library_book |
| Ashram Library Book Inward | Ashram Issue Counter | Doc | 0 | 0 | ashram_issue_counter/doctype/ashram_library_book_inward |
| Ashram Library Book Inward Item | Ashram Issue Counter | Child | 0 | 0 | ashram_issue_counter/doctype/ashram_library_book_inward_item |
| Ashram Library Book Issue | Ashram Issue Counter | Doc | 0 | 0 | ashram_issue_counter/doctype/ashram_library_book_issue |
| Ashram Library Book Issue Item | Ashram Issue Counter | Child | 0 | 0 | ashram_issue_counter/doctype/ashram_library_book_issue_item |
| Ashram Library Book Ledger | Ashram Issue Counter | Doc | 0 | 0 | ashram_issue_counter/doctype/ashram_library_book_ledger |
| Ashram Library Book Return | Ashram Issue Counter | Doc | 0 | 0 | ashram_issue_counter/doctype/ashram_library_book_return |
| Ashram Library Book Return Item | Ashram Issue Counter | Child | 0 | 0 | ashram_issue_counter/doctype/ashram_library_book_return_item |
| Ashram Store Inward | Ashram Issue Counter | Doc | 0 | 0 | ashram_issue_counter/doctype/ashram_store_inward |
| Ashram Store Inward Item | Ashram Issue Counter | Child | 0 | 0 | ashram_issue_counter/doctype/ashram_store_inward_item |
| Ashram Store Item | Ashram Issue Counter | Doc | 0 | 0 | ashram_issue_counter/doctype/ashram_store_item |
| Ashram Store Item Issue | Ashram Issue Counter | Doc | 0 | 0 | ashram_issue_counter/doctype/ashram_store_item_issue |
| Ashram Store Outward Item | Ashram Issue Counter | Child | 0 | 0 | ashram_issue_counter/doctype/ashram_store_outward_item |
| Ashram Store User | Ashram Issue Counter | Doc | 0 | 0 | ashram_issue_counter/doctype/ashram_store_user |
| Ashraya Candidate | Ashraya Base | Doc | 0 | 0 | ashraya_base/doctype/ashraya_candidate |
| Ashraya Ceremony | Ashraya Base | Doc | 0 | 0 | ashraya_base/doctype/ashraya_ceremony |
| Ashraya Ceremony Participant | Ashraya Base | Doc | 0 | 0 | ashraya_base/doctype/ashraya_ceremony_participant |
| Ashraya Guide | Ashraya Base | Doc | 0 | 0 | ashraya_base/doctype/ashraya_guide |
| Ashraya Level | Ashraya Base | Doc | 0 | 0 | ashraya_base/doctype/ashraya_level |
| Bed | FOLK Base | Doc | 0 | 0 | folk_base/doctype/bed |
| Bed Type | FOLK Base | Doc | 0 | 0 | folk_base/doctype/bed_type |
| Bhakta | Bhakta Training | Doc | 0 | 0 | bhakta_training/doctype/bhakta |
| Bhakta Training Attendance | Bhakta Training | Doc | 0 | 0 | bhakta_training/doctype/bhakta_training_attendance |
| Bhakta Training Attendance Tool | Bhakta Training | Single | - | 0 | bhakta_training/doctype/bhakta_training_attendance_tool |
| Bhakta Training Faculty | Bhakta Training | Doc | 0 | 1 (2026-09-30) | bhakta_training/doctype/bhakta_training_faculty |
| Bhakta Training Semester | Bhakta Training | Doc | 0 | 0 | bhakta_training/doctype/bhakta_training_semester |
| Bhakta Training Session | Bhakta Training | Doc | 0 | 0 | bhakta_training/doctype/bhakta_training_session |
| Bhakta Training Session Type | Bhakta Training | Doc | 0 | 0 | bhakta_training/doctype/bhakta_training_session_type |
| DD Item | Divine Dishes | Doc | 0 | 0 | divine_dishes/doctype/dd_item |
| DD Order | Divine Dishes | Doc | 0 | 0 | divine_dishes/doctype/dd_order |
| DD Order Item | Divine Dishes | Child | 0 | 0 | divine_dishes/doctype/dd_order_item |
| DD Subscription | Divine Dishes | Doc | 0 | 0 | divine_dishes/doctype/dd_subscription |
| DD Subscription Day Detail | Divine Dishes | Child | 0 | 0 | divine_dishes/doctype/dd_subscription_day_detail |
| DD User Address | Divine Dishes | Doc | 0 | 0 | divine_dishes/doctype/dd_user_address |
| DD Wallet Tx | Divine Dishes | Doc | 0 | 0 | divine_dishes/doctype/dd_wallet_tx |
| Divine Dishes Settings | Divine Dishes | Single | - | 0 | divine_dishes/doctype/divine_dishes_settings |
| Dormitory | FOLK Base | Doc | 0 | 0 | folk_base/doctype/dormitory |
| Dormitory Bed | FOLK Base | Doc | 0 | 0 | folk_base/doctype/dormitory_bed |
| Dormitory Reservation | FOLK Base | Doc | 0 | 0 | folk_base/doctype/dormitory_reservation |
| FOLK Book | FOLK Base | Doc | 0 | 0 | folk_base/doctype/folk_book |
| FOLK Calling Campaign | FOLK Base | Doc | 0 | 0 | folk_base/doctype/folk_calling_campaign |
| FOLK Calling Group | FOLK Base | Doc | 0 | 0 | folk_base/doctype/folk_calling_group |
| FOLK Donation | FOLK Base | Doc | 0 | 4 (2026-08-04) | folk_base/doctype/folk_donation |
| FOLK Event Participant | FOLK Base | Doc | 0 | 0 | folk_base/doctype/folk_event_participant |
| FOLK Event Settings | FOLK Base | Single | - | 0 | folk_base/doctype/folk_event_settings |
| FOLK Guide | FOLK Base | Doc | 0 | 3 (2026-09-29) | folk_base/doctype/folk_guide |
| FOLK Institute Degree | FOLK Base | Doc | 0 | 0 | folk_base/doctype/folk_institute_degree |
| FOLK Redirect | FOLK Base | Doc | 0 | 0 | folk_base/doctype/folk_redirect |
| FOLK Residency | FOLK Base | Doc | 0 | 0 | folk_base/doctype/folk_residency |
| FOLK Residency Guide | FOLK Base | Child | 0 | 0 | folk_base/doctype/folk_residency_guide |
| FOLK Residency Rent | FOLK Base | Doc | 0 | 0 | folk_base/doctype/folk_residency_rent |
| FOLK Residency Rent Return | FOLK Base | Doc | 0 | 0 | folk_base/doctype/folk_residency_rent_return |
| FOLK Session Registration | FOLK Base | Doc | 0 | 0 | folk_base/doctype/folk_session_registration |
| FOLK Session Registration Student | FOLK Base | Child | 0 | 0 | folk_base/doctype/folk_session_registration_student |
| FOLK Student | FOLK Base | Doc | 0 | 0 | folk_base/doctype/folk_student |
| FOLK Student App OTP | FOLK Base | Doc | 0 | 0 | folk_base/doctype/folk_student_app_otp |
| FOLK Student Book | FOLK Base | Child | 0 | 0 | folk_base/doctype/folk_student_book |
| FOLK Student Collect | FOLK Base | Doc | 0 | 0 | folk_base/doctype/folk_student_collect |
| FOLK Student Interaction | FOLK Base | Doc | 0 | 0 | folk_base/doctype/folk_student_interaction |
| FOLK Trip | FOLK Trip | Doc | 0 | 0 | folk_trip/doctype/folk_trip |
| FOLK Trip IRCTC ID | FOLK Trip | Doc | 0 | 0 | folk_trip/doctype/folk_trip_irctc_id |
| FOLK Trip Notification | FOLK Trip | Single | - | 0 | folk_trip/doctype/folk_trip_notification |
| FOLK Trip Train | Folk Trip | Doc | 0 | 0 | folk_trip/doctype/folk_trip_train |
| FOLK Trip Train Passenger | FOLK Trip | Child | 0 | 0 | folk_trip/doctype/folk_trip_train_passenger |
| FOLK Trip Train Ticket | FOLK Trip | Doc | 0 | 0 | folk_trip/doctype/folk_trip_train_ticket |
| FOLK Trip Yatri | FOLK Trip | Doc | 0 | 0 | folk_trip/doctype/folk_trip_yatri |
| FOLK Volunteer User | FOLK Base | Child | 0 | 0 | folk_base/doctype/folk_volunteer_user |
| Firebase Admin App | Firebase | Doc | 0 | 0 | firebase/doctype/firebase_admin_app |
| Firebase App Token | Firebase | Doc | 0 | 0 | firebase/doctype/firebase_app_token |
| Fleet Driver | FLEET | Doc | 0 | 0 | fleet/doctype/fleet_driver |
| Fleet Vehicle | FLEET | Doc | 0 | 0 | fleet/doctype/fleet_vehicle |
| Fleet Vehicle Movement | FLEET | Doc | 0 | 0 | fleet/doctype/fleet_vehicle_movement |
| Fleet Vehicle Refuel | FLEET | Doc | 0 | 0 | fleet/doctype/fleet_vehicle_refuel |
| GH Additional Service | Guest House | Doc | 0 | 0 | guest_house/doctype/gh_additional_service |
| GH Floor-wise Room Detail | Guest House | Child | 0 | 0 | guest_house/doctype/gh_floor_wise_room_detail |
| GH Guest Category | Guest House | Doc | 0 | 0 | guest_house/doctype/gh_guest_category |
| GH Room | Guest House | Doc | 0 | 0 | guest_house/doctype/gh_room |
| GH Room Amount Settings | Guest House | Child | 0 | 0 | guest_house/doctype/gh_room_amount_settings |
| GH Room Booking | Guest House | Doc | 0 | 0 | guest_house/doctype/gh_room_booking |
| GH Room Booking Additional Service | Guest House | Child | 0 | 0 | guest_house/doctype/gh_room_booking_additional_service |
| GH Room Booking Details | Guest House | Child | 0 | 0 | guest_house/doctype/gh_room_booking_details |
| GH Room Type | Guest House | Doc | 0 | 0 | guest_house/doctype/gh_room_type |
| GH Settings | Guest House | Single | - | 0 | guest_house/doctype/gh_settings |
| IT Brand | IT | Doc | 0 | 0 | it/doctype/it_brand |
| IT Category | IT | Doc | 0 | 0 | it/doctype/it_category |
| IT Device | IT | Doc | 0 | 0 | it/doctype/it_device |
| IT Device Specification | IT | Child | 0 | 0 | it/doctype/it_device_specification |
| IT Specification | IT | Doc | 0 | 0 | it/doctype/it_specification |
| IT UOM | IT | Doc | 0 | 0 | it/doctype/it_uom |
| IT User | IT | Doc | 0 | 0 | it/doctype/it_user |
| Notification Channel | Firebase | Doc | 0 | 0 | firebase/doctype/notification_channel |
| SmartPing Settings | SmartPing | Single | - | 0 | smartping/doctype/smartping_settings |
| Temple Visitor Ping | Security | Doc | 0 | 0 | security/doctype/temple_visitor_ping |
| User Unsubscribe | Firebase | Doc | 0 | 0 | firebase/doctype/user_unsubscribe |

Singles with non-empty saved values (exported): Bhakta Training Attendance Tool, Divine Dishes Settings, FOLK Event Settings, FOLK Trip Notification, GH Settings, SmartPing Settings

### Reports, pages, workspaces and other metadata (module-owned)
- Report: Ashram Library Stock, Ashram Library User Status, Ashram Stock, Ashram Store Devotee Report, Ashraya Report, Orders Summary, Student Rent Report, Ticket Allocation
- Workspace: Ashram, Ashram Store, Divine Dishes, FOLK, IT
- Dashboard Chart: IT Devices Category, IT User Report
- Dashboard Chart Source: Visitors Hourly
- Web Form: bon-fire-registeration
- Linked via doctype - Report (ref_doctype in scope): Ashram Library Stock, Ashram Library User Status, Ashram Stock, Ashram Store Devotee Report, Ashraya Report, Orders Summary, Student Rent Report, Ticket Allocation
- Linked via doctype - Dashboard Chart: IT Devices Category, IT User Report
- Linked via doctype - Web Form: bon-fire-registeration

### DB leftovers that must be cleaned together
- Custom Fields (on these doctypes, or linking to them from other doctypes): 8: Asset.folk_residency, Material Request Item.folk_residency, Purchase Invoice Item.folk_residency, Purchase Order Item.folk_residency, Purchase Receipt Item.folk_residency, Sales Invoice Item.folk_residency, Sales Invoice.gh_room_booking, Sales Order Item.folk_residency
- Property Setters: 58; Custom DocPerm rows: 5
- Link/Table fields in doctypes OUTSIDE this group pointing in: HKMP Setting.firebase_admin_app->Firebase Admin App

### Scheduled jobs (Scheduled Job Type rows)
- `hkm.divine_dishes.tasks.every_day_evening` (Cron 15 20 * * *) last run 2026-10-08 20:18
- `hkm.firebase.doctype.app_notification.app_notification.delete_old_app_notifications` (Daily Long ) last run 2026-10-09 07:02

### hooks.py lines to remove/edit
- line 92: `website_generators = ["DD User Address"]`
- line 115: `"FOLK Student": "hkm.folk_base.folk_listview_filter.student_query",`
- line 116: `"Ashraya Candidate": "hkm.ashraya_base.ashraya_listview_filter.query",`
- line 117: `"DD Wallet Tx": "hkm.divine_dishes.list_view_filter.query",`
- line 118: `"DD Subscription": "hkm.divine_dishes.list_view_filter.query",`
- line 119: `"DD Order": "hkm.divine_dishes.list_view_filter.query",`
- line 270: `"hkm.firebase.doctype.app_notification.app_notification.delete_old_app_notifications",`
- line 285: `"15 20 * * *": ["hkm.divine_dishes.tasks.every_day_evening"],`

### Code outside this group that references it (16 files)
**Must be edited first (not removed by any of groups A-C): 13**
- `hkm/hooks.py` -> Ashraya Candidate, DD Order, DD Subscription, DD User Address, DD Wallet Tx ...
- `hkm/hkm_approval_matrix/utils/notification_services.py` -> SmartPing Settings
- `hkm/erpnext___custom/report/hkm_eagle_view/hkm_eagle_view.py` -> FOLK Residency
- `hkm/erpnext___custom/constants/docperms.py` -> FOLK Guide
- `hkm/api/__init__.py` -> hkm.api.v1.guest_house
- `hkm/patches/jan_25/add_custom_field_sales_invoice_gh_booking.py` -> GH Room Booking
- `hkm/fixtures/custom_docperm.json` -> FOLK Guide, FOLK Residency
- `hkm/fixtures/role.json` -> FOLK Guide
- `hkm/workspace_sidebar/ashram_store.json` -> Ashram Library Book Issue, Ashram Library Book Return, Ashram Store Item Issue
- `hkm/workspace_sidebar/folk.json` -> FOLK Donation, FOLK Residency Rent, FOLK Student
- `hkm/operations/operations2.py` -> FOLK Donation, FOLK Student
- `hkm/operations/operations.py` -> App Notification, FOLK Donation, FOLK Student, Firebase Admin App, Firebase App Token ...
- `hkm_dashboard/src/modules/guest_house/api/guestHouseApi.ts` -> hkm.api.v1.guest_house

Already covered by another selected group (goes away with it): 3
- `hkm/hkm_pay/notify_user.py` -> App Notification
- `hkm/hkm_pay/doctype/hkmp_setting/hkmp_setting.json` -> Firebase Admin App
- `hkm/hkm_pay/doctype/hkmp_entry/hkmp_entry.py` -> App Notification

### Tier 2 roles that this group frees (all hkm references of the role that are inside this group / total)
- Ashram Store Manager: 12/12 references here
- Ashraya Devotee: 7/7 references here
- Ashraya Manager: 7/7 references here
- Bhakta Training Coordinator: 6/6 references here
- DCC Cashier: 1/2 references here; other references: ['operations/operations.py']
- DCC Executive: 1/4 references here; other references: ['erpnext___custom/doctype/hkm_redirect/hkm_redirect.json', 'erpnext___custom/report/asset_lifewise/asset_lifewise.json', 'operations/operations.py']
- DCC Manager: 1/5 references here; other references: ['api/hkm_dashboard/donor_search.py', 'erpnext___custom/doctype/hkm_redirect/hkm_redirect.json', 'erpnext___custom/report/stock_received_but_not_billed/stock_received_but_not_billed.json']
- DCC Preacher: 1/3 references here; other references: ['erpnext___custom/doctype/hkm_redirect/hkm_redirect.json', 'operations/operations.py']
- DD Manager: 8/8 references here
- DED Admin: 1/1 references here
- DED User: 1/4 references here; other references: ['erpnext___custom/doctype/hkm_expense_voucher/hkm_expense_voucher.json', 'erpnext___custom/doctype/hkm_expense_voucher/hkm_expense_voucher_filter.py', 'erpnext___custom/doctype/hkm_expense_voucher_type/hkm_expense_voucher_type.json']
- FOLK Admin: 28/28 references here
- FOLK Guide: 24/24 references here
- Guest House Manager: 6/6 references here
- IT Manager: 6/7 references here; other references: ['erpnext___custom/report/asset_lifewise/asset_lifewise.json']
- Nexus Admin: 1/1 references here
- Nexus Preacher: 1/3 references here; other references: ['erpnext___custom/doctype/hkm_redirect/hkm_redirect.json', 'operations/operations.py']
- Nexus Sadhak: 1/2 references here; other references: ['operations/operations.py']
- Temple Security User: 1/1 references here

---

## B. Dead parts of 'ERPNext - Custom'

- DocTypes: **43** (rows of data in all their tables: **0**)
- Code snapshot: `code_snapshot/B_dead_erpnext_custom.tar.gz` (215 files, 570 KB uncompressed)
- Full DB export: `db_export/B_dead_erpnext_custom.json` (DocType docs incl. fields/permissions, CREATE TABLE statements, table rows, singles values, reports/pages/workspaces etc., custom fields, property setters, custom docperms, scheduled jobs, module defs)


### DocTypes
| DocType | Module | Type | Rows | Desk visits (3 mo) | Code folder |
|---|---|---|---|---|---|
| Additional Cost Center | ERPNext - Custom | Doc | 0 | 0 | erpnext___custom/doctype/additional_cost_center |
| Block GST Entry | ERPNext - Custom | Child | 0 | 0 | erpnext___custom/doctype/block_gst_entry |
| Block GST Entry Settings | ERPNext - Custom | Single | - | 0 | erpnext___custom/doctype/block_gst_entry_settings |
| Freeze Transaction Settings | ERPNext - Custom | Doc | 0 | 0 | erpnext___custom/doctype/freeze_transaction_settings |
| Freeze Transaction Settings Document | ERPNext - Custom | Child | 0 | 0 | erpnext___custom/doctype/freeze_transaction_settings_document |
| HKM Asset Movement | ERPNext - Custom | Doc | 0 | 0 | erpnext___custom/doctype/hkm_asset_movement |
| HKM Asset Specification | ERPNext - Custom | Doc | 0 | 0 | erpnext___custom/doctype/hkm_asset_specification |
| HKM Asset Specification Value | ERPNext - Custom | Child | 0 | 0 | erpnext___custom/doctype/hkm_asset_specification_value |
| HKM Assets Reco | ERPNext - Custom | Doc | 0 | 0 | erpnext___custom/doctype/hkm_assets_reco |
| HKM Attendance Request | ERPNext - Custom | Doc | 0 | 0 | erpnext___custom/doctype/hkm_attendance_request |
| HKM Budget | ERPNext - Custom | Doc | 0 | 0 | erpnext___custom/doctype/hkm_budget |
| HKM Debug | ERPNext - Custom | Doc | 0 | 0 | erpnext___custom/doctype/hkm_debug |
| HKM Expense Voucher | ERPNext - Custom | Doc | 0 | 0 | erpnext___custom/doctype/hkm_expense_voucher |
| HKM Expense Voucher Type | ERPNext - Custom | Doc | 0 | 0 | erpnext___custom/doctype/hkm_expense_voucher_type |
| HKM Expense Voucher Type Account | ERPNext - Custom | Child | 0 | 0 | erpnext___custom/doctype/hkm_expense_voucher_type_account |
| HKM HR Operations | ERPNext - Custom | Single | - | 0 | erpnext___custom/doctype/hkm_hr_operations |
| HKM HR Settings | ERPNext - Custom | Single | - | 0 | erpnext___custom/doctype/hkm_hr_settings |
| HKM Leaves | ERPNext - Custom | Doc | 0 | 0 | erpnext___custom/doctype/hkm_leaves |
| HKM Voucher | ERPNext - Custom | Doc | 0 | 0 | erpnext___custom/doctype/hkm_voucher |
| HKM Voucher Detail | ERPNext - Custom | Child | 0 | 0 | erpnext___custom/doctype/hkm_voucher_detail |
| HKM Voucher Type | ERPNext - Custom | Doc | 0 | 0 | erpnext___custom/doctype/hkm_voucher_type |
| HKM Voucher Type Account | ERPNext - Custom | Child | 0 | 0 | erpnext___custom/doctype/hkm_voucher_type_account |
| Internal Adjustment | ERPNext - Custom | Doc | 0 | 0 | erpnext___custom/doctype/internal_adjustment |
| Internal Adjustment Creator | ERPNext - Custom | Doc | 0 | 0 | erpnext___custom/doctype/internal_adjustment_creator |
| Internal Adjustment Creator Account | ERPNext - Custom | Child | 0 | 0 | erpnext___custom/doctype/internal_adjustment_creator_account |
| Internal Adjustment Creator Cost Head | ERPNext - Custom | Child | 0 | 0 | erpnext___custom/doctype/internal_adjustment_creator_cost_head |
| Internal Adjustment Detail | ERPNext - Custom | Child | 0 | 0 | erpnext___custom/doctype/internal_adjustment_detail |
| Internal Adjustment Type | ERPNext - Custom | Doc | 0 | 0 | erpnext___custom/doctype/internal_adjustment_type |
| Item Price Update | ERPNext - Custom | Doc | 0 | 0 | erpnext___custom/doctype/item_price_update |
| Item Price Update Detail | ERPNext - Custom | Child | 0 | 0 | erpnext___custom/doctype/item_price_update_detail |
| MRN Usability Settings | ERPNext - Custom | Single | - | 0 | erpnext___custom/doctype/mrn_usability_settings |
| MRN Usability Settings Document | ERPNext - Custom | Child | 0 | 0 | erpnext___custom/doctype/mrn_usability_settings_document |
| QZ Printer | ERPNext - Custom | Doc | 0 | 0 | erpnext___custom/doctype/qz_printer |
| RTL Department | ERPNext - Custom | Doc | 0 | 0 | erpnext___custom/doctype/rtl_department |
| RTL Department Member | ERPNext - Custom | Child | 0 | 0 | erpnext___custom/doctype/rtl_department_member |
| RTL Holiday | ERPNext - Custom | Child | 0 | 0 | erpnext___custom/doctype/rtl_holiday |
| RTL Leaves | ERPNext - Custom | Doc | 0 | 0 | erpnext___custom/doctype/rtl_leaves |
| RTL Project | ERPNext - Custom | Doc | 0 | 1 (2026-09-01) | erpnext___custom/doctype/rtl_project |
| RTL Project Daily Status | ERPNext - Custom | Doc | 0 | 0 | erpnext___custom/doctype/rtl_project_daily_status |
| RTL Project Schedule | ERPNext - Custom | Doc | 0 | 0 | erpnext___custom/doctype/rtl_project_schedule |
| RTL Project Settings | ERPNext - Custom | Single | - | 0 | erpnext___custom/doctype/rtl_project_settings |
| Suspense Tool | ERPNext - Custom | Single | - | 0 | erpnext___custom/doctype/suspense_tool |
| Work Request Head | ERPNext - Custom | Doc | 0 | 0 | erpnext___custom/doctype/work_request_head |

Singles with non-empty saved values (exported): Block GST Entry Settings, HKM HR Operations, HKM HR Settings, MRN Usability Settings, RTL Project Settings, Suspense Tool

### Reports, pages, workspaces and other metadata (module-owned)
- Report: HKM Budget Variance
- Page: rtl_project_dashboard
- Linked via doctype - Report (ref_doctype in scope): HKM Budget Variance

### DB leftovers that must be cleaned together
- Custom Fields (on these doctypes, or linking to them from other doctypes): 7: Asset.specifications
- Property Setters: 8; Custom DocPerm rows: 13

### Scheduled jobs (Scheduled Job Type rows)
- `hkm.erpnext___custom.doctype.rtl_project.rtl_project.update_all_missed_daily_status_counts` (Cron 0 0 * * *) last run 2026-10-09 07:02
- `hkm.erpnext___custom.doctype.rtl_project_schedule.rtl_project_schedule.run_scheduled_projects` (Daily ) last run 2026-10-09 07:02

### hooks.py lines to remove/edit
- line 120: `"HKM Voucher": "hkm.erpnext___custom.doctype.hkm_voucher.hkm_voucher_filter.list_filter",`
- line 121: `"RTL Project": "hkm.erpnext___custom.doctype.rtl_project.rtl_project_filter.list",`
- line 138: `"HKM Voucher": "hkm.erpnext___custom.doctype.hkm_voucher.hkm_voucher_filter.has_single_access",`
- line 139: `"RTL Project": "hkm.erpnext___custom.doctype.rtl_project.rtl_project_filter.single",`
- line 182: `"before_cancel": "hkm.erpnext___custom.doctype.freeze_transaction_settings.freeze_transaction_settings.validate_transaction_against_frozen_date",`
- line 219: `"on_submit": "hkm.erpnext___custom.doctype.hkm_budget.budget_utilization.update_budget_utilization_on_submit",`
- line 220: `"on_cancel": "hkm.erpnext___custom.doctype.hkm_budget.budget_utilization.update_budget_utilization_on_cancel",`
- line 224: `"before_insert": "hkm.erpnext___custom.doctype.mrn_usability_settings.mrn_usability_settings.validate_mrn_settings",`
- line 233: `"hkm.erpnext___custom.doctype.hkm_budget.budget_utilization.update_budget_utilization_on_submit",`
- line 236: `"on_cancel": "hkm.erpnext___custom.doctype.hkm_budget.budget_utilization.update_budget_utilization_on_cancel",`
- line 242: `"on_submit": "hkm.erpnext___custom.doctype.hkm_budget.budget_utilization.update_budget_utilization_on_submit",`
- line 243: `"on_cancel": "hkm.erpnext___custom.doctype.hkm_budget.budget_utilization.update_budget_utilization_on_cancel",`
- line 247: `"on_submit": "hkm.erpnext___custom.doctype.hkm_budget.budget_utilization.update_budget_utilization_on_submit",`
- line 248: `"on_cancel": "hkm.erpnext___custom.doctype.hkm_budget.budget_utilization.update_budget_utilization_on_cancel",`
- line 263: `"hkm.erpnext___custom.doctype.rtl_project_schedule.rtl_project_schedule.run_scheduled_projects",`
- line 293: `"hkm.erpnext___custom.doctype.rtl_project.rtl_project.update_all_missed_daily_status_counts",`
- line 301: `# "hkm.erpnext___custom.doctype.rtl_project.rtl_email_notifications.send_deadline_reminder_emails",`
- line 305: `# "30 19 * * *": "hkm.erpnext___custom.doctype.rtl_project.rtl_email_notifications.send_daily_status_reminders",`
- line 307: `# "0 19 * * *": "hkm.erpnext___custom.doctype.rtl_project.rtl_email_notifications.send_daily_status_matrix_to_hods",`
- line 324: `"HKM Budget",`
- line 325: `"Internal Adjustment Detail",`

### Code outside this group that references it (22 files)
**Must be edited first (not removed by any of groups A-C): 22**
- `hkm/hooks_extend.py` -> hkm.erpnext___custom.doctype.freeze_transaction_settings
- `hkm/hooks.py` -> HKM Budget, HKM Voucher, Internal Adjustment Detail, RTL Project, hkm.erpnext___custom.doctype.freeze_transaction_settings ...
- `hkm/erpnext___custom/workspace/hkm/hkm.json` -> Block GST Entry Settings, Freeze Transaction Settings, Item Price Update, MRN Usability Settings, Work Request Head
- `hkm/erpnext___custom/workspace/sales/sales.json` -> Item Price Update
- `hkm/erpnext___custom/overrides/HKMMaterialRequest.py` -> Work Request Head
- `hkm/erpnext___custom/overrides/purchase_order/workflow_action.py` -> hkm.erpnext___custom.doctype.hkm_debug
- `hkm/erpnext___custom/extend/accounts_controller.py` -> Block GST Entry Settings
- `hkm/erpnext___custom/extend/gl_entry.py` -> hkm.erpnext___custom.doctype.hkm_budget
- `hkm/erpnext___custom/extend/asset.py` -> HKM Asset Movement, HKM Asset Specification
- `hkm/erpnext___custom/report/hkm_eagle_view/hkm_eagle_view.js` -> Internal Adjustment Type
- `hkm/erpnext___custom/report/hkm_eagle_view/report/voucher_wise_report/main.py` -> Internal Adjustment
- `hkm/erpnext___custom/report/hkm_eagle_view/utils/dimension_report_data_processor.py` -> Internal Adjustment Type
- `hkm/erpnext___custom/report/hkm_eagle_view/utils/columns_builder.py` -> Internal Adjustment Type
- `hkm/erpnext___custom/report/utils/income_expense_aie/column_builders.py` -> Internal Adjustment Type
- `hkm/api/hkm_dashboard/eagle_view.py` -> Internal Adjustment, Internal Adjustment Type
- `hkm/patches/v_0_0/add_custom_field_for_asset.py` -> HKM Asset Specification Value
- `hkm/expense_summary/main.py` -> Internal Adjustment
- `hkm/fixtures/custom_docperm.json` -> Additional Cost Center, HKM Budget, Item Price Update, RTL Project
- `hkm/public/js/asset_category.js` -> hkm.erpnext___custom.doctype.hkm_assets_reco
- `hkm/workspace_sidebar/sales.json` -> Item Price Update
- `hkm_dashboard/src/modules/eagle-view/components/EagleViewFilters.tsx` -> Internal Adjustment Type
- `hkm_dashboard/src/modules/asset_reco/api/assetRecoApi.ts` -> hkm.api.asset_reco

Already covered by another selected group (goes away with it): 0

### Tier 2 roles that this group frees (all hkm references of the role that are inside this group / total)
- Account Ledger Seer: 2/5 references here; other references: ['erpnext___custom/report/coa_excel/coa_excel.json', 'erpnext___custom/report/hkm_eagle_view/hkm_eagle_view.json', 'erpnext___custom/report/hkm_report_a02/hkm_report_a02.json']
- Asset Reco: 5/6 references here; other references: ['api/v1/asset.py']
- DED User: 3/4 references here; other references: ['firebase/doctype/firebase_app_token/firebase_app_token.json']
- HKM Cashier: 3/3 references here
- HKM Expense Voucher Approver: 2/2 references here
- HR Leave Request: 1/1 references here
- Internal Adjustment User: 2/2 references here
- RTL Admin: 10/10 references here
- Work Request Head Manager: 1/1 references here

---

## C. HKM Integration + HKM Pay (+ HKM API Call)

- DocTypes: **14** (rows of data in all their tables: **0**)
- Code snapshot: `code_snapshot/C_integration_and_pay.tar.gz` (78 files, 277 KB uncompressed)
- Full DB export: `db_export/C_integration_and_pay.json` (DocType docs incl. fields/permissions, CREATE TABLE statements, table rows, singles values, reports/pages/workspaces etc., custom fields, property setters, custom docperms, scheduled jobs, module defs)


### DocTypes
| DocType | Module | Type | Rows | Desk visits (3 mo) | Code folder |
|---|---|---|---|---|---|
| AU Bank Account | HKM Integration | Doc | 0 | 0 | hkm_integration/doctype/au_bank_account |
| AU Bank Integration | HKM Integration | Single | - | 0 | hkm_integration/doctype/au_bank_integration |
| AU Bank Integration Detail | HKM Integration | Child | 0 | 0 | hkm_integration/doctype/au_bank_integration_detail |
| HKM API Call | ERPNext - Custom | Doc | 0 | 0 | erpnext___custom/doctype/hkm_api_call |
| HKM Payment Request | HKM Integration | Doc | 0 | 0 | hkm_integration/doctype/hkm_payment_request |
| HKM Payment Request Detail | HKM Integration | Child | 0 | 0 | hkm_integration/doctype/hkm_payment_request_detail |
| HKMP Bank Account | HKM Pay | Doc | 0 | 0 | hkm_pay/doctype/hkmp_bank_account |
| HKMP Bank Settings | HKM Pay | Child | 0 | 0 | hkm_pay/doctype/hkmp_bank_settings |
| HKMP Entry | HKM Pay | Doc | 0 | 0 | hkm_pay/doctype/hkmp_entry |
| HKMP Payee Directory | HKM Pay | Doc | 0 | 0 | hkm_pay/doctype/hkmp_payee_directory |
| HKMP Setting | HKM Pay | Single | - | 0 | hkm_pay/doctype/hkmp_setting |
| HKMP User | HKM Pay | Doc | 0 | 0 | hkm_pay/doctype/hkmp_user |
| IndusInd Bank Integration | HKM Integration | Single | - | 0 | hkm_integration/doctype/indusind_bank_integration |
| IndusInd Bank Integration Detail | HKM Integration | Child | 0 | 0 | hkm_integration/doctype/indusind_bank_integration_detail |

Singles with non-empty saved values (exported): AU Bank Integration, HKMP Setting, IndusInd Bank Integration

### Reports, pages, workspaces and other metadata (module-owned)

### DB leftovers that must be cleaned together
- Custom Fields (on these doctypes, or linking to them from other doctypes): 0
- Property Setters: 11; Custom DocPerm rows: 0

### Scheduled jobs (Scheduled Job Type rows)
- `hkm.hkm_integration.doctype.au_bank_account.au_bank_account.auto_update_bank_txs` (Cron 30 * * * *) last run 2026-10-09 16:30
- `hkm.hkm_pay.tasks.unbilled_hkmp_user_block` (Cron 30 9 25 * *) last run 2026-09-25 09:30
- `hkm.hkm_pay.doctype.hkmp_entry.hkmp_entry.update_hkmp_payee_directory` (Cron 0 0 * * *) last run 2026-10-09 07:02
- `hkm.hkm_integration.doctype.hkm_payment_request.hkm_payment_request.update_payment_request_status` (Cron */2 * * * *) last run 2026-10-09 17:26
- `hkm.tasks.notify_users_about_low_balance` (Cron 0 10 * * *) last run 2026-10-09 10:02
- `hkm.tasks.notify_users_about_pending_bills` (Cron 0 0 */15 * *) last run 2026-10-01 07:02
- `hkm.hkm_pay.tasks.unbilled_hkmp_user_send_email` (Cron 30 9 10 * *) last run 2026-09-10 09:30
- `hkm.hkm_pay.doctype.hkmp_entry.hkmp_entry.update_transaction_status` (Cron * * * * *) last run 2026-10-09 17:26
- `hkm.hkm_integration.doctype.au_bank_integration.au_payment_api.refresh_oauth_token` (Daily ) last run 2026-10-09 07:02
- `hkm.hkm_pay.doctype.hkmp_entry.hkmp_entry.update_daily_limit` (Daily ) last run 2026-10-09 07:02
- `hkm.hkm_integration.doctype.au_bank_integration.au_bank_integration.refresh_token` (Monthly ) last run 2026-10-01 07:02

### hooks.py lines to remove/edit
- line 73: `"HKM Payment Request": "public/js/hkm_payment_request.js",`
- line 122: `"HKMP Entry": "hkm.hkm_pay.doctype.hkmp_entry.hkmp_entry_filter.list_filter",`
- line 140: `"HKMP Entry": "hkm.hkm_pay.doctype.hkmp_entry.hkmp_entry_filter.doc_filter",`
- line 264: `"hkm.hkm_pay.doctype.hkmp_entry.hkmp_entry.update_daily_limit",`
- line 265: `"hkm.hkm_integration.doctype.au_bank_integration.au_payment_api.refresh_oauth_token",`
- line 274: `"hkm.hkm_integration.doctype.au_bank_integration.au_bank_integration.refresh_token"`
- line 279: `"hkm.hkm_integration.doctype.hkm_payment_request.hkm_payment_request.update_payment_request_status",`
- line 282: `"hkm.hkm_pay.doctype.hkmp_entry.hkmp_entry.update_transaction_status",`
- line 288: `"hkm.hkm_integration.doctype.au_bank_account.au_bank_account.auto_update_bank_txs"`
- line 294: `"hkm.hkm_pay.doctype.hkmp_entry.hkmp_entry.update_hkmp_payee_directory",`
- line 311: `"30 9 10 * *": "hkm.hkm_pay.tasks.unbilled_hkmp_user_send_email",`
- line 312: `"30 9 25 * *": "hkm.hkm_pay.tasks.unbilled_hkmp_user_block",`

### Code outside this group that references it (4 files)
**Must be edited first (not removed by any of groups A-C): 4**
- `hkm/tasks.py` -> HKMP User, hkm.hkm_pay
- `hkm/hooks.py` -> HKM Payment Request, HKMP Entry, hkm.hkm_integration, hkm.hkm_pay, public/js/hkm_payment_request.js
- `hkm/fixtures/role.json` -> HKMP User
- `hkm_dashboard/src/modules/hkm_pay_user_management/api/hkmpUserApi.ts` -> hkm.api.hkm_dashboard.hkmp_user, hkm.hkm_pay

Already covered by another selected group (goes away with it): 0

### Tier 2 roles that this group frees (all hkm references of the role that are inside this group / total)
- HKMP User: 14/15 references here; other references: ['tasks.py']

---

## E. OPTIONAL (not selected): never-opened reports/page/workspaces of 'ERPNext - Custom' - for your decision only

- DocTypes: **0** (rows of data in all their tables: **0**)
- Code snapshot: `code_snapshot/E_optional_unopened_reports.tar.gz` (74 files, 359 KB uncompressed)
- Full DB export: `db_export/E_optional_unopened_reports.json` (DocType docs incl. fields/permissions, CREATE TABLE statements, table rows, singles values, reports/pages/workspaces etc., custom fields, property setters, custom docperms, scheduled jobs, module defs)


### DocTypes
| DocType | Module | Type | Rows | Desk visits (3 mo) | Code folder |
|---|---|---|---|---|---|

### Reports, pages, workspaces and other metadata (module-owned)
- Report: Asset Received But Not Billed, COA Excel, GSTR Taxwise, HKM Eagle View, HKM Report A02, ITEM With GST Rate, Purchase Department Analysis, Purchase Order Track, Stock Received But Not Billed
- Page: hkm-point-of-sale
- Workspace: HKM, Sales

### DB leftovers that must be cleaned together
- Custom Fields (on these doctypes, or linking to them from other doctypes): 0
- Property Setters: 0; Custom DocPerm rows: 0

### Scheduled jobs (Scheduled Job Type rows)
- none

### hooks.py lines to remove/edit
- line 49: `"erpnext___custom/page/hkm_point_of_sale/hkm_pos_controller.js"`

### Code outside this group that references it (1 files)
**Must be edited first (not removed by any of groups A-C): 1**
- `hkm/hooks.py` -> erpnext___custom/page/hkm_point_of_sale

Already covered by another selected group (goes away with it): 0

### Tier 2 roles that this group frees (all hkm references of the role that are inside this group / total)
- Account Ledger Seer: 3/5 references here; other references: ['erpnext___custom/doctype/internal_adjustment/internal_adjustment.json', 'erpnext___custom/doctype/internal_adjustment_type/internal_adjustment_type.json']
- DCC Manager: 1/5 references here; other references: ['api/hkm_dashboard/donor_search.py', 'erpnext___custom/doctype/hkm_redirect/hkm_redirect.json', 'firebase/doctype/firebase_app_token/firebase_app_token.json']
---

## D. Module Definitions (Module Def records, `modules.txt`)
| Module Def | What it contains | Recommendation |
|---|---|---|
| `HKM` | nothing (0 doctypes, reports, pages) - only a line in `modules.txt` | Delete the Module Def and its line in `hkm/modules.txt` |
| `ERPNext___Custom` | **in-use content:** DocTypes Execution Department Concern Person, PK Yatra, PK Yatra Batch; Reports HKM-HSN-wise-summary of outward supplies, HSN Summary B2B, HSN-Vouchers, Stock Summary, TDS Deduction Details; Page hkm-point-of-sale; Print Formats HKM - Quotation Format, HKM - Sales Invoice Format, HKM - Sales Invoices Format. It is not in `modules.txt` and has no code folder | **Do not delete.** Merge into `ERPNext - Custom` (change the `module` of these records), then delete the empty Module Def. PK Yatra / PK Yatra Batch are DB-only custom doctypes with data (6 and 14 rows) and are accounting dimensions - move them into code first or they are lost on a new site |
| `Folk Trip` (casing duplicate of `FOLK Trip`) | doctype FOLK Trip Train, report Ticket Allocation | Goes away with group A |
Also not in code but in DB only (DB-only custom doctypes): HKM Restricted DocType (5 rows), HKM User Company Access (46 rows), PK Yatra, PK Yatra Batch - all in use; export them to the repo so a fresh install has them.
Module Def JSON docs: `db_export/D_module_defs.json`.
