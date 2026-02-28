"""HKM - Hare Krishna Movement ERP Extensions.

Comprehensive Frappe application extending ERPNext for HKM operations including:
- Budget management with multi-dimensional control
- Approval matrix system
- RTL (Real-Time Logging) project management
- Divine Dishes food management
- FOLK (Foundation of Life and Knowledge) student management
- Ashraya candidate management
- Fleet management
- Custom POS system
- Mobile app integration
- Theme customization (light/dark modes)
"""

from __future__ import unicode_literals

from . import __version__ as app_version
from hkm.fixtures import custom_fixtures

# Import report extensions
import hkm.erpnext___custom.extend.reports.accounts_payable_summary.accounts_payable_summary
import hkm.erpnext___custom.extend.reports.supplier_ledger_summary.supplier_ledger_summary
import hkm.erpnext___custom.extend.reports.general_ledger.general_ledger

# Application Metadata
app_name = "hkm"
app_title = "Hare Krishna Movement"
app_publisher = "Narahari Dasa"
app_description = "For Various Departments in HKM"
app_icon = "sitemap"
app_color = "blue"
app_email = "nrhd@hkm-group.org"
app_license = "MIT"

export_python_type_annotations = True

# ============================================================================
# ASSET INCLUDES
# ============================================================================

# Desk CSS and JavaScript
# app_include_css = "hkmj-theme.bundle.css"
app_include_js = ["hkm_app.bundle.js"]

# Page-specific JavaScript
page_js = {
    "hkm-point-of-sale": [
        "erpnext___custom/page/hkm_point_of_sale/hkm_pos_controller.js"
    ]
}

# DocType-specific JavaScript
doctype_js = {
    "Material Request": "public/js/material_request.js",
    "Purchase Order": "public/js/purchase_order.js",
    "Journal Entry": "public/js/journal_entry.js",
    "Purchase Receipt": "public/js/purchase_receipt.js",
    "Stock Entry": "public/js/stock_entry.js",
    "Purchase Invoice": "public/js/purchase_invoice.js",
    "Sales Invoice": "public/js/sales_invoice.js",
    "Item": "public/js/item.js",
    "POS Invoice": "public/js/pos_invoice.js",
    "POS Profile": "public/js/pos_profile.js",
    "POS Closing Entry": "public/js/pos_closing_entry.js",
    "Item Code Printer": "public/js/item_code_printer.js",
    "Bank Transaction": "public/js/bank_transaction.js",
    "Payment Entry": "public/js/payment_entry.js",
    "Asset Category": "public/js/asset_category.js",
}
doctype_list_js = {
    "Purchase Order": "public/js/purchase_order.js",
    "HKM Payment Request": "public/js/hkm_payment_request.js",
}

# ============================================================================
# WEBSITE CONFIGURATION
# ============================================================================

# URL routing rules
website_route_rules = [
    {"from_route": "/sl/<short_url>", "to_route": "redirect"},  # Short URL redirect
    {"from_route": "/point-of-sale", "to_route": "hkm-point-of-sale"},  # POS redirect
]

# Desk route redirects
website_redirects = [
    {"source": "/app/point-of-sale", "target": "/app/hkm-point-of-sale"},
]

# Web generators
website_generators = ["DD User Address"]

# ============================================================================
# JINJA ENVIRONMENT
# ============================================================================

jinja = {
	"methods": ["hkm.ahmedabad.custom.get_purchase_order_details"],
	"filters": ["hkm.expense_summary.jinja_filters"],
}

# ============================================================================
# INSTALLATION HOOKS
# ============================================================================
after_install = "hkm.erpnext___custom.setup.after_install"
before_uninstall = "hkm.erpnext___custom.setup.before_uninstall"

# ============================================================================
# PERMISSIONS
# ============================================================================

# List view permission query conditions
permission_query_conditions = {
    "FOLK Student": "hkm.folk_base.folk_listview_filter.student_query",
    "Ashraya Candidate": "hkm.ashraya_base.ashraya_listview_filter.query",
    "DD Wallet Tx": "hkm.divine_dishes.list_view_filter.query",
    "DD Subscription": "hkm.divine_dishes.list_view_filter.query",
    "DD Order": "hkm.divine_dishes.list_view_filter.query",
    "HKM Voucher": "hkm.erpnext___custom.doctype.hkm_voucher.hkm_voucher_filter.list_filter",
    "RTL Project": "hkm.erpnext___custom.doctype.rtl_project.rtl_project_filter.list",
    "HKMP Entry": "hkm.hkm_pay.doctype.hkmp_entry.hkmp_entry_filter.list_filter",
    "Cost_Head" : "hkm.erpnext___custom.doctype.cost_head.cost_head_filter.list_filter"
}

# Single document permission checks
has_permission = {
    "HKM Voucher": "hkm.erpnext___custom.doctype.hkm_voucher.hkm_voucher_filter.has_single_access",
    "RTL Project": "hkm.erpnext___custom.doctype.rtl_project.rtl_project_filter.single",
    "HKMP Entry": "hkm.hkm_pay.doctype.hkmp_entry.hkmp_entry_filter.doc_filter",
    "Cost Head": "hkm.erpnext___custom.doctype.cost_head.cost_head_filter.single"
}


override_whitelisted_methods = {
    "erpnext.accounts.doctype.accounting_dimension.accounting_dimension.get_dimensions":
        "hkm.erpnext___custom.doctype.cost_head.cost_head_filter.get_accounting_dimension"
}

# ============================================================================
# DOCTYPE OVERRIDES
# ============================================================================
# Custom DocType class overrides
override_doctype_class = {
    "POS Closing Entry": "hkm.erpnext___custom.overrides.HKMPOSClosingEntry.HKMPOSClosingEntry",
    "POS Invoice": "hkm.erpnext___custom.overrides.HKMPOSInvoice.HKMPOSInvoice",
    "Sales Invoice": "hkm.erpnext___custom.overrides.HKMSalesInvoice.HKMSalesInvoice",
    "Journal Entry": "hkm.erpnext___custom.overrides.HKMJournalEntry.HKMJournalEntry",
    "Material Request": "hkm.erpnext___custom.overrides.HKMMaterialRequest.HKMMaterialRequest",
    "Purchase Order": "hkm.erpnext___custom.overrides.purchase_order.HKMPurchaseOrder.HKMPurchaseOrder",
    "Purchase Invoice": "hkm.erpnext___custom.overrides.HKMPurchaseInvoice.HKMPurchaseInvoice",
    "Report": "hkm.erpnext___custom.overrides.HKMReport.HKMReport",
}

# ============================================================================
# DOCUMENT EVENTS
# ============================================================================

doc_events = {
    "*": {
        "before_cancel": "hkm.erpnext___custom.doctype.freeze_transaction_settings.freeze_transaction_settings.validate_transaction_against_frozen_date",
        "before_save": [
            "hkm.hkm_approval_matrix.main.before_save",
            "hkm.erpnext___custom.extend.cost_center.set_dimensions",
        ],
        "on_cancel": "hkm.hkm_approval_matrix.main.on_cancel",
        "before_submit": "hkm.hkm_approval_matrix.main.before_submit",
        "before_update_after_submit": "hkm.erpnext___custom.extend.cost_center.set_dimensions",
        "on_update": [
            "hkm.hooks_extend.on_update",
            "hkm.hkm_approval_matrix.main.on_update",
        ],
    },
    # Alternative approach: Exclude system documents during migration
    # "Property Setter": {},  # No validation for Property Setters
    # "Custom Field": {},     # No validation for Custom Fields
    # "DocType": {},         # No validation for DocTypes
    "Task": {"on_update": "hkm.erpnext___custom.task_notification.query"},
    "Sales Invoice": {
        # "validate": "hkm.erpnext___custom.overrides.sales_invoice.validate_extra",
        "before_submit": "hkm.erpnext___custom.extend.accounts_controller.validate_gst_entry",
    },
    "Supplier": {
        "before_insert": [
            "hkm.erpnext___custom.extend.supplier.creation_from_gstin",
            "hkm.erpnext___custom.extend.supplier.set_concerned_person",
        ],
    },
    "Item": {
        "before_insert": "hkm.erpnext___custom.extend.item.item_taxes_and_income_account_set",  # Before the document first time inserted, this will not run always whenever some changes are made to the document
        "before_insert": "hkm.erpnext___custom.extend.item.update_item_code_in_barcodes",
    },
    "Purchase Invoice": {
        "before_submit": [
            "hkm.erpnext___custom.extend.accounts_controller.validate_expense_account_for_non_stock_item",
            "hkm.erpnext___custom.extend.accounts_controller.validate_gst_entry",
        ],
        "on_submit": "hkm.erpnext___custom.doctype.hkm_budget.budget_utilization.update_budget_utilization_on_submit",
        "on_cancel": "hkm.erpnext___custom.doctype.hkm_budget.budget_utilization.update_budget_utilization_on_cancel",
    },
    "Stock Entry": {
        "before_submit": "hkm.erpnext___custom.extend.accounts_controller.validate_expense_account_for_non_stock_item",
        "before_insert": "hkm.erpnext___custom.doctype.mrn_usability_settings.mrn_usability_settings.validate_mrn_settings",
    },
    "Purchase Receipt": {
        "validate": "hkm.erpnext___custom.extend.purchase_receipt.validate",
        "on_update_after_submit": "hkm.erpnext___custom.extend.purchase_receipt.on_update_after_submit",
    },
    "Payment Entry": {
        "on_submit": [
            "hkm.erpnext___custom.extend.payment_entry.on_submit",
            "hkm.erpnext___custom.doctype.hkm_budget.budget_utilization.update_budget_utilization_on_submit",
        ],
        "before_save": "hkm.erpnext___custom.extend.payment_entry.before_save",
        "on_cancel": "hkm.erpnext___custom.doctype.hkm_budget.budget_utilization.update_budget_utilization_on_cancel",
    },
    "POS Closing Entry": {
        "validate": "hkm.erpnext___custom.extend.pos_closing_entry.validate"
    },
    "Purchase Order": {
        "on_submit": "hkm.erpnext___custom.doctype.hkm_budget.budget_utilization.update_budget_utilization_on_submit",
        "on_cancel": "hkm.erpnext___custom.doctype.hkm_budget.budget_utilization.update_budget_utilization_on_cancel",
    },
    "GL Entry": {
        "validate": "hkm.erpnext___custom.extend.gl_entry.validate",
        "on_submit": "hkm.erpnext___custom.doctype.hkm_budget.budget_utilization.update_budget_utilization_on_submit",
        "on_cancel": "hkm.erpnext___custom.doctype.hkm_budget.budget_utilization.update_budget_utilization_on_cancel",
    },
    "Asset": {
        "on_submit": "hkm.erpnext___custom.extend.asset.on_submit",
        "validate": "hkm.erpnext___custom.extend.asset.validate",
    },
}

# ============================================================================
# SCHEDULED TASKS
# ============================================================================

scheduler_events = {
    # Daily tasks
    "daily": [
        "hkm.erpnext___custom.doctype.rtl_project_schedule.rtl_project_schedule.run_scheduled_projects",
        "hkm.hkm_pay.doctype.hkmp_entry.hkmp_entry.update_daily_limit",
        "hkm.hkm_integration.doctype.au_bank_integration.au_payment_api.refresh_oauth_token",
    ],
    # Long-running daily tasks
    "daily_long": [
        "hkm.erpnext___custom.doctype.hkm_redirect.hkm_redirect.delete_temporary_short_links",
        "hkm.firebase.doctype.app_notification.app_notification.delete_old_app_notifications",
    ],
    # Monthly tasks
    "monthly": [
        "hkm.hkm_integration.doctype.au_bank_integration.au_bank_integration.refresh_token"
    ],
    # Cron-based scheduled tasks
    "cron": {
        "*/2 * * * *": [
            "hkm.hkm_integration.doctype.hkm_payment_request.hkm_payment_request.update_payment_request_status",
        ],
        "* * * * *": [
            "hkm.hkm_pay.doctype.hkmp_entry.hkmp_entry.update_transaction_status",
        ],
        # Daily at 8:15 PM: Divine Dishes evening tasks
        "15 20 * * *": ["hkm.divine_dishes.tasks.every_day_evening"],
        # Every hour at :45: Auto-update bank transactions
        "30 * * * *": [
            "hkm.hkm_integration.doctype.au_bank_account.au_bank_account.auto_update_bank_txs"
        ],
        # Daily at midnight: Close MRN (Material Receipt Note) and update RTL Project missed counts
        "0 0 * * *": [
            "hkm.tasks.mrn_close",
            "hkm.erpnext___custom.doctype.rtl_project.rtl_project.update_all_missed_daily_status_counts",
            "hkm.hkm_pay.doctype.hkmp_entry.hkmp_entry.update_hkmp_payee_directory",
            "hkm.tasks.correct_item_tax_rate"
        ],
        # Monthly Monday at 2 PM: Expense summary report
        "0 14 28-31 * *": "hkm.tasks.summary_report_expenses_monthly",
        # Daily at configured deadline reminder time: RTL Project deadline reminders
        "0 10 * * *": [
            # "hkm.erpnext___custom.doctype.rtl_project.rtl_email_notifications.send_deadline_reminder_emails",
            "hkm.tasks.notify_users_about_low_balance",
        ],
        # Daily at 7:30 PM: RTL Project daily status reminders
        # "30 19 * * *": "hkm.erpnext___custom.doctype.rtl_project.rtl_email_notifications.send_daily_status_reminders",
        # Daily at 7 PM: RTL Project status matrix to HODs
        # "0 19 * * *": "hkm.erpnext___custom.doctype.rtl_project.rtl_email_notifications.send_daily_status_matrix_to_hods",
        "0 0 */15 * *": [
            "hkm.tasks.notify_users_about_pending_bills",
        ],
        "30 9 10 * *": "hkm.hkm_pay.tasks.unbilled_hkmp_user_send_email",
        "30 9 25 * *": "hkm.hkm_pay.tasks.unbilled_hkmp_user_block",
    },
}

# ============================================================================
# CUSTOM CONFIGURATIONS
# ============================================================================

# DocTypes that support accounting dimensions
accounting_dimension_doctypes = [
    "Material Request",
    "Stock Entry",
    "HKM Budget",
    "Internal Adjustment Detail",
]

# DocTypes that use approval matrix
approval_matrix_doctypes = [
    "Purchase Order",
]

# DocTypes allowed for stock reposting
repost_allowed_doctypes = ["Stock Entry"]

# Fixtures to export/import
fixtures = custom_fixtures
