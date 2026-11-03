# Step 1 - Roles cleanup: backup & review (site erp.hkmh.in)

Generated 2026-10-08 11:32. **Nothing has been deleted.** This is a read-only snapshot.

Full row-level backup: `roles_full_backup.json` (Role doc, every Has Role row, Custom DocPerm rows, DocPerm rows, code references).  Restore helper: `restore_roles.py`.

## How roles were classified

'Admin users' = the 6 accounts holding ~130 roles each (Administrator, anirudhkotha564@gmail.com, khandalkarnutan@gmail.com, nrhd@hkmjaipur.org, polampallisaivardhan2007@gmail.com, tc.sys.admin@hkmhyderabad.org). They are ignored.

A role is a delete candidate only if **no enabled non-admin user holds it** and it is not a system role. Then:

- **TIER 1 - delete now:** no references in any app's code or doctype/report JSON, no standard DocPerm. Only DB-level leftovers (Custom DocPerm rows, report/role-profile links).
- **TIER 2 - defer to module/code step:** still listed in an hkm doctype/report/page JSON or in runtime code. If you delete the role now, `bench migrate` re-creates it from that JSON. Remove the module/code first (Steps 2-3), then delete the role.
- **Not candidates:** roles shipped by frappe/erpnext (re-created on migrate, pointless to delete), roles in use by real users, system roles.

Counts: Tier 1 = 50, Tier 2 = 34, shipped-by-installed-app with no user = 15, in use = 50, system = 6.

Deleting all Tier 1 touches: 50 Role rows, 290 Has Role rows, 45 Custom DocPerm rows.

## TIER 1 - delete now

| # | Role | Disabled | Admin holders | Custom DocPerm rows (on existing / missing doctypes) | Other links to clean (report / role profile) |
|---|---|---|---|---|---|
| 1 | Agent | yes | 0 | 3 (3 / 0) | - |
| 2 | CRM Manager | no | 6 | 3 (3 / 0) | - |
| 3 | Class Evaluator | no | 6 | 0 (0 / 0) | - |
| 4 | DCC CS | no | 6 | 0 (0 / 0) | - |
| 5 | DCC Marketing | no | 6 | 2 (2 / 0) | - |
| 6 | DED Allowance Manager | no | 6 | 0 (0 / 0) | - |
| 7 | DED TC | no | 6 | 0 (0 / 0) | - |
| 8 | Drive Admin | no | 6 | 0 (0 / 0) | - |
| 9 | Drive User | no | 6 | 0 (0 / 0) | - |
| 10 | ECS Manager | no | 6 | 0 (0 / 0) | - |
| 11 | Education Manager | no | 6 | 0 (0 / 0) | - |
| 12 | Festival Pass Admin | no | 6 | 0 (0 / 0) | - |
| 13 | Foreign Donor Manager | no | 6 | 2 (1 / 1) | - |
| 14 | Gameplan Admin | no | 6 | 0 (0 / 0) | - |
| 15 | Gameplan Guest | no | 6 | 0 (0 / 0) | - |
| 16 | Gameplan Member | no | 6 | 0 (0 / 0) | - |
| 17 | HKCC Expense Observer | no | 6 | 0 (0 / 0) | - |
| 18 | HKCC Observer | no | 6 | 4 (1 / 3) | - |
| 19 | HKM MIS Manager | no | 6 | 0 (0 / 0) | - |
| 20 | HKM MIS User | no | 6 | 1 (1 / 0) | - |
| 21 | Helpdesk Contact | no | 6 | 0 (0 / 0) | - |
| 22 | Insights Admin | no | 6 | 0 (0 / 0) | - |
| 23 | Insights User | no | 6 | 0 (0 / 0) | - |
| 24 | Interviewer | no | 6 | 0 (0 / 0) | - |
| 25 | Leave Approver | no | 6 | 4 (0 / 4) | - |
| 26 | Loan Manager | yes | 0 | 6 (0 / 6) | - |
| 27 | Nexus Folk Admin | no | 6 | 0 (0 / 0) | - |
| 28 | PF Admin | no | 6 | 0 (0 / 0) | - |
| 29 | PF Checker | no | 6 | 0 (0 / 0) | - |
| 30 | PF Custodian | no | 6 | 0 (0 / 0) | - |
| 31 | PF Executive | no | 6 | 0 (0 / 0) | - |
| 32 | Prasadam Admin | no | 6 | 0 (0 / 0) | - |
| 33 | Prasadam Coupon Checker | no | 6 | 0 (0 / 0) | - |
| 34 | Prasadam Request User | no | 6 | 0 (0 / 0) | - |
| 35 | RPT Receiver | no | 6 | 0 (0 / 0) | - |
| 36 | Raven User | no | 6 | 0 (0 / 0) | - |
| 37 | Stock Notice Receiver | no | 6 | 0 (0 / 0) | - |
| 38 | Stock Notice Receiver - Jaipur | no | 6 | 0 (0 / 0) | - |
| 39 | Stock Notice Receiver - Kota | no | 6 | 0 (0 / 0) | - |
| 40 | Stock Notice Receiver - Udaipur | no | 6 | 0 (0 / 0) | - |
| 41 | Stock Viewer | no | 6 | 5 (5 / 0) | Report: Stock Summary; Report: Stock Voucher Register |
| 42 | TF Admin | no | 6 | 0 (0 / 0) | - |
| 43 | Task Giver | no | 6 | 12 (12 / 0) | - |
| 44 | Ticket Raiser | no | 6 | 1 (0 / 1) | - |
| 45 | WF Admin | no | 6 | 0 (0 / 0) | - |
| 46 | WF Driver | no | 6 | 0 (0 / 0) | - |
| 47 | WhatsApp Manager | no | 6 | 0 (0 / 0) | - |
| 48 | Wiki Approver | no | 6 | 0 (0 / 0) | - |
| 49 | Yatra Looker | no | 6 | 2 (2 / 0) | - |
| 50 | Yatra Manager | no | 6 | 0 (0 / 0) | - |

Notes for Tier 1:
- Stock Viewer is listed on reports **Stock Summary** and **Stock Voucher Register**; Stock Summary is actively used (306 visits), but through other roles. After deleting, confirm those reports still list the roles your users have.
- Task Giver has 12 and Item-related roles have many Custom DocPerm rows; they have no users, so no one loses access.
- Roles with 'missing doctypes' in the Custom DocPerm column belong to uninstalled apps (HRMS, Donor, Patron...).

## TIER 2 - defer until the module/code step

| # | Role | Std DocPerm | Custom DocPerm | Why deferred (hkm files that still list it) | Links |
|---|---|---|---|---|---|
| 1 | Account Ledger Seer | 2 | 32 | erpnext___custom/doctype/internal_adjustment/internal_adjustment.json, erpnext___custom/doctype/internal_adjustment_type/internal_adjustment_type.json, erpnext___custom/report/coa_excel/coa_excel.json (+2 more) | Report: COA Excel; Report: HKM Eagle View; Report: HKM Report A02; Report: HSN Summary B2B; Report: HSN-Vouchers; Report: Party Voucher Register; Report: Sales Register with Tax ID; Report: TDS Deduction Report - Q; Report: Vendor Bank Details; Role Profile: Vasudha Super Admin |
| 2 | Ashram Store Manager | 9 | 2 | ashram_issue_counter/doctype/ashram_library_book/ashram_library_book.json, ashram_issue_counter/doctype/ashram_library_book_inward/ashram_library_book_inward.json, ashram_issue_counter/doctype/ashram_library_book_issue/ashram_library_book_issue.json (+9 more) | Report: Ashram Library Stock; Report: Ashram Library User Status; Report: Ashram Store Devotee Report; Report: Stock Voucher Register; Role Profile: Vasudha Super Admin |
| 3 | Ashraya Devotee | 5 | 0 | ashraya_base/ashraya_listview_filter.py, ashraya_base/doctype/ashraya_candidate/ashraya_candidate.json, ashraya_base/doctype/ashraya_ceremony/ashraya_ceremony.json (+4 more) | Report: Ashraya Report; Role Profile: Vasudha Super Admin |
| 4 | Ashraya Manager | 5 | 0 | ashraya_base/ashraya_listview_filter.py, ashraya_base/doctype/ashraya_candidate/ashraya_candidate.json, ashraya_base/doctype/ashraya_ceremony/ashraya_ceremony.json (+4 more) | Report: Ashraya Report; Role Profile: Vasudha Super Admin |
| 5 | Asset Manager | 0 | 1 | erpnext___custom/report/asset_lifewise/asset_lifewise.json | Report: Asset Lifewise |
| 6 | Asset Reco | 3 | 2 | api/asset_reco.py, api/v1/asset.py, api/v1/asset_reco.py (+3 more) | Role Profile: Vasudha Super Admin |
| 7 | Bhakta Training Coordinator | 6 | 0 | bhakta_training/doctype/bhakta_training_attendance/bhakta_training_attendance.json, bhakta_training/doctype/bhakta_training_attendance_tool/bhakta_training_attendance_tool.json, bhakta_training/doctype/bhakta_training_faculty/bhakta_training_faculty.json (+3 more) | Role Profile: Vasudha Super Admin |
| 8 | DCC Cashier | 1 | 13 | firebase/doctype/firebase_app_token/firebase_app_token.json, operations/operations.py | Role Profile: Vasudha Super Admin |
| 9 | DCC Executive | 2 | 22 | erpnext___custom/doctype/hkm_redirect/hkm_redirect.json, erpnext___custom/report/asset_lifewise/asset_lifewise.json, firebase/doctype/firebase_app_token/firebase_app_token.json (+1 more) | Report: Asset Lifewise; Role Profile: Vasudha Super Admin |
| 10 | DCC Manager | 2 | 23 | api/hkm_dashboard/donor_search.py, erpnext___custom/doctype/hkm_redirect/hkm_redirect.json, erpnext___custom/report/stock_received_but_not_billed/stock_received_but_not_billed.json (+2 more) | Report: Stock Received But Not Billed; Role Profile: Vasudha Super Admin |
| 11 | DCC Preacher | 2 | 15 | erpnext___custom/doctype/hkm_redirect/hkm_redirect.json, firebase/doctype/firebase_app_token/firebase_app_token.json, operations/operations.py | Role Profile: Vasudha Super Admin |
| 12 | DD Manager | 6 | 0 | divine_dishes/doctype/dd_item/dd_item.json, divine_dishes/doctype/dd_order/dd_order.json, divine_dishes/doctype/dd_order/dd_order.py (+5 more) | Report: Orders Summary; Role Profile: Vasudha Super Admin; Workspace: Divine Dishes |
| 13 | DED Admin | 1 | 0 | firebase/doctype/firebase_app_token/firebase_app_token.json | Role Profile: Vasudha Super Admin |
| 14 | DED User | 3 | 0 | erpnext___custom/doctype/hkm_expense_voucher/hkm_expense_voucher.json, erpnext___custom/doctype/hkm_expense_voucher/hkm_expense_voucher_filter.py, erpnext___custom/doctype/hkm_expense_voucher_type/hkm_expense_voucher_type.json (+1 more) | Role Profile: Vasudha Super Admin |
| 15 | ERP Coordinator | 1 | 3 | erpnext___custom/doctype/supplier_creation_request/supplier_creation_request.json | Role Profile: Vasudha Super Admin |
| 16 | Expense Approver | 0 | 4 | erpnext___custom/doctype/cost_head/cost_head.json | - |
| 17 | FOLK Admin | 24 | 7 | firebase/doctype/firebase_app_token/firebase_app_token.json, folk_base/doctype/bed/bed.json, folk_base/doctype/bed_type/bed_type.json (+25 more) | Report: Student Rent Report; Report: Ticket Allocation; Role Profile: Vasudha Super Admin |
| 18 | FOLK Guide | 12 | 9 | ashraya_base/ashraya_listview_filter.py, firebase/doctype/firebase_app_token/firebase_app_token.json, folk_base/anniversary.py (+21 more) | Role Profile: Vasudha Super Admin |
| 19 | Guest House Manager | 6 | 2 | guest_house/doctype/gh_additional_service/gh_additional_service.json, guest_house/doctype/gh_guest_category/gh_guest_category.json, guest_house/doctype/gh_room/gh_room.json (+3 more) | Report: HSN Summary B2B; Report: HSN-Vouchers; Report: Sales Register with Tax ID; Role Profile: Vasudha Super Admin |
| 20 | HKM Cashier | 2 | 0 | erpnext___custom/doctype/hkm_expense_voucher/hkm_expense_voucher.json, erpnext___custom/doctype/hkm_expense_voucher/hkm_expense_voucher_filter.py, erpnext___custom/doctype/hkm_expense_voucher_type/hkm_expense_voucher_type.json | Role Profile: Vasudha Super Admin |
| 21 | HKM Expense Voucher Approver | 0 | 0 | erpnext___custom/doctype/hkm_expense_voucher/hkm_expense_voucher.py, erpnext___custom/doctype/hkm_expense_voucher/hkm_expense_voucher_filter.py | - |
| 22 | HKMP User | 4 | 0 | api/hkm_dashboard/hkmp_user.py, api/v1/hkm_pay.py, hkm_pay/constant.py (+12 more) | Role Profile: Vasudha Super Admin |
| 23 | HR Leave Request | 1 | 2 | erpnext___custom/doctype/hkm_attendance_request/hkm_attendance_request.json | Role Profile: Vasudha Super Admin |
| 24 | IT Manager | 6 | 5 | erpnext___custom/report/asset_lifewise/asset_lifewise.json, it/doctype/it_brand/it_brand.json, it/doctype/it_category/it_category.json (+4 more) | Report: Asset Lifewise; Role Profile: Vasudha Super Admin |
| 25 | Internal Adjustment User | 2 | 0 | erpnext___custom/doctype/internal_adjustment/internal_adjustment.json, erpnext___custom/doctype/internal_adjustment_type/internal_adjustment_type.json | Role Profile: Vasudha Super Admin |
| 26 | Item & Supplier Creator | 0 | 32 | erpnext___custom/report/asset_lifewise/asset_lifewise.json | - |
| 27 | Nexus Admin | 1 | 0 | firebase/doctype/firebase_app_token/firebase_app_token.json | Role Profile: Vasudha Super Admin |
| 28 | Nexus Preacher | 2 | 0 | erpnext___custom/doctype/hkm_redirect/hkm_redirect.json, firebase/doctype/firebase_app_token/firebase_app_token.json, operations/operations.py | Role Profile: Vasudha Super Admin |
| 29 | Nexus Sadhak | 1 | 0 | firebase/doctype/firebase_app_token/firebase_app_token.json, operations/operations.py | Role Profile: Vasudha Super Admin |
| 30 | POS Manager | 0 | 5 | erpnext___custom/report/warehouse_sales_&_stock_analysis/warehouse_sales_&_stock_analysis.json | Report: Warehouse Sales & Stock Analysis |
| 31 | POS Sales Report | 0 | 0 | api/hkm_dashboard/daily_sales_report.py | - |
| 32 | RTL Admin | 4 | 1 | erpnext___custom/doctype/rtl_leaves/rtl_leaves.json, erpnext___custom/doctype/rtl_project/rtl_project.json, erpnext___custom/doctype/rtl_project/rtl_project.py (+7 more) | Role Profile: Vasudha Super Admin |
| 33 | Temple Security User | 1 | 0 | security/doctype/temple_visitor_ping/temple_visitor_ping.json | Role Profile: Vasudha Super Admin |
| 34 | Work Request Head Manager | 1 | 0 | erpnext___custom/doctype/work_request_head/work_request_head.json | Role Profile: Vasudha Super Admin |

Caution in Tier 2: **POS Sales Report** is used by `api/hkm_dashboard/daily_sales_report.py`; **HKMP User**, **Asset Reco**, **DCC Manager**, **DD Manager**, **FOLK Guide** are checked in runtime code. Remove that code first.

## Not candidates: shipped by an installed app, no active user

Academics User, Auditor, Blogger, Cashier, Employee, Employee Self Service, Fulfillment User, Inbox User, Instructor, Maintenance Manager, Maintenance User, Projects User, Quality Manager, Student, Support Team

These get re-created by `bench migrate` (they appear in frappe/erpnext doctype permissions), so deleting them achieves nothing. Disabled ones can stay disabled.

## Other role leftovers (not roles themselves) - for later

- Role Profiles with 0 users: Accounts Finance, Item Editor (empty), Operations, Vasudha Super Admin, Warehouse Staff. 'Vasudha Super Admin' lists many of the Tier 1/2 roles; edit it before deleting those roles.
- Has Role rows pointing to roles that no longer exist: Purchase Recommender, Agriculture Manager, Purchase First Approver, Operator.
- ~100 doctypes referenced by Custom DocPerm rows no longer exist; 124 Property Setters point to missing doctypes (separate cleanup).

## Suggested manual procedure
1. `bench --site erp.hkmh.in backup --with-files` (full DB backup; this is the real safety net).
2. Review this document and `roles_full_backup.json`.
3. Remove the Tier 1 role names from Role Profile 'Vasudha Super Admin' (and any other profile).
4. Delete the Tier 1 roles from Desk (Role list). Check that their Has Role and Custom DocPerm rows are gone; delete leftover Custom DocPerm rows for them if any remain.
5. Run `bench --site erp.hkmh.in migrate` on a copy first and confirm none of the Tier 1 roles come back.
6. Tier 2 waits for Steps 2-3.

### Restore
`bench --site erp.hkmh.in execute` is not needed; run: `cd frappe-bench/sites && ../env/bin/python ../apps/hkm/cleanup_backup/01_roles/restore_roles.py <role names...|--tier1|--all>` (see script header). It re-inserts Role, Has Role and Custom DocPerm rows exactly as captured. Standard DocPerm rows come back from doctype JSON on migrate.
