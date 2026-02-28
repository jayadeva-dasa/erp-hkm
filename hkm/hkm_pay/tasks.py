import frappe
from datetime import datetime
from frappe.utils import getdate, nowdate, add_months, get_first_day, get_last_day, format_date

from hkm.hkm_pay.notify_user import create_transaction_excel

"""
BLOCK HKMP USER AT 25TH OF EVERY MONTH
"""

def update_creation_datetime():
    for i in frappe.get_all("HKM Payment Request", fields=["name" , "creation"]):
        frappe.db.set_value("HKM Payment Request", i.name, "request_creation", i.creation)
    frappe.db.commit()

def update_bill_restriction_status(payment_user):

    if not frappe.db.get_value("HKMP User", payment_user, "bill_submission_restriction_enabled"):
        print("Bill submission restriction is not enabled for this user")
        return

    bill_submission_upto_date = frappe.db.get_value("HKMP User", payment_user, "bill_submission_upto_date")

    if not bill_submission_upto_date:
        print("Bill submission up to date not found for this user")
        return
    print(f"Bill submission up to date: {bill_submission_upto_date}")
    print(f"User: {payment_user}")
    exists = frappe.db.exists(
        "HKMP Entry",
        {
            "docstatus": 1,
            "status": "Success",
            "bill_received": 0,
            "is_return": 0,
            "user": payment_user,
            "creation": ("<=", f"{bill_submission_upto_date} 23:59:59"),
        },
    )

    print(f"Exists: {exists}")
    if not exists:
        print("No unbilled transactions found for this user")
        frappe.db.set_value("HKMP User", payment_user, "bill_submission_restriction_enabled", 0)
    else:
        print("Unbilled transactions found for this user")

    frappe.db.commit()  # v16: OK - background task


def unbilled_hkmp_user_block():

    last_month = add_months(getdate(nowdate()), -1)
    to_date = get_last_day(last_month)

    users = frappe.db.sql_list("""
        SELECT DISTINCT user
        FROM `tabHKMP Entry`
        WHERE docstatus = 1
          AND status = "Success"
          AND bill_received = 0
          AND is_return = 0
          AND creation <= %(to_date)s
    """, {
        "to_date": f"{to_date} 23:59:59",
    })

    for u in users:
        frappe.db.set_value("HKMP User", u, "bill_submission_restriction_enabled", 1)
        frappe.db.set_value("HKMP User", u, "bill_submission_upto_date", to_date)    
    

    frappe.db.commit()  # v16: OK - background task


def unbilled_hkmp_user_send_email():
    """
    Send email notification to users with unbilled transactions up to previous month.
    Warning them that their account will be blocked if bills are not submitted.
    """
    import os

    last_month = add_months(getdate(nowdate()), -1)
    to_date = get_last_day(last_month)

    # Get users with unbilled transactions from previous month
    users_with_unbilled = frappe.db.sql("""
        SELECT DISTINCT user
        FROM `tabHKMP Entry`
        WHERE docstatus = 1
          AND bill_received = 0
          AND is_return = 0
          AND status = 'Success'
          AND creation <= %(to_date)s
    """, {
        "to_date": f"{to_date} 23:59:59",
    }, as_dict=True)

    if not users_with_unbilled:
        print("No users with unbilled transactions found for previous month.")
        return

    print(f"Sending warning emails to {len(users_with_unbilled)} users with unbilled transactions")

    for user_record in users_with_unbilled:
        try:
            user = user_record.get("user")
            
            if not frappe.db.exists("HKMP User", user):
                continue

            user_doc = frappe.get_doc("HKMP User", user)

            # Get unbilled transactions for this user from previous month
            query_selection = """
                creation as `Transaction Date`,
                company as Company,
                status as Status,
                beneficiary_name as `Beneficiary Name`,
                upi_id as `VPA (UPI)`,
                customer_ref_no as UTR,
                amount as Amount,
                remarks as Remarks,
                CASE WHEN is_return = 1 THEN 'Yes' ELSE 'No' END as `Is Return`,    
                CASE WHEN bill_received = 1 THEN 'Yes' ELSE 'No' END as `Bill Received`
            """

            query = f"""
                SELECT 
                    {query_selection}
                FROM `tabHKMP Entry`        
                WHERE user = %s 
                AND docstatus = 1 
                AND bill_received = 0
                AND is_return = 0
                AND status = 'Success'
                  AND creation <= %s
                ORDER BY creation DESC
            """

            unbilled_transactions = frappe.db.sql(
                query,
                (user_doc.name, f"{to_date} 23:59:59"),
                as_dict=True,
            )

            if not unbilled_transactions:
                continue

            # Create Excel file with unbilled transactions
            file_path, file_name = create_transaction_excel(
                user_doc.full_name, 
                unbilled_transactions, 
                None,  # No start date - all transactions up to end date
                f"{to_date} 23:59:59"
            )

            # Generate warning email HTML
            email_html = generate_warning_email_html(
                user_doc.full_name, 
                len(unbilled_transactions), 
                to_date
            )

            # Send email with attachment
            with open(file_path, "rb") as f:
                file_content = f.read()

            frappe.sendmail(
                recipients=[user_doc.user],
                reference_doctype="HKMP User",
                reference_name=user_doc.name,
                subject=f"⚠️ URGENT: Account Blocking Warning - {len(unbilled_transactions)} Pending Bills - {user_doc.full_name}",
                message=email_html,
                delayed=False,
                header=["URGENT: Account Blocking Warning", "red"],
                attachments=[{"fname": file_name, "fcontent": file_content}],
            )

            # Delete temporary file
            if os.path.exists(file_path):
                os.remove(file_path)

            print(f"Warning email sent to {user_doc.name} for {len(unbilled_transactions)} unbilled transactions")

        except Exception as e:
            frappe.log_error(
                message=f"Error sending warning email to user {user}: {str(e)}",
                title="HKMP Warning Email Error",
            )
            print(f"Error sending email to {user}: {str(e)}")
            continue

    frappe.db.commit()  # v16: OK - background task




def generate_warning_email_html(user_name, transaction_count, end_date):
    """
    Generate HTML email body for account blocking warning with unbilled transactions.

    Args:
        user_name: Full name of the user
        transaction_count: Number of unbilled transactions
        end_date: End date of the period (all transactions up to this date)

    Returns:
        str: HTML email content
    """
    # Format dates
    try:
        end_formatted = format_date(end_date, "dd-MMM-yyyy")
        date_range_text = f"up to {end_formatted}"
    except (TypeError, ValueError):
        date_range_text = f"up to {end_date}"

    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); padding: 20px; border-radius: 8px 8px 0 0;">
            <h2 style="color: #ffffff; margin: 0; text-align: center;">
                ⚠️ URGENT: Account Blocking Warning
            </h2>
        </div>
        
        <div style="background-color: #f8f9fa; padding: 30px; border: 1px solid #dee2e6; border-top: none;">
            <p style="color: #333; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                Hare Krishna! <br/> <strong>{user_name}</strong>,
            </p>
            
            <div style="background-color: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; margin: 20px 0; border-radius: 4px;">
                <h4 style="color: #721c24; margin: 0 0 10px 0; font-size: 15px;">
                    🚨 URGENT ACTION REQUIRED
                </h4>
                <p style="color: #721c24; font-size: 14px; margin: 0; line-height: 1.8;">
                    <strong>Your account is going to be blocked</strong> because you have <strong>{transaction_count} unbilled transaction(s)</strong> from the previous month that have not been submitted.
                </p>
            </div>
            
            <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 4px;">
                <h4 style="color: #856404; margin: 0 0 10px 0; font-size: 15px;">
                    📋 Unbilled Transaction Details
                </h4>
                <ul style="color: #856404; font-size: 13px; margin: 0; padding-left: 20px; line-height: 1.8;">
                    <li>Period: <strong>{date_range_text}</strong></li>
                    <li>Total Unbilled Transactions: <strong>{transaction_count}</strong></li>
                    <li>Status: <strong>Bills Not Submitted</strong></li>
                </ul>
            </div>
            
            <div style="background-color: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 20px 0; border-radius: 4px;">
                <h4 style="color: #155724; margin: 0 0 10px 0; font-size: 15px;">
                    ✅ To Avoid Account Blocking
                </h4>
                <p style="color: #155724; font-size: 13px; margin: 0 0 10px 0; line-height: 1.8;">
                    Please submit all pending bills to the <strong>Accounts Department</strong> immediately to avoid any inconvenience.
                </p>
                <p style="color: #155724; font-size: 13px; margin: 0; line-height: 1.8;">
                    <strong>Attached:</strong> Detailed statement of all unbilled transactions for your reference.
                </p>
            </div>
            
            <div style="background-color: #e7f3ff; border-left: 4px solid #0056b3; padding: 15px; margin: 20px 0; border-radius: 4px;">
                <h4 style="color: #004085; margin: 0 0 10px 0; font-size: 15px;">
                    ℹ️ Important Information
                </h4>
                <p style="color: #004085; font-size: 13px; margin: 0; line-height: 1.8;">
                    If bills are not submitted promptly, your account will be blocked on the 20th of this month, and you will not be able to make any transactions until the bills are cleared.
                </p>
            </div>
            
            <p style="color: #555; font-size: 14px; line-height: 1.8; margin: 20px 0 0 0;">
                For any queries or assistance, please contact the <strong>Accounts Department</strong> immediately.
            </p>
        </div>
        
        <div style="background-color: #6c757d; padding: 15px; border-radius: 0 0 8px 8px; text-align: center;">
            <p style="color: #ffffff; font-size: 12px; margin: 0;">
                This is an automated message. Please do not reply to this email.
            </p>
            <p style="color: #d1d1d1; font-size: 11px; margin: 10px 0 0 0;">
                © {datetime.now().year} HKM Jaipur. All rights reserved.
            </p>
        </div>
    </div>
    """