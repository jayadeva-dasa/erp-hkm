#!/usr/bin/env python3
"""
Supplier Verification Email System with Excel Attachment

Sends emails with Excel attachment for concerned persons to verify and complete supplier information.
"""

import frappe
from frappe import _
from frappe.utils import nowdate, get_files_path
import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


TEST_EMAIL = "nrhd@hkmjaipur.org"
VISHNU_EMAIL = "vishnu.sharma@hkmjaipur.org"


def get_supplier_complete_data(concerned_person):
    """Get complete supplier data with all fields for Excel"""
    
    suppliers = frappe.db.sql("""
        SELECT 
            s.name as supplier_id,
            s.supplier_name,
            s.pan,
            s.gstin,
            s.supplier_creation_request,
            s.owner,
            s.custom_aadhar_no
        FROM `tabSupplier` s
        WHERE s.custom_concerned_person = %(concerned_person)s
            AND s.disabled = 0
        ORDER BY s.supplier_name
    """, {"concerned_person": concerned_person}, as_dict=1)
    
    # For each supplier, get address, contact, and bank details
    for supplier in suppliers:
        
        # Get address from Dynamic Link
        address_data = frappe.db.sql("""
            SELECT 
                a.address_line1,
                a.address_line2,
                a.city,
                a.state,
                a.pincode
            FROM `tabDynamic Link` dl
            INNER JOIN `tabAddress` a ON a.name = dl.parent
            WHERE dl.link_doctype = 'Supplier'
                AND dl.link_name = %(supplier)s
            ORDER BY a.is_primary_address DESC, a.creation DESC
            LIMIT 1
        """, {"supplier": supplier.supplier_id}, as_dict=1)
        
        if address_data:
            supplier.address_line1 = address_data[0].address_line1
            supplier.address_line2 = address_data[0].address_line2
            supplier.city = address_data[0].city
            supplier.state = address_data[0].state
            supplier.pincode = address_data[0].pincode
        else:
            supplier.address_line1 = None
            supplier.address_line2 = None
            supplier.city = None
            supplier.state = None
            supplier.pincode = None
        
        # Get contact details from Dynamic Link
        contact_data = frappe.db.sql("""
            SELECT 
                c.name as contact_id
            FROM `tabDynamic Link` dl
            INNER JOIN `tabContact` c ON c.name = dl.parent
            WHERE dl.link_doctype = 'Supplier'
                AND dl.link_name = %(supplier)s
            ORDER BY c.is_primary_contact DESC, c.creation DESC
            LIMIT 1
        """, {"supplier": supplier.supplier_id}, as_dict=1)
        
        if contact_data:
            contact_id = contact_data[0].contact_id
            
            # Get phone from Contact Phone child table
            phone_data = frappe.db.sql("""
                SELECT phone
                FROM `tabContact Phone`
                WHERE parent = %(contact)s
                    AND is_primary_mobile_no = 1
                LIMIT 1
            """, {"contact": contact_id}, as_dict=1)
            
            if not phone_data:
                # If no primary, get first phone
                phone_data = frappe.db.sql("""
                    SELECT phone
                    FROM `tabContact Phone`
                    WHERE parent = %(contact)s
                    LIMIT 1
                """, {"contact": contact_id}, as_dict=1)
            
            supplier.mobile_no = phone_data[0].phone if phone_data else None
            
            # Get email from Contact Email child table
            email_data = frappe.db.sql("""
                SELECT email_id
                FROM `tabContact Email`
                WHERE parent = %(contact)s
                    AND is_primary = 1
                LIMIT 1
            """, {"contact": contact_id}, as_dict=1)
            
            if not email_data:
                # If no primary, get first email
                email_data = frappe.db.sql("""
                    SELECT email_id
                    FROM `tabContact Email`
                    WHERE parent = %(contact)s
                    LIMIT 1
                """, {"contact": contact_id}, as_dict=1)
            
            supplier.email_id = email_data[0].email_id if email_data else None
        else:
            supplier.mobile_no = None
            supplier.email_id = None
        
        # Get bank account details
        bank_accounts = frappe.get_all(
            "Bank Account",
            filters={
                "party_type": "Supplier",
                "party": supplier.supplier_id,
                "disabled": 0
            },
            fields=["bank", "bank_account_no", "branch_code", "account_name"],
            limit=1
        )
        
        if bank_accounts:
            supplier.bank = bank_accounts[0].bank
            supplier.bank_account_no = bank_accounts[0].bank_account_no
            supplier.branch_code = bank_accounts[0].branch_code
            supplier.account_holder_name = bank_accounts[0].account_name
        else:
            supplier.bank = None
            supplier.bank_account_no = None
            supplier.branch_code = None
            supplier.account_holder_name = None
    
    return suppliers


def create_supplier_verification_excel(concerned_person, suppliers):
    """Create Excel file with supplier data for verification"""
    
    # Create workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Supplier Verification"
    
    # Define styles
    header_fill = PatternFill(start_color="3498DB", end_color="3498DB", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Define headers
    headers = [
        "Sr. No.",
        "Belongs to You?\n(YES/NO)",
        "Supplier ID",
        "Supplier Name",
        "Mobile Number",
        "Email",
        "Address Line 1",
        "Address Line 2",
        "City",
        "State",
        "Pincode",
        "Bank",
        "Bank Account Number",
        "IFSC Code",
        "Account Holder Name",
        "GST Number",
        "PAN Number",
        "Aadhar Number"
    ]
    
    # Write headers
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = border
    
    # Set column widths
    column_widths = {
        1: 8,   # Sr. No.
        2: 15,  # Belongs to You?
        3: 20,  # Supplier ID
        4: 35,  # Supplier Name
        5: 15,  # Mobile Number
        6: 25,  # Email
        7: 30,  # Address Line 1
        8: 25,  # Address Line 2
        9: 15,  # City
        10: 15, # State
        11: 10, # Pincode
        12: 25, # Bank
        13: 20, # Bank Account Number
        14: 15, # IFSC Code
        15: 30, # Account Holder Name
        16: 18, # GST Number
        17: 12, # PAN Number
        18: 15  # Aadhar Number
    }
    
    for col_num, width in column_widths.items():
        ws.column_dimensions[get_column_letter(col_num)].width = width
    
    # Special fill for "Belongs to You?" column
    belongs_fill = PatternFill(start_color="FFF9C4", end_color="FFF9C4", fill_type="solid")
    belongs_font = Font(bold=True, size=11)
    
    # Write data rows
    for idx, supplier in enumerate(suppliers, 1):
        row_num = idx + 1
        
        # Format address
        address_line1 = supplier.address_line1 or ""
        address_line2 = supplier.address_line2 or ""
        
        row_data = [
            idx,                                    # Sr. No.
            "YES",                                  # Belongs to You? (default YES)
            supplier.supplier_id,                   # Supplier ID
            supplier.supplier_name,                 # Supplier Name
            supplier.mobile_no or "",              # Mobile Number
            supplier.email_id or "",               # Email
            address_line1,                         # Address Line 1
            address_line2,                         # Address Line 2
            supplier.city or "",                   # City
            supplier.state or "",                  # State
            supplier.pincode or "",                # Pincode
            supplier.bank or "",                   # Bank
            supplier.bank_account_no or "",        # Bank Account Number
            supplier.branch_code or "",            # IFSC Code
            supplier.account_holder_name or "",    # Account Holder Name
            supplier.gstin or "",                  # GST Number
            supplier.pan or "",                    # PAN Number
            supplier.custom_aadhar_no or ""        # Aadhar Number
        ]
        
        for col_num, value in enumerate(row_data, 1):
            cell = ws.cell(row=row_num, column=col_num)
            cell.value = value
            cell.border = border
            cell.alignment = Alignment(vertical='center', wrap_text=True)
            
            # Special formatting for "Belongs to You?" column
            if col_num == 2:
                cell.fill = belongs_fill
                cell.font = belongs_font
                cell.alignment = Alignment(horizontal='center', vertical='center')
    
    # Add instructions sheet
    ws_instructions = wb.create_sheet("Instructions", 0)
    ws_instructions.column_dimensions['A'].width = 100
    
    instructions = [
        ("SUPPLIER VERIFICATION - INSTRUCTIONS", True, "3498DB"),
        ("", False, None),
        ("Dear Concerned Person,", False, None),
        ("", False, None),
        ("Please review the 'Supplier Verification' sheet and complete the following:", False, None),
        ("", False, None),
        ("STEP 1: VERIFY SUPPLIER OWNERSHIP", True, "FFC107"),
        ("• Column B 'Belongs to You?' is pre-filled with 'YES' for all suppliers", False, None),
        ("• If a supplier DOES NOT belong to you, simply change 'YES' to 'NO'", False, None),
        ("• You can add a comment in that cell (right-click > Insert Comment) to explain why", False, None),
        ("", False, None),
        ("STEP 2: FILL MISSING INFORMATION", True, "27AE60"),
        ("• Fill in any blank cells with correct information", False, None),
        ("• Required fields: Mobile Number, Address, Bank Details, PAN or Aadhar", False, None),
        ("• Correct any incorrect information you notice", False, None),
        ("", False, None),
        ("STEP 3: SAVE & SUBMIT", True, "3498DB"),
        ("• Save the file after completing all changes", False, None),
        ("• Reply to the email with this completed Excel file attached", False, None),
        ("", False, None),
        ("IMPORTANT NOTES:", True, "E67E22"),
        ("• Do NOT delete or add rows", False, None),
        ("• Do NOT change Supplier ID or Supplier Name columns", False, None),
        ("• For suppliers that don't belong to you: Just change 'YES' to 'NO' in Column B", False, None),
        ("• You can add cell comments (right-click cell > Insert Comment) to provide additional context", False, None),
        ("• GST Number: If GST is provided, PAN will be auto-extracted (characters 3-12)", False, None),
        ("• Either PAN or Aadhar is mandatory", False, None),
        ("• Bank details are critical for payment processing", False, None),
        ("", False, None),
        ("RESPONSE DEADLINE: 7 days from email date", True, "C0392B"),
        ("", False, None),
        ("Contact for Support:", False, None),
        ("Vishnu Sharma - vishnu.sharma@hkmjaipur.org", False, None),
    ]
    
    for row_num, (text, is_bold, bg_color) in enumerate(instructions, 1):
        cell = ws_instructions.cell(row=row_num, column=1)
        cell.value = text
        if is_bold:
            cell.font = Font(bold=True, size=12, color="FFFFFF" if bg_color else "000000")
        if bg_color:
            cell.fill = PatternFill(start_color=bg_color, end_color=bg_color, fill_type="solid")
        cell.alignment = Alignment(wrap_text=True, vertical='center')
    
    # Save file
    file_name = f"Supplier_Verification_{concerned_person.split('@')[0]}_{frappe.utils.now_datetime().strftime('%Y%m%d_%H%M%S')}.xlsx"
    file_path = os.path.join(get_files_path(), file_name)
    wb.save(file_path)
    
    return file_path, file_name


def generate_email_html_with_summary(concerned_person, suppliers, recipient_email=None):
    """Generate HTML email with summary table (not full details)"""
    
    user = frappe.get_doc("User", concerned_person)
    user_name = user.full_name or concerned_person.split('@')[0]
    
    # Use recipient_email if provided, otherwise use concerned_person
    display_email = recipient_email if recipient_email else concerned_person
    
    # Count suppliers by source
    from_scr = sum(1 for s in suppliers if s.supplier_creation_request)
    from_direct = len(suppliers) - from_scr
    
    # Count data availability
    with_mobile = sum(1 for s in suppliers if s.mobile_no)
    with_address = sum(1 for s in suppliers if s.address_line1)
    with_bank = sum(1 for s in suppliers if s.bank)
    with_pan = sum(1 for s in suppliers if s.pan)
    
    # Pre-calculate all dynamic values to avoid Jinja interpretation
    total_suppliers = len(suppliers)
    mobile_percent = round(with_mobile/total_suppliers*100) if total_suppliers > 0 else 0
    address_percent = round(with_address/total_suppliers*100) if total_suppliers > 0 else 0
    bank_percent = round(with_bank/total_suppliers*100) if total_suppliers > 0 else 0
    pan_percent = round(with_pan/total_suppliers*100) if total_suppliers > 0 else 0
    current_date = frappe.utils.formatdate(nowdate(), 'dd-MMM-yyyy')
    deadline_date = frappe.utils.formatdate(frappe.utils.add_days(nowdate(), 7), 'dd-MMM-yyyy')
    
    # Build footer completely as Python string to avoid Jinja interpretation
    footer_html = f"""
        <div style="padding: 20px; background-color: white; border-left: 3px solid #3498db; border-right: 3px solid #3498db; border-bottom: 3px solid #3498db; border-radius: 0 0 5px 5px;">
            <p style="color: #7f8c8d; font-size: 13px; margin: 10px 0;">
                This is an automated verification email generated on <strong>{current_date}</strong>.
            </p>
            <p style="color: #7f8c8d; font-size: 13px; margin: 10px 0; line-height: 1.6;">
                <strong>Your Email:</strong> {display_email}<br>
                <strong>Total Suppliers:</strong> {total_suppliers}<br>
                <strong>Excel File:</strong> Attached to this email<br>
                <strong>Response Deadline:</strong> {deadline_date}<br>
                <strong>System:</strong> HKM Jaipur ERP
            </p>
            <div style="background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin: 15px 0;">
                <p style="color: #2c3e50; font-size: 13px; margin: 0 0 8px 0; font-weight: bold;">
                    📞 Contact Person for Support:
                </p>
                <p style="color: #34495e; font-size: 13px; margin: 0; line-height: 1.6;">
                    <strong>Vishnu Sharma</strong><br>
                    Email: <a href="mailto:vishnu.sharma@hkmjaipur.org" style="color: #3498db; text-decoration: none;">vishnu.sharma@hkmjaipur.org</a><br>
                    <strong>For any questions or to submit the completed Excel file, please reply to this email.</strong>
                </p>
            </div>
        </div>
    """
    
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 1400px; margin: 0 auto;">
        <div style="background-color: #3498db; color: white; padding: 20px; border-radius: 5px 5px 0 0;">
            <h2 style="margin: 0;">Supplier Verification & Information Update Request</h2>
        </div>
        
        <div style="padding: 20px; background-color: #f8f9fa; border-left: 3px solid #3498db; border-right: 3px solid #3498db;">
            <p style="font-size: 16px; color: #2c3e50;">Dear <strong>{user_name}</strong>,</p>
            
            <p style="font-size: 14px; color: #34495e; line-height: 1.6;">
                We are updating our supplier database and need your help to verify and complete the information 
                for <strong>{total_suppliers} suppliers</strong> under your responsibility.
            </p>
            
            <div style="background-color: #e8f4f8; padding: 15px; border-left: 4px solid #3498db; margin: 20px 0; border-radius: 3px;">
                <p style="margin: 0 0 10px 0; color: #2c3e50; font-weight: bold;">
                    📌 Why are you the Concerned Person?
                </p>
                <ul style="margin: 10px 0; color: #34495e; line-height: 1.6;">
                    <li><strong>{from_direct} suppliers</strong> - You created these suppliers directly in the ERP system</li>
                    <li><strong>{from_scr} suppliers</strong> - You raised the Supplier Creation Request for these suppliers</li>
                </ul>
            </div>
            
            <div style="background-color: #e8f5e9; padding: 15px; border-left: 4px solid #4caf50; margin: 20px 0; border-radius: 3px;">
                <p style="margin: 0 0 10px 0; color: #2c3e50; font-weight: bold;">
                    📧 Not the Right Person?
                </p>
                <p style="margin: 0; color: #34495e; line-height: 1.6;">
                    If you are <strong>not the appropriate person</strong> to handle these suppliers, please <strong>forward this email</strong> 
                    to the relevant person in your department who should verify and update this information. 
                    Please also inform Vishnu Sharma (CC'd in this email) about the correct person.
                </p>
            </div>
            
            <div style="background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0; border-radius: 3px;">
                <p style="margin: 0; color: #856404; font-weight: bold;">
                    ⚠️ Action Required: Review Excel File & Respond
                </p>
            </div>
        </div>
        
        <div style="padding: 20px; background-color: white; border-left: 3px solid #3498db; border-right: 3px solid #3498db;">
            <h3 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
                Supplier Summary ({total_suppliers} total)
            </h3>
            
            <div style="background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin: 15px 0;">
                <p style="margin: 0; color: #2c3e50; font-weight: bold;">Data Completeness Overview:</p>
                <table style="width: 100%; margin-top: 10px;">
                    <tr>
                        <td style="padding: 5px;">Mobile Numbers Available:</td>
                        <td style="padding: 5px;"><strong>{with_mobile} / {total_suppliers}</strong> ({mobile_percent}%)</td>
                        <td style="padding: 5px;">Addresses Available:</td>
                        <td style="padding: 5px;"><strong>{with_address} / {total_suppliers}</strong> ({address_percent}%)</td>
                    </tr>
                    <tr>
                        <td style="padding: 5px;">Bank Details Available:</td>
                        <td style="padding: 5px;"><strong>{with_bank} / {total_suppliers}</strong> ({bank_percent}%)</td>
                        <td style="padding: 5px;">PAN Numbers Available:</td>
                        <td style="padding: 5px;"><strong>{with_pan} / {total_suppliers}</strong> ({pan_percent}%)</td>
                    </tr>
                </table>
            </div>
            
            <p style="color: #34495e; font-size: 14px; margin: 15px 0;">
                Below is a quick summary of your suppliers. <strong>Complete details are in the attached Excel file.</strong>
            </p>
            
            <div style="overflow-x: auto;">
                <table style="width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 13px;">
                    <thead>
                        <tr style="background-color: #ecf0f1;">
                            <th style="padding: 12px 8px; text-align: left; border: 1px solid #bdc3c7; width: 50px;">Sr. No.</th>
                            <th style="padding: 12px 8px; text-align: left; border: 1px solid #bdc3c7; width: 30%;">Supplier Name</th>
                            <th style="padding: 12px 8px; text-align: left; border: 1px solid #bdc3c7; width: 12%;">Mobile No.</th>
                            <th style="padding: 12px 8px; text-align: left; border: 1px solid #bdc3c7; width: 25%;">Address</th>
                            <th style="padding: 12px 8px; text-align: center; border: 1px solid #bdc3c7; width: 10%;">Bank Info</th>
                            <th style="padding: 12px 8px; text-align: center; border: 1px solid #bdc3c7; width: 8%;">PAN</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    
    for idx, supplier in enumerate(suppliers, 1):
        bg_color = "#ffffff" if idx % 2 == 0 else "#f8f9fa"
        
        # Format address
        address_parts = []
        if supplier.address_line1:
            address_parts.append(supplier.address_line1)
        if supplier.city:
            address_parts.append(supplier.city)
        if supplier.state:
            address_parts.append(supplier.state)
        address = ", ".join(address_parts) if address_parts else "-"
        
        # Mobile
        mobile = supplier.mobile_no or "-"
        
        # Bank info status
        has_bank = bool(supplier.bank and supplier.bank_account_no)
        bank_status = "✓" if has_bank else "✗"
        bank_color = "#27ae60" if has_bank else "#e74c3c"
        
        # PAN status
        has_pan = bool(supplier.pan)
        pan_status = "✓" if has_pan else "✗"
        pan_color = "#27ae60" if has_pan else "#e74c3c"
        
        html += f"""
                    <tr style="background-color: {bg_color};">
                        <td style="padding: 10px 8px; border: 1px solid #dee2e6; text-align: center;">{idx}</td>
                        <td style="padding: 10px 8px; border: 1px solid #dee2e6;"><strong>{supplier.supplier_name}</strong></td>
                        <td style="padding: 10px 8px; border: 1px solid #dee2e6;">{mobile}</td>
                        <td style="padding: 10px 8px; border: 1px solid #dee2e6;">{address}</td>
                        <td style="padding: 10px 8px; border: 1px solid #dee2e6; text-align: center; color: {bank_color}; font-weight: bold;">{bank_status}</td>
                        <td style="padding: 10px 8px; border: 1px solid #dee2e6; text-align: center; color: {pan_color}; font-weight: bold;">{pan_status}</td>
                    </tr>
        """
    
    html += f"""
                    </tbody>
                </table>
            </div>
            
            <div style="background-color: #e8f5e9; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #27ae60;">
                <p style="margin: 0 0 5px 0; color: #2c3e50; font-weight: bold;">Legend:</p>
                <p style="margin: 5px 0; color: #34495e; font-size: 13px;">
                    <span style="color: #27ae60; font-weight: bold;">✓</span> = Information Available &nbsp;&nbsp;&nbsp;
                    <span style="color: #e74c3c; font-weight: bold;">✗</span> = Information Missing (Please Fill in Excel)
                </p>
            </div>
        </div>
        
        <div style="padding: 20px; background-color: #e8f5e9; border-left: 3px solid #3498db; border-right: 3px solid #3498db;">
            <h3 style="color: #2c3e50; margin-top: 0;">
                📎 Excel File Attached - Action Required
            </h3>
            
            <p style="color: #34495e; line-height: 1.6; font-size: 14px;">
                An Excel file is attached to this email with complete details of all your suppliers.
            </p>
            
            <div style="background-color: white; padding: 20px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #27ae60;">
                <p style="margin: 0 0 10px 0; color: #2c3e50; font-weight: bold; font-size: 15px;">
                    📝 What You Need to Do:
                </p>
                <ol style="color: #34495e; line-height: 1.8; margin: 10px 0;">
                    <li><strong>Open the attached Excel file</strong> (contains 2 sheets)
                        <ul style="margin: 5px 0; font-size: 13px;">
                            <li><strong>Instructions</strong> - Read this first</li>
                            <li><strong>Supplier Verification</strong> - Main data sheet</li>
                        </ul>
                    </li>
                    <li><strong>Verify Supplier Ownership</strong> (Column B: "Belongs to You?")
                        <ul style="margin: 5px 0; font-size: 13px;">
                            <li>All suppliers are pre-filled with <strong>"YES"</strong></li>
                            <li>If a supplier does <strong>NOT</strong> belong to you, simply change to <strong>"NO"</strong></li>
                            <li>You can add a comment to that cell (right-click > Insert Comment) to explain why</li>
                        </ul>
                    </li>
                    <li><strong>Fill in missing information</strong> (blank cells):
                        <ul style="margin: 5px 0;">
                            <li>Mobile Number</li>
                            <li>Email</li>
                            <li>Complete Address (Line 1, Line 2, City, State, Pincode)</li>
                            <li>Bank Details (Bank, Account Number, IFSC Code, Account Holder Name)</li>
                            <li>GST Number (if applicable)</li>
                            <li>PAN Number or Aadhar Number (at least one required)</li>
                        </ul>
                    </li>
                    <li><strong>Save the Excel file</strong></li>
                    <li><strong>Reply to this email</strong> with the completed Excel file attached</li>
                </ol>
            </div>
            
            <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 15px 0;">
                <p style="margin: 0; color: #856404; font-weight: bold;">
                    ⚠️ Important Guidelines:
                </p>
                <ul style="color: #856404; line-height: 1.6; margin: 10px 0;">
                    <li><strong>Supplier Ownership:</strong> Just change "YES" to "NO" in Column B if supplier doesn't belong to you</li>
                    <li><strong>Comments:</strong> You can add cell comments (right-click > Insert Comment) for additional context</li>
                    <li><strong>Do NOT</strong> delete or add rows</li>
                    <li><strong>Do NOT</strong> change Supplier ID or Supplier Name columns</li>
                    <li><strong>GST Number:</strong> If GST is provided, PAN will be automatically extracted (characters 3-12)</li>
                    <li><strong>Bank Details:</strong> Critical for payment processing - please prioritize these</li>
                </ul>
            </div>
        </div>
        
        <div style="padding: 20px; background-color: #d1ecf1; border-left: 3px solid #3498db; border-right: 3px solid #3498db;">
            <h3 style="color: #0c5460; margin-top: 0;">
                ℹ️ Why This Information is Important
            </h3>
            <p style="color: #0c5460; line-height: 1.6;">
                Complete supplier information ensures:
            </p>
            <ul style="color: #0c5460; line-height: 1.8;">
                <li><strong>Smooth payment processing</strong> - Bank details required for all payments</li>
                <li><strong>Tax compliance</strong> - GST/PAN needed for accurate tax reporting</li>
                <li><strong>Better communication</strong> - Mobile and email for quick coordination</li>
                <li><strong>Legal compliance</strong> - Complete records as per regulatory requirements</li>
            </ul>
        </div>
        
        <div style="padding: 20px; background-color: #ffe6e6; border-left: 3px solid #e74c3c; border-right: 3px solid #e74c3c; border: 2px solid #e74c3c; margin: 0;">
            <h3 style="color: #c0392b; margin-top: 0;">
                ⚠️ CRITICAL WARNING - Supplier Disabling Policy
            </h3>
            <p style="color: #c0392b; line-height: 1.6; font-weight: bold; margin: 10px 0;">
                If you do not update the supplier details and we do not have proper information, 
                we will <strong>DISABLE these suppliers</strong> in the ERP system.
            </p>
            <p style="color: #7f1d1d; line-height: 1.6; margin: 10px 0;">
                <strong>This means you will NOT be able to:</strong>
            </p>
            <ul style="color: #7f1d1d; line-height: 1.8; margin: 10px 0;">
                <li>Create purchase orders for these suppliers</li>
                <li>Make payments to these suppliers</li>
                <li>Interact with or deal with these suppliers in any capacity</li>
            </ul>
            
            <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #f39c12;">
                <p style="margin: 0 0 10px 0; color: #856404; font-weight: bold;">
                    📝 MANDATORY FIELDS FOR ALL SUPPLIERS:
                </p>
                <ul style="color: #856404; line-height: 1.6; margin: 5px 0;">
                    <li><strong>Mobile Number</strong> - MANDATORY for all suppliers</li>
                    <li><strong>Address</strong> - MANDATORY for all suppliers</li>
                    <li><strong>Bank Details</strong> - Required for payment processing</li>
                    <li><strong>PAN Number</strong> - Required for regular suppliers with established businesses</li>
                </ul>
            </div>
            
            <div style="background-color: #e8f4f8; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #3498db;">
                <p style="margin: 0 0 10px 0; color: #2c3e50; font-weight: bold;">
                    📌 SPECIAL EXCEPTION - Wage Workers & Small Vendors:
                </p>
                <p style="color: #34495e; line-height: 1.6; margin: 5px 0;">
                    For <strong>regular wage workers</strong> or suppliers <strong>without established shops</strong> 
                    (no proper business location), the following rules apply:
                </p>
                <ul style="color: #34495e; line-height: 1.6; margin: 10px 0;">
                    <li><strong>Mobile Number</strong> - MANDATORY (must be provided)</li>
                    <li><strong>Address</strong> - MANDATORY (must be provided)</li>
                    <li><strong>PAN Number</strong> - NOT mandatory for such suppliers</li>
                    <li><strong>Transaction Limit</strong> - Such suppliers (without PAN) will be restricted to transactions <strong>below ₹10,000</strong> only</li>
                </ul>
                <p style="color: #c0392b; line-height: 1.6; margin: 10px 0; font-weight: bold;">
                    ⚠️ If these suppliers do not have complete information, they will have <strong>REDUCED DEALINGS</strong> and limited transaction capabilities.
                </p>
            </div>
        </div>
        {footer_html}
    </div>
    """
    
    return html


def send_verification_email_with_excel(concerned_person, test_mode=True):
    """
    Send supplier verification email with Excel attachment
    
    Args:
        concerned_person: Email ID of the concerned person
        test_mode: If True, sends email to TEST_EMAIL instead
    """
    
    try:
        # Get complete supplier data
        suppliers = get_supplier_complete_data(concerned_person)
        
        if not suppliers:
            return {
                "success": False,
                "message": f"No suppliers found for {concerned_person}"
            }
        
        # Check if user is disabled
        user = frappe.get_doc("User", concerned_person)
        user_name = user.full_name or concerned_person.split('@')[0]
        is_disabled = user.enabled == 0
        
        # If user is disabled, send to Vishnu Sharma as SPOC
        if is_disabled and not test_mode:
            recipient = VISHNU_EMAIL
            user_status = " - User Disabled, SPOC Required"
        else:
            recipient = TEST_EMAIL if test_mode else concerned_person
            user_status = ""
        
        # Create Excel file
        file_path, file_name = create_supplier_verification_excel(concerned_person, suppliers)
        
        # Generate email HTML with summary (pass recipient for correct footer display)
        email_html = generate_email_html_with_summary(concerned_person, suppliers, recipient_email=recipient)
        
        # Prepare CC list
        if is_disabled and not test_mode:
            cc_list = []
        else:
            cc_list = [VISHNU_EMAIL]
        
        # Send email with attachment
        frappe.sendmail(
            recipients=[recipient],
            cc=cc_list,
            subject=f"Supplier Verification - {user_name} ({len(suppliers)} suppliers){user_status}",
            message=email_html,
            header=["Supplier Verification", "orange"],
            reply_to=VISHNU_EMAIL,
            attachments=[{
                "fname": file_name,
                "fcontent": open(file_path, "rb").read()
            }]
        )
        
        # Delete temporary file
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return {
            "success": True,
            "message": f"Email sent to {recipient}{' (user disabled - sent to Vishnu)' if is_disabled else ''}",
            "supplier_count": len(suppliers),
            "concerned_person": concerned_person,
            "user_disabled": is_disabled,
            "excel_file": file_name
        }
        
    except Exception as e:
        frappe.log_error(
            message=f"Error sending verification email to {concerned_person}: {str(e)}",
            title="Supplier Verification Email Error"
        )
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }


def send_verification_to_all_concerned_persons(test_mode=True, site='hkmjerp.in'):
    """Send verification emails with Excel to all concerned persons"""
    
    frappe.init(site=site)
    frappe.connect()
    
    try:
        # Get all concerned persons
        concerned_persons = frappe.db.sql("""
            SELECT 
                custom_concerned_person,
                COUNT(*) as supplier_count
            FROM tabSupplier
            WHERE custom_concerned_person IS NOT NULL
                AND disabled = 0
            GROUP BY custom_concerned_person
            ORDER BY custom_concerned_person
        """, as_dict=1)
        
        print(f"\n{'='*100}")
        print(f"Sending Supplier Verification Emails with Excel Attachments")
        print(f"Site: {site}")
        print(f"Mode: {'TEST (all emails to ' + TEST_EMAIL + ')' if test_mode else 'PRODUCTION'}")
        print(f"Total Concerned Persons: {len(concerned_persons)}")
        print(f"{'='*100}\n")
        
        results = {
            "total": len(concerned_persons),
            "success": 0,
            "failed": 0,
            "disabled_users": 0,
            "details": []
        }
        
        for idx, cp in enumerate(concerned_persons, 1):
            print(f"[{idx}/{len(concerned_persons)}] {cp.custom_concerned_person} ({cp.supplier_count} suppliers)...")
            
            result = send_verification_email_with_excel(
                concerned_person=cp.custom_concerned_person,
                test_mode=test_mode
            )
            
            if result["success"]:
                if result.get("user_disabled"):
                    print(f"  ✓ Sent (User Disabled → Vishnu Sharma)")
                    results["disabled_users"] += 1
                else:
                    print(f"  ✓ Sent successfully")
                results["success"] += 1
            else:
                print(f"  ✗ Failed: {result['message']}")
                results["failed"] += 1
            
            results["details"].append({
                "concerned_person": cp.custom_concerned_person,
                "supplier_count": cp.supplier_count,
                "status": result["success"],
                "message": result["message"]
            })
        
        frappe.db.commit()  # v16: REVIEW - check if needed
        
        print(f"\n{'='*100}")
        print(f"Summary:")
        print(f"  Total Concerned Persons: {results['total']}")
        print(f"  Emails Sent: {results['success']}")
        print(f"  Disabled Users (sent to Vishnu): {results['disabled_users']}")
        print(f"  Failed: {results['failed']}")
        print(f"{'='*100}\n")
        
        return results
        
    except Exception as e:
        frappe.db.rollback()
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        frappe.destroy()


def send_verification_to_all_sites(test_mode=True):
    """Send verification emails to all HKM sites"""
    
    sites = [
        'hkmjerp.in',         # Jaipur
        'erp.hkmkota.org',    # Kota
        'erp.hkmudaipur.org', # Udaipur
        'erp.hkmjodhpur.org'  # Jodhpur
    ]
    
    all_results = {}
    
    print(f"\n{'='*100}")
    print(f"SENDING SUPPLIER VERIFICATION EMAILS TO ALL HKM SITES")
    print(f"{'='*100}")
    print(f"Sites: {', '.join(sites)}")
    print(f"Mode: {'TEST' if test_mode else 'PRODUCTION'}")
    print(f"{'='*100}\n")
    
    for site in sites:
        print(f"\n{'*'*100}")
        print(f"PROCESSING SITE: {site.upper()}")
        print(f"{'*'*100}")
        
        try:
            result = send_verification_to_all_concerned_persons(
                test_mode=test_mode,
                site=site
            )
            all_results[site] = result
        except Exception as e:
            print(f"ERROR processing {site}: {str(e)}")
            import traceback
            traceback.print_exc()
            all_results[site] = {
                "error": str(e),
                "total": 0,
                "success": 0,
                "failed": 0
            }
    
    # Print overall summary
    print(f"\n{'='*100}")
    print(f"OVERALL SUMMARY - ALL SITES")
    print(f"{'='*100}")
    
    total_all = 0
    success_all = 0
    failed_all = 0
    disabled_all = 0
    
    for site, result in all_results.items():
        print(f"\n{site}:")
        if "error" in result:
            print(f"  ✗ ERROR: {result['error']}")
        else:
            print(f"  Total Concerned Persons: {result['total']}")
            print(f"  Emails Sent: {result['success']}")
            print(f"  Disabled Users: {result.get('disabled_users', 0)}")
            print(f"  Failed: {result['failed']}")
            total_all += result['total']
            success_all += result['success']
            failed_all += result['failed']
            disabled_all += result.get('disabled_users', 0)
    
    print(f"\n{'='*100}")
    print(f"GRAND TOTAL:")
    print(f"  Total Concerned Persons Across All Sites: {total_all}")
    print(f"  Total Emails Sent: {success_all}")
    print(f"  Total Disabled Users: {disabled_all}")
    print(f"  Total Failed: {failed_all}")
    print(f"{'='*100}\n")
    
    return all_results


def test_verification_email_with_excel():
    """Send a test verification email with Excel attachment"""
    
    frappe.init(site='hkmjerp.in')
    frappe.connect()
    
    try:
        # Find a concerned person with moderate number of suppliers
        result = frappe.db.sql("""
            SELECT 
                custom_concerned_person,
                COUNT(*) as supplier_count
            FROM tabSupplier
            WHERE custom_concerned_person IS NOT NULL
                AND disabled = 0
            GROUP BY custom_concerned_person
            HAVING COUNT(*) BETWEEN 5 AND 20
            ORDER BY supplier_count DESC
            LIMIT 1
        """, as_dict=1)
        
        if not result:
            print("No suitable concerned person found for testing")
            return
        
        concerned_person = result[0].custom_concerned_person
        supplier_count = result[0].supplier_count
        
        print(f"\n{'='*100}")
        print(f"TEST - Supplier Verification Email with Excel Attachment")
        print(f"{'='*100}")
        print(f"Concerned Person: {concerned_person}")
        print(f"Supplier Count: {supplier_count}")
        print(f"Test Email: {TEST_EMAIL}")
        print(f"CC: {VISHNU_EMAIL}")
        print(f"Reply-To: {VISHNU_EMAIL}")
        print(f"{'='*100}\n")
        
        # Send verification email
        result = send_verification_email_with_excel(
            concerned_person=concerned_person,
            test_mode=True
        )
        
        if result["success"]:
            print("✓ SUCCESS!")
            print(f"  Email sent to: {TEST_EMAIL}")
            print(f"  Excel file: {result['excel_file']}")
            print(f"  Suppliers: {result['supplier_count']}")
        else:
            print(f"✗ FAILED: {result['message']}")
        
        frappe.db.commit()  # v16: REVIEW - check if needed
        print(f"\n{'='*100}\n")
        
    except Exception as e:
        frappe.db.rollback()
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        frappe.destroy()


if __name__ == "__main__":
    test_verification_email_with_excel()

