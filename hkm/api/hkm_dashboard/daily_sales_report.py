from datetime import datetime, timedelta
import frappe
from frappe import _


def get_daywise_dates(from_date=None, to_date=None):
    if not from_date or not to_date:
        frappe.throw(
            _("Date range is required. Use set_date_range() or provide parameters.")
        )

    start = datetime.strptime(from_date, "%Y-%m-%d")
    end = datetime.strptime(to_date, "%Y-%m-%d")

    date_list = []
    while start <= end:
        date_list.append(start.strftime("%Y-%m-%d"))
        start += timedelta(days=1)

    return date_list


def _check_pos_sales_permission():
    """Check if user has permission to access POS Sales Report."""
    user_roles = frappe.get_roles(frappe.session.user)
    if "POS Sales Report" not in user_roles and frappe.session.user != "Administrator":
        frappe.throw(_("You don't have permission to access this report."))


def _get_adjustment_amount(date, company, account, account_type):
    """Get adjustment amount for a specific account type (Cash or Bank) for a given date."""
    result = frappe.db.sql(
        """
        SELECT SUM(gl.debit - gl.credit) AS adjustment_amount
        FROM `tabGL Entry` gl
        INNER JOIN `tabAccount` a ON a.name = gl.account
        WHERE gl.posting_date = %(posting_date)s
        AND gl.company = %(company)s
        AND gl.voucher_type = 'Journal Entry'
        AND gl.is_cancelled = 0
        AND gl.against = %(account)s
        AND a.account_type = %(account_type)s
        AND a.root_type = 'Asset'
        AND a.report_type = 'Balance Sheet'
        """,
        {
            "posting_date": date,
            "company": company,
            "account": account,
            "account_type": account_type,
        },
        as_dict=True,
    )
    return (result[0].adjustment_amount or 0) if result and result[0].adjustment_amount else 0


@frappe.whitelist()
def company_list_for_sales_report():    
    company = "Touchstone Foundation Jaipur"
    return [company]

@frappe.whitelist()
def account_list_for_sales_report():
    accounts  = [
        "POS Sales Fund - Annakoot - TSFJ" ,
        "POS Sales Fund - Paraphernalia - TSFJ" ,
        "POS Sales Fund - Bakery - TSFJ" ,
        "POS Sales Fund - TSFJ" ,
    ]
    return accounts

@frappe.whitelist()
def get_daily_sales_report(from_date, to_date, company, account):
    _check_pos_sales_permission()
    date_list = get_daywise_dates(from_date, to_date)

    daily_sales_data = []
    opening_balance = 0

    for date in date_list:
        # Get total sale amount directly from SQL aggregation
        sale_result = frappe.db.sql(
            """
            SELECT SUM(debit - credit) AS sale_amount
            FROM `tabGL Entry`
            WHERE posting_date = %(posting_date)s
            AND company = %(company)s
            AND account = %(account)s
            AND is_cancelled = 0
            AND voucher_type = 'Sales Invoice'
            """,
            {
                "posting_date": date,
                "company": company,
                "account": account,
            },
            as_dict=True,
        )
        total_sale_amount = (sale_result[0].sale_amount or 0) if sale_result and sale_result[0].sale_amount else 0

        # Get adjustment amounts using helper function
        total_cash_adjustment_amount = _get_adjustment_amount(date, company, account, "Cash")
        total_bank_adjustment_amount = _get_adjustment_amount(date, company, account, "Bank")
        total_adjustments = total_cash_adjustment_amount + total_bank_adjustment_amount

        # Calculate closing balance: Opening Balance + Sales - Adjustments
        closing_balance = opening_balance + total_sale_amount - total_adjustments

        daily_sales_data.append(
            {
                "date": date,
                "opening_balance": opening_balance,
                "sale_amount": total_sale_amount,
                "cash_adjustment": total_cash_adjustment_amount,
                "bank_adjustment": total_bank_adjustment_amount,
                "total_adjustments": total_adjustments,
                "closing_balance": closing_balance,
            }
        )

        opening_balance = closing_balance

    return daily_sales_data


@frappe.whitelist()
def get_daily_sales_report_cash(from_date, to_date, company, account):
    _check_pos_sales_permission()
    date_list = get_daywise_dates(from_date, to_date)
    daily_cash_data = []
    opening_balance = 0

    for date in date_list:
        # Get cash adjustment amount using helper function
        total_cash_adjustment_amount = _get_adjustment_amount(date, company, account, "Cash")

        # Optimized query: Get cash collection directly by joining GL Entry -> Sales Invoice Item -> POS Invoice Reference -> POS Closing Entry
        cash_collection_result = frappe.db.sql(
            """
            SELECT DISTINCT
                pce.name,
                pce.cash_collection
            FROM `tabGL Entry` gl
            INNER JOIN `tabSales Invoice Item` sii ON sii.parent = gl.voucher_no
            INNER JOIN `tabPOS Invoice Reference` pir ON pir.pos_invoice = sii.pos_invoice
            INNER JOIN `tabPOS Closing Entry` pce ON pce.name = pir.parent
            WHERE gl.posting_date = %(posting_date)s
            AND gl.company = %(company)s
            AND gl.account = %(account)s
            AND gl.is_cancelled = 0
            AND gl.voucher_type = 'Sales Invoice'
            AND sii.pos_invoice IS NOT NULL
            AND pce.company = %(company)s
            AND pce.docstatus = 1
            AND pce.cash_collection IS NOT NULL
            AND pce.cash_collection > 0
            """,
            {
                "posting_date": date,
                "company": company,
                "account": account,
            },
            as_dict=True,
        )

        # Sum all distinct closing entries to avoid duplicate counting
        total_cash_collection = sum(
            entry.cash_collection or 0
            for entry in cash_collection_result
            if entry.cash_collection
        )

        # Calculate difference and closing balance
        difference = total_cash_collection - total_cash_adjustment_amount
        closing_balance = opening_balance + difference

        daily_cash_data.append(
            {
                "date": date,
                "opening_balance": opening_balance,
                "total_cash_collection": total_cash_collection,
                "total_cash_adjustment_amount": total_cash_adjustment_amount,
                "difference": difference,
                "closing_balance": closing_balance,
            }
        )

        opening_balance = closing_balance

    return daily_cash_data

