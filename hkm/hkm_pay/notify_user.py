import frappe
from frappe import _
from frappe.utils import get_files_path, format_datetime
import os
import json
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime


@frappe.whitelist()
def send_statement_email(user, start_date=None, end_date=None):
    """
    Send email to user with Excel statement of their transactions.

    Args:
        user: HKMP User name (links to User doctype)
        start_date: Start date of the transactions
        end_date: End date of the transactions
    """
    try:
        if not frappe.db.exists("HKMP User", user):
            frappe.throw("HKMP User not found")
        # Get user email from HKMP User -> User
        user_doc = frappe.get_doc("HKMP User", user)

        # Get pending bills with all fields
        condition = """ 
            AND is_return = 0 
            AND bill_received = 0 
            AND status = 'Success'
        """

        query_params = [user_doc.name]

        if start_date and end_date:
            condition = " AND creation BETWEEN %s AND %s"
            query_params.extend([start_date, end_date])
            # Column order when date range is provided: Transaction Date, Company, Status, Beneficiary Name, VPA, UTR, Amount, Remarks, Is Return, Bill Received
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
        else:
            # Base query selection when no date range - standard fields only
            query_selection = """
                creation as `Transaction Date`,
                company as Company,
                beneficiary_name as `Beneficiary Name`,
                upi_id as `VPA (UPI)`,
                customer_ref_no as UTR,
                amount as Amount,
                remarks as Remarks
            """

        query = f"""
            SELECT 
                {query_selection}
            FROM `tabHKMP Entry`        
            WHERE user = %s 
            AND docstatus = 1 
            {condition}
            ORDER BY creation DESC
        """

        pending_bills = frappe.db.sql(
            query,
            tuple(query_params),
            as_dict=True,
        )

        if not pending_bills:
            return

        # Create Excel file
        file_path, file_name = create_transaction_excel(
            user_doc.full_name, pending_bills, start_date, end_date
        )

        # Generate email HTML body
        email_html = generate_statement_email_html(
            user_doc.full_name, len(pending_bills), start_date, end_date
        )

        # Send email with attachment
        with open(file_path, "rb") as f:
            file_content = f.read()

        frappe.sendmail(
            recipients=[user_doc.name],
            reference_doctype="HKMP User",
            reference_name=user_doc.name,
            subject=f"HKM Pay Transaction Statement - {user_doc.full_name} - {len(pending_bills)} Pending Transactions",
            message=email_html,
            delayed=False,
            header=["HKMP Transaction Statement", "blue"],
            attachments=[{"fname": file_name, "fcontent": file_content}],
        )

        # Delete temporary file
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        if start_date and end_date:
            frappe.throw(f"{str(e)}")
        frappe.log_error(
            message=f"Error sending statement email to user {user}: {str(e)}",
            title="HKMP Statement Email Error",
        )
        return {"success": False, "message": f"Error: {str(e)}"}


def create_transaction_excel(user, transactions, start_date, end_date):
    """
    Create Excel file with transaction data.

    Args:
        user: HKMP User name
        transactions: List of transaction dictionaries from SQL result

    Returns:
        tuple: (file_path, file_name)
    """
    if not transactions:
        raise ValueError("No transactions provided")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Transactions"

    # Define border style
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    # Header style
    header_fill = PatternFill(
        start_color="4472C4", end_color="4472C4", fill_type="solid"
    )
    header_font = Font(bold=True, size=11, color="FFFFFF")

    # Get all field names from first transaction (already formatted with aliases from SQL)
    all_fields = list(transactions[0].keys())

    # Headers are the field names from SQL aliases
    headers = all_fields

    # Write headers
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(
            horizontal="center", vertical="center", wrap_text=True
        )
        cell.border = thin_border

    # Write data rows
    for row_idx, transaction in enumerate(transactions, 2):
        # Write all fields
        for col_idx, fieldname in enumerate(all_fields, 1):
            value = transaction.get(fieldname)

            # Special handling for Transaction Date field
            if fieldname == "Transaction Date":
                if value:
                    # Handle datetime object or string
                    if isinstance(value, str):
                        # Parse datetime string
                        try:
                            dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
                        except ValueError:
                            try:
                                dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                            except ValueError:
                                formatted_value = value
                            else:
                                formatted_value = format_datetime(
                                    dt, "dd-MMM-yyyy HH:mm:ss"
                                )
                        else:
                            formatted_value = format_datetime(
                                dt, "dd-MMM-yyyy HH:mm:ss"
                            )
                    elif hasattr(value, "strftime"):
                        # Already a datetime object
                        formatted_value = format_datetime(value, "dd-MMM-yyyy HH:mm:ss")
                    else:
                        formatted_value = str(value)
                else:
                    formatted_value = ""
                value = formatted_value
            # Handle None values
            elif value is None:
                value = ""
            # Handle JSON fields
            elif isinstance(value, (dict, list)):
                value = json.dumps(value)

            cell = ws.cell(row=row_idx, column=col_idx)
            cell.value = value
            cell.border = thin_border
            cell.alignment = Alignment(vertical="center", wrap_text=True)

    # Set column widths (auto-adjust based on content)
    for col_num in range(1, len(headers) + 1):
        column_letter = get_column_letter(col_num)
        max_length = 0

        # Check header length
        header_cell = ws.cell(row=1, column=col_num)
        if header_cell.value:
            max_length = len(str(header_cell.value))

        # Check data lengths
        for row in ws.iter_rows(
            min_row=2, max_row=ws.max_row, min_col=col_num, max_col=col_num
        ):
            cell = row[0]
            if cell.value:
                cell_length = len(str(cell.value))
                if cell_length > max_length:
                    max_length = cell_length

        # Set width with some padding (min 10, max 50)
        adjusted_width = min(max(max_length + 2, 10), 50)
        ws.column_dimensions[column_letter].width = adjusted_width

    # Freeze header row
    ws.freeze_panes = "A2"

    # Save file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"HKMP_Statement_{user}_{timestamp}.xlsx"
    file_path = os.path.join(get_files_path(), file_name)
    wb.save(file_path)

    return file_path, file_name


def generate_statement_email_html(user_name, transaction_count, start_date, end_date):
    """
    Generate HTML email body for transaction statement.

    Args:
        user_name: Full name of the user
        transaction_count: Number of transactions
        start_date: Start date of the transactions (optional)
        end_date: End date of the transactions (optional)

    Returns:
        str: HTML email content
    """
    # Format dates if provided
    date_range_text = ""
    if start_date and end_date:
        try:
            start_formatted = format_datetime(start_date, "dd-MMM-yyyy")
            end_formatted = format_datetime(end_date, "dd-MMM-yyyy")
            date_range_text = f"from {start_formatted} to {end_formatted}"
        except (TypeError, ValueError):
            date_range_text = f"from {start_date} to {end_date}"

    # Generate statement details section
    if start_date and end_date:
        statement_section = f"""
            <p style="color: #555; font-size: 14px; line-height: 1.8; margin: 0 0 20px 0;">
                Please find attached your transaction statement containing <strong>{transaction_count} transaction(s)</strong> 
                {date_range_text}.
            </p>
            
            <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 4px;">
                <h4 style="color: #856404; margin: 0 0 10px 0; font-size: 15px;">
                    📋 Statement Details
                </h4>
                <ul style="color: #856404; font-size: 13px; margin: 0; padding-left: 20px; line-height: 1.8;">
                    <li>Total Transactions: <strong>{transaction_count}</strong></li>
                    <li>Date Range: <strong>{date_range_text}</strong></li>
                </ul>
            </div>
        """
    else:
        statement_section = f"""
            <p style="color: #555; font-size: 14px; line-height: 1.8; margin: 0 0 20px 0;">
                Please find attached your transaction statement containing <strong>{transaction_count} pending transaction(s)</strong> 
                that require bill submission.
            </p>
            
            <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 4px;">
                <h4 style="color: #856404; margin: 0 0 10px 0; font-size: 15px;">
                    📋 Statement Details
                </h4>
                <ul style="color: #856404; font-size: 13px; margin: 0; padding-left: 20px; line-height: 1.8;">
                    <li>Total Pending Transactions: <strong>{transaction_count}</strong></li>
                </ul>
            </div>
            
            <div style="background-color: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 20px 0; border-radius: 4px;">
                <h4 style="color: #155724; margin: 0 0 10px 0; font-size: 15px;">
                    📝 Action Required
                </h4>
                <p style="color: #155724; font-size: 13px; margin: 0; line-height: 1.8;">
                    Please submit the bills for these transactions to the <strong>Accounts Department</strong> at your earliest convenience.
                </p>
            </div>
        """

    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 8px 8px 0 0;">
            <h2 style="color: #ffffff; margin: 0; text-align: center;">
                HKM Pay Transaction Statement
            </h2>
        </div>
        
        <div style="background-color: #f8f9fa; padding: 30px; border: 1px solid #dee2e6; border-top: none;">
            <p style="color: #333; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                Hare Krishna! <br/> <strong>{user_name}</strong>,
            </p>
            
            {statement_section}
            
            <p style="color: #555; font-size: 14px; line-height: 1.8; margin: 20px 0 0 0;">
                If you have any questions or need assistance, please contact Accounts Department.
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




def send_notification_to_user():
    """
    Send low balance notifications to users whose available amount
    is 10% or less of their advance limit.
    Uses optimized SQL query to filter at database level.
    """
    setting_doc = frappe.get_cached_doc("HKMP Setting")
    if not setting_doc.firebase_admin_app:
        print("No Firebase admin app found")
        return

    # SQL query to get users with low balance (available_amt <= 10% of advance_limit)
    # Filters at database level for better performance
    users_with_low_balance = frappe.db.sql(
        """
        SELECT name
        FROM `tabHKMP User`
        WHERE enabled = 1
            AND advance_limit > 0
            AND COALESCE(available_amt, 0) <= (advance_limit * 0.1)
        """,
        as_dict=True,
    )

    print("Users with low balance:", users_with_low_balance)
    if not users_with_low_balance:
        return

    # Create notifications for users with low balance
    for user in users_with_low_balance:
        frappe.get_doc(
            {
                "doctype": "App Notification",
                "app": setting_doc.firebase_admin_app,
                "user": user.name,
                "subject": "HKMP Low Balance Notification",
                "message": "Low available limit. Please submit bills to Accounts.",
            }
        ).insert(ignore_permissions=True)

    frappe.db.commit()  # v16: REVIEW - check if needed
