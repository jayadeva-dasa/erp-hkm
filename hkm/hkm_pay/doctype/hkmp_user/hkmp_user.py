# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

import string
from hkm.hkm_pay.doctype.hkmp_entry.payment import update_user_balance
import frappe
from frappe.model.document import Document
from hkm.mobile_app.auth import random_string_generator

HKMP_USER_MANAGEMENT_ALLOWED_ROLES = [
    "System Manager",
    "Accounts User",
    "Accounts Admin",
    "Accounts Manager",
]


class HKMPUser(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF
        from hkm.erpnext___custom.doctype.hkm_active_company.hkm_active_company import HKMActiveCompany

        active_company: DF.Table[HKMActiveCompany]
        advance_limit: DF.Currency
        available_amt: DF.Currency
        available_daily_limit: DF.Currency
        bill_submission_restriction_enabled: DF.Check
        bill_submission_upto_date: DF.Date | None
        daily_limit: DF.Currency
        department: DF.Link | None
        enabled: DF.Check
        full_name: DF.Data | None
        per_transaction_limit: DF.Currency
        secret_pin: DF.Password | None
        user: DF.Link | None
    # end: auto-generated types

    def after_insert(self):
        """Send email to the user with the secret PIN"""
        self.send_email_to_user(show_secret_pin(self.name))

    def before_save(self):

        if not self.secret_pin:
            self.secret_pin = random_string_generator(4, string.digits)

    def before_insert(self):
        """Initialize available amounts on first insert"""
        if not self.available_amt:
            self.available_amt = self.advance_limit or 0

        if not self.available_daily_limit:
            self.available_daily_limit = self.daily_limit or 0

        pin = random_string_generator(4, string.digits)
        self.secret_pin = pin

    def send_email_to_user(self, pin):
        """Send professional email to the user with the secret PIN"""
        user = frappe.get_doc("User", self.user)

        # Create professional HTML email template
        email_message = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
            <div style="background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <!-- Header -->
                <div style="text-align: center; margin-bottom: 30px;">
                    <h2 style="color: #2c3e50; margin: 0;">HKMP User Account Created</h2>
                    <p style="color: #7f8c8d; margin-top: 10px;">Welcome to HKM Pay System</p>
                </div>
                
                <!-- Greeting -->
                <p style="color: #34495e; font-size: 16px; margin-bottom: 20px;">
                    Dear {self.full_name or user.full_name},
                </p>
                
                <p style="color: #34495e; font-size: 14px; line-height: 1.6; margin-bottom: 20px;">
                    Your HKMP User account has been successfully created. Below are your account details and security PIN for accessing the system.
                </p>
                
                <!-- PIN Display -->
                <div style="background-color: #ecf0f1; padding: 25px; border-radius: 8px; text-align: center; margin: 30px 0;">
                    <p style="color: #7f8c8d; font-size: 14px; margin: 0 0 10px 0;">Your Secret PIN</p>
                    <h1 style="color: #e74c3c; font-size: 48px; letter-spacing: 8px; margin: 10px 0; font-family: 'Courier New', monospace;">
                        {pin}
                    </h1>
                </div>
                
                <!-- Account Details -->
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #2c3e50; margin-top: 0;">Account Details:</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; color: #7f8c8d; font-size: 14px;">Advance Limit:</td>
                            <td style="padding: 8px 0; color: #34495e; font-size: 14px; text-align: right; font-weight: bold;">
                                {frappe.utils.fmt_money(self.advance_limit, currency="INR")}
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #7f8c8d; font-size: 14px;">Daily Limit:</td>
                            <td style="padding: 8px 0; color: #34495e; font-size: 14px; text-align: right; font-weight: bold;">
                                {frappe.utils.fmt_money(self.daily_limit, currency="INR")}
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #7f8c8d; font-size: 14px;">Per Transaction Limit:</td>
                            <td style="padding: 8px 0; color: #34495e; font-size: 14px; text-align: right; font-weight: bold;">
                                {frappe.utils.fmt_money(self.per_transaction_limit, currency="INR")}
                            </td>
                        </tr>
                        {f'''<tr>
                            <td style="padding: 8px 0; color: #7f8c8d; font-size: 14px;">Department:</td>
                            <td style="padding: 8px 0; color: #34495e; font-size: 14px; text-align: right; font-weight: bold;">
                                {self.department}
                            </td>
                        </tr>''' if self.department else ''}
                    </table>
                </div>
                
                <!-- Security Instructions -->
                <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 4px;">
                    <h4 style="color: #856404; margin: 0 0 10px 0; font-size: 16px;">
                        🔒 Security Instructions
                    </h4>
                    <ul style="color: #856404; font-size: 13px; margin: 0; padding-left: 20px; line-height: 1.8;">
                        <li>Keep your PIN confidential and do not share it with anyone</li>
                        <li>Do not write down your PIN or save it in an unsecured location</li>
                        <li>If you suspect your PIN has been compromised, contact the administrator immediately</li>
                        <li>You can regenerate a new PIN anytime from the system</li>
                    </ul>
                </div>
                
                <!-- Footer -->
                <div style="margin-top: 30px; padding-top: 20px; border-top: 2px solid #ecf0f1;">
                    <p style="color: #7f8c8d; font-size: 13px; line-height: 1.6; margin: 0;">
                        If you have any questions or need assistance, please contact your system administrator.
                    </p>
                    <p style="color: #95a5a6; font-size: 12px; margin-top: 15px; font-style: italic;">
                        This is an automated message. Please do not reply to this email.
                    </p>
                </div>
            </div>
            
            <!-- Footer Note -->
            <div style="text-align: center; margin-top: 20px;">
                <p style="color: #95a5a6; font-size: 12px;">
                    © {frappe.utils.nowdate()[:4]} HKM Jaipur. All rights reserved.
                </p>
            </div>
        </div>
        """

        try:
            # frappe.sendmail(
            #     recipients=[user.email],
            #     subject="Welcome to HKMP - Your Secret PIN and Account Details",
            #     message=email_message,
            #     delayed=False,
            #     retry=3,
            # )
            frappe.enqueue(
                frappe.sendmail,
                queue="default",
                recipients=[user.email],
                subject="Welcome to HKMP - Your Secret PIN and Account Details",
                message=email_message,
                delayed=False,
                retry=3,
            )
            frappe.logger().info(
                f"PIN email sent successfully to {user.email} for HKMP User {self.name}"
            )
        except Exception as e:
            frappe.log_error(
                message=f"Failed to send PIN email to {user.email} for HKMP User {self.name}: {str(e)}",
                title="HKMP User PIN Email Failed",
            )
            frappe.throw(
                f"Failed to send email to {user.email}. Please contact the administrator."
            )

    def on_update(self):
        update_user_balance(self.user)

    def validate(self):
        """Validate limit hierarchy and constraints"""
        self.validate_limits()
        self.validate_available_amounts()

    def validate_limits(self):
        """Ensure limit hierarchy: per_transaction_limit <= daily_limit <= advance_limit"""
        # Ensure daily_limit doesn't exceed advance_limit
        if (
            self.daily_limit
            and self.advance_limit
            and self.daily_limit > self.advance_limit
        ):
            frappe.throw(
                f"Daily Limit ({frappe.utils.fmt_money(self.daily_limit)}) cannot exceed "
                f"Advance Limit ({frappe.utils.fmt_money(self.advance_limit)})"
            )

        # Ensure per_transaction_limit doesn't exceed daily_limit
        if (
            self.per_transaction_limit
            and self.daily_limit
            and self.per_transaction_limit > self.daily_limit
        ):
            frappe.throw(
                f"Per Transaction Limit ({frappe.utils.fmt_money(self.per_transaction_limit)}) "
                f"cannot exceed Daily Limit ({frappe.utils.fmt_money(self.daily_limit)})"
            )

        # Ensure per_transaction_limit doesn't exceed advance_limit
        if (
            self.per_transaction_limit
            and self.advance_limit
            and self.per_transaction_limit > self.advance_limit
        ):
            frappe.throw(
                f"Per Transaction Limit ({frappe.utils.fmt_money(self.per_transaction_limit)}) "
                f"cannot exceed Advance Limit ({frappe.utils.fmt_money(self.advance_limit)})"
            )

    def validate_available_amounts(self):
        """Ensure available amounts don't exceed their respective limits"""
        # Ensure available_amt doesn't exceed advance_limit
        if (
            self.available_amt
            and self.advance_limit
            and self.available_amt > self.advance_limit
        ):
            self.available_amt = self.advance_limit

        # Ensure available_daily_limit doesn't exceed daily_limit
        if (
            self.available_daily_limit
            and self.daily_limit
            and self.available_daily_limit > self.daily_limit
        ):
            self.available_daily_limit = self.daily_limit

        # Ensure available_daily_limit doesn't exceed available_amt
        if (
            self.available_daily_limit
            and self.available_amt
            and self.available_daily_limit > self.available_amt
        ):
            self.available_daily_limit = self.available_amt

        if not self.available_daily_limit:
            self.available_daily_limit = self.daily_limit or 0


def check_hkmp_user_management_permission():
    """Check if user has permission to access HKM Pay User Management"""
    user_roles = frappe.get_roles(frappe.session.user)
    has_access = any(role in HKMP_USER_MANAGEMENT_ALLOWED_ROLES for role in user_roles)

    if not has_access:
        frappe.throw(
            frappe._(
                "You don't have permission to access HKM Pay User Management. Required roles: {0}"
            ).format(", ".join(HKMP_USER_MANAGEMENT_ALLOWED_ROLES)),
            frappe.PermissionError,
        )


@frappe.whitelist()
def generate_secret_pin(docname, desired_pin=None):
    check_hkmp_user_management_permission()
    """Generate a random 4 digit PIN for the user or use desired PIN if provided"""
    doc = frappe.get_doc("HKMP User", docname)
    
    if desired_pin:
        # Validate desired PIN
        desired_pin = str(desired_pin).strip()
        if not desired_pin.isdigit():
            frappe.throw("PIN must contain only digits (0-9)")
        if len(desired_pin) != 4:
            frappe.throw("PIN must be exactly 4 digits")
        doc.secret_pin = desired_pin
    else:
        # Generate random PIN if not provided
        doc.secret_pin = random_string_generator(4, string.digits)
    
    doc.save()
    return doc.secret_pin


@frappe.whitelist()
def show_secret_pin(docname):
    check_hkmp_user_management_permission()
    """Show the secret PIN for the user"""
    doc = frappe.get_doc("HKMP User", docname)
    return doc.get_password("secret_pin")


def add_hkmp_company():
    for i in frappe.get_all("HKMP User"):
        doc = frappe.get_doc("HKMP User", i.name)
        doc.append(
            "active_company",
            {
                "company": "Hare Krishna Movement Jaipur",
            },
        )
        doc.save()
