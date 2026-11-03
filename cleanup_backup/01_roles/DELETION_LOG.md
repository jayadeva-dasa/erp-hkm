# Tier 1 role deletion log

Run: 2026-10-09 10:33
DB backup taken just before: sites/erp.hkmh.in/private/backups/20261009_160215-erp_hkmh_in-database.sql.gz

Deleted 50 roles, 290 Has Role rows, 45 Custom DocPerm rows.
Left over afterwards: roles=0, Has Role=0, Custom DocPerm=0

| Role | Has Role rows removed | Custom DocPerm rows removed |
|---|---|---|
| Agent | 0 | 3 |
| CRM Manager | 6 | 3 |
| Class Evaluator | 6 | 0 |
| DCC CS | 6 | 0 |
| DCC Marketing | 6 | 2 |
| DED Allowance Manager | 6 | 0 |
| DED TC | 6 | 0 |
| Drive Admin | 6 | 0 |
| Drive User | 6 | 0 |
| ECS Manager | 6 | 0 |
| Education Manager | 6 | 0 |
| Festival Pass Admin | 6 | 0 |
| Foreign Donor Manager | 6 | 2 |
| Gameplan Admin | 6 | 0 |
| Gameplan Guest | 6 | 0 |
| Gameplan Member | 6 | 0 |
| HKCC Expense Observer | 6 | 0 |
| HKCC Observer | 6 | 4 |
| HKM MIS Manager | 6 | 0 |
| HKM MIS User | 6 | 1 |
| Helpdesk Contact | 6 | 0 |
| Insights Admin | 6 | 0 |
| Insights User | 6 | 0 |
| Interviewer | 6 | 0 |
| Leave Approver | 6 | 4 |
| Loan Manager | 0 | 6 |
| Nexus Folk Admin | 6 | 0 |
| PF Admin | 6 | 0 |
| PF Checker | 6 | 0 |
| PF Custodian | 6 | 0 |
| PF Executive | 6 | 0 |
| Prasadam Admin | 6 | 0 |
| Prasadam Coupon Checker | 6 | 0 |
| Prasadam Request User | 6 | 0 |
| RPT Receiver | 6 | 0 |
| Raven User | 6 | 0 |
| Stock Notice Receiver | 6 | 0 |
| Stock Notice Receiver - Jaipur | 6 | 0 |
| Stock Notice Receiver - Kota | 6 | 0 |
| Stock Notice Receiver - Udaipur | 6 | 0 |
| Stock Viewer | 8 | 5 |
| TF Admin | 6 | 0 |
| Task Giver | 6 | 12 |
| Ticket Raiser | 6 | 1 |
| WF Admin | 6 | 0 |
| WF Driver | 6 | 0 |
| WhatsApp Manager | 6 | 0 |
| Wiki Approver | 6 | 0 |
| Yatra Looker | 6 | 2 |
| Yatra Manager | 6 | 0 |

Restore: see restore_roles.py (--tier1), or restore the DB backup above.
