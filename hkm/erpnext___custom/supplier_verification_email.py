#!/usr/bin/env python3
"""
Supplier Verification Email System

Sends emails to all concerned persons asking them to verify 
which suppliers actually belong to them.
"""

import frappe
from frappe import _
from frappe.utils import nowdate
import frappe.utils


TEST_EMAIL = "nrhd@hkmjaipur.org"


def get_concerned_person_suppliers(concerned_person):
    """Get all suppliers for a concerned person with additional details"""
    
    suppliers = frappe.db.sql("""
        SELECT 
            s.name,
            s.supplier_name,
            s.mobile_no,
            s.supplier_primary_address,
            a.address_line1,
            a.city,
            a.state,
            s.supplier_creation_request,
            s.owner
        FROM `tabSupplier` s
        LEFT JOIN `tabAddress` a ON a.name = s.supplier_primary_address
        WHERE s.custom_concerned_person = %(concerned_person)s
            AND s.disabled = 0
        ORDER BY s.supplier_name
    """, {"concerned_person": concerned_person}, as_dict=1)
    
    return suppliers


def generate_verification_email_html(concerned_person, suppliers):
    """Generate HTML email for supplier verification"""
    
    user = frappe.get_doc("User", concerned_person)
    user_name = user.full_name or concerned_person.split('@')[0]
    
    # Count suppliers by source
    from_scr = sum(1 for s in suppliers if s.supplier_creation_request)
    from_direct = len(suppliers) - from_scr
    
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 1400px; margin: 0 auto;">
        <div style="background-color: #3498db; color: white; padding: 20px; border-radius: 5px 5px 0 0;">
            <h2 style="margin: 0;">Supplier Verification Request</h2>
        </div>
        
        <div style="padding: 20px; background-color: #f8f9fa; border-left: 3px solid #3498db; border-right: 3px solid #3498db;">
            <p style="font-size: 16px; color: #2c3e50;">Dear <strong>{user_name}</strong>,</p>
            
            <p style="font-size: 14px; color: #34495e; line-height: 1.6;">
                We are updating our supplier management system and need your help to verify which suppliers 
                are under your responsibility. According to our records, you are listed as the 
                <strong>Concerned Person</strong> for the following <strong>{len(suppliers)} suppliers</strong>.
            </p>
            
            <div style="background-color: #e8f4f8; padding: 15px; border-left: 4px solid #3498db; margin: 20px 0; border-radius: 3px;">
                <p style="margin: 0 0 10px 0; color: #2c3e50; font-weight: bold;">
                    📌 Why are you listed as the Concerned Person?
                </p>
                <p style="margin: 0; color: #34495e; line-height: 1.6;">
                    You have been assigned as the concerned person for these suppliers because:
                </p>
                <ul style="margin: 10px 0; color: #34495e; line-height: 1.6;">
                    <li><strong>{from_direct} suppliers</strong> - You created these suppliers directly in the ERP system</li>
                    <li><strong>{from_scr} suppliers</strong> - You raised the Supplier Creation Request for these suppliers</li>
                </ul>
            </div>
            
            <div style="background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0; border-radius: 3px;">
                <p style="margin: 0; color: #856404; font-weight: bold;">
                    ⚠️ Action Required: Please Review and Respond
                </p>
            </div>
        </div>
        
        <div style="padding: 20px; background-color: white; border-left: 3px solid #3498db; border-right: 3px solid #3498db;">
            <h3 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
                Your Assigned Suppliers ({len(suppliers)} total)
            </h3>
            
            <table style="width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 13px;">
                <thead>
                    <tr style="background-color: #ecf0f1;">
                        <th style="padding: 12px 8px; text-align: left; border: 1px solid #bdc3c7; width: 50px;">Sr. No.</th>
                        <th style="padding: 12px 8px; text-align: left; border: 1px solid #bdc3c7; width: 30%;">Supplier Name</th>
                        <th style="padding: 12px 8px; text-align: left; border: 1px solid #bdc3c7; width: 12%;">Mobile No.</th>
                        <th style="padding: 12px 8px; text-align: left; border: 1px solid #bdc3c7;">Address</th>
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
        
        # Mobile number
        mobile = supplier.mobile_no or "-"
        
        html += f"""
                <tr style="background-color: {bg_color};">
                    <td style="padding: 10px 8px; border: 1px solid #dee2e6; text-align: center;">{idx}</td>
                    <td style="padding: 10px 8px; border: 1px solid #dee2e6;"><strong>{supplier.supplier_name}</strong></td>
                    <td style="padding: 10px 8px; border: 1px solid #dee2e6;">{mobile}</td>
                    <td style="padding: 10px 8px; border: 1px solid #dee2e6;">{address}</td>
                </tr>
        """
    
    html += """
                </tbody>
            </table>
        </div>
        
        <div style="padding: 20px; background-color: #e8f5e9; border-left: 3px solid #3498db; border-right: 3px solid #3498db;">
            <h3 style="color: #2c3e50; margin-top: 0;">
                📝 How to Respond
            </h3>
            
            <p style="color: #34495e; line-height: 1.6;">
                Please review the list above and respond to this email using <strong>one of the following formats</strong>:
            </p>
            
            <div style="background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0;">
                <p style="margin: 0 0 10px 0; color: #27ae60; font-weight: bold;">
                    ✅ Option 1: If ALL suppliers belong to you
                </p>
                <pre style="background-color: #f8f9fa; padding: 10px; border-left: 3px solid #27ae60; margin: 5px 0; overflow-x: auto;">CONFIRMED: All suppliers are correct</pre>
            </div>
            
            <div style="background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0;">
                <p style="margin: 0 0 10px 0; color: #e67e22; font-weight: bold;">
                    ⚠️ Option 2: If SOME suppliers do NOT belong to you
                </p>
                <p style="margin: 5px 0; font-size: 13px; color: #7f8c8d;">
                    List only the suppliers that should be REMOVED from your list:
                </p>
                <pre style="background-color: #f8f9fa; padding: 10px; border-left: 3px solid #e67e22; margin: 5px 0; overflow-x: auto;">REMOVE:
SUP-2023-00123
SUP-2024-00456
ABC Enterprises</pre>
                <p style="margin: 5px 0; font-size: 12px; color: #95a5a6; font-style: italic;">
                    (You can use either Supplier ID or Supplier Name)
                </p>
            </div>
            
            <div style="background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0;">
                <p style="margin: 0 0 10px 0; color: #c0392b; font-weight: bold;">
                    ❌ Option 3: If NO suppliers belong to you
                </p>
                <pre style="background-color: #f8f9fa; padding: 10px; border-left: 3px solid #c0392b; margin: 5px 0; overflow-x: auto;">REMOVE ALL: None of these suppliers belong to me</pre>
            </div>
            
            <div style="background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0;">
                <p style="margin: 0 0 10px 0; color: #3498db; font-weight: bold;">
                    ➕ Option 4: If you want to ADD suppliers not in your list
                </p>
                <p style="margin: 5px 0; font-size: 13px; color: #7f8c8d;">
                    List suppliers that should be added to your responsibility:
                </p>
                <pre style="background-color: #f8f9fa; padding: 10px; border-left: 3px solid #3498db; margin: 5px 0; overflow-x: auto;">ADD:
XYZ Suppliers
PQR Enterprises
SUP-2024-00789</pre>
            </div>
        </div>
        
        <div style="padding: 20px; background-color: #fff3cd; border-left: 3px solid #3498db; border-right: 3px solid #3498db;">
            <h3 style="color: #856404; margin-top: 0;">
                ⏰ Important Notes
            </h3>
            <ul style="color: #856404; line-height: 1.8;">
                <li><strong>Response Deadline:</strong> Please respond within <strong>7 days</strong> from receiving this email</li>
                <li><strong>Reply Method:</strong> Simply reply to this email with your response in the format shown above</li>
                <li><strong>No Response = Confirmation:</strong> If we don't hear from you, we'll assume all suppliers listed are correct</li>
                <li><strong>Questions?</strong> Contact the Accounts team if you need clarification about any supplier</li>
            </ul>
        </div>
        
        <div style="padding: 20px; background-color: #d1ecf1; border-left: 3px solid #3498db; border-right: 3px solid #3498db;">
            <h3 style="color: #0c5460; margin-top: 0;">
                ℹ️ Why This Matters
            </h3>
            <p style="color: #0c5460; line-height: 1.6;">
                As the <strong>Concerned Person</strong> for these suppliers, you will:
            </p>
            <ul style="color: #0c5460; line-height: 1.8;">
                <li>Receive monthly reports on outstanding balances and payments</li>
                <li>Be responsible for following up on pending invoices</li>
                <li>Get notified about advance payments awaiting invoice submission</li>
                <li>Be the primary contact for supplier-related queries</li>
            </ul>
            <p style="color: #0c5460; line-height: 1.6;">
                Therefore, it's important that the supplier assignments are accurate.
            </p>
        </div>
        
        <div style="padding: 20px; background-color: white; border-left: 3px solid #3498db; border-right: 3px solid #3498db; border-bottom: 3px solid #3498db; border-radius: 0 0 5px 5px;">
            <p style="color: #7f8c8d; font-size: 13px; margin: 10px 0;">
                This is an automated verification email generated on <strong>{frappe.utils.formatdate(nowdate(), "dd-MMM-yyyy")}</strong>.
            </p>
            <p style="color: #7f8c8d; font-size: 13px; margin: 10px 0; line-height: 1.6;">
                <strong>Your Email:</strong> {concerned_person}<br>
                <strong>Total Suppliers:</strong> {len(suppliers)}<br>
                <strong>System:</strong> HKM Jaipur ERP
            </p>
            <div style="background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin: 15px 0;">
                <p style="color: #2c3e50; font-size: 13px; margin: 0 0 8px 0; font-weight: bold;">
                    📞 Contact Person for Support:
                </p>
                <p style="color: #34495e; font-size: 13px; margin: 0; line-height: 1.6;">
                    <strong>Vishnu Sharma</strong><br>
                    Email: <a href="mailto:vishnu.sharma@hkmjaipur.org" style="color: #3498db; text-decoration: none;">vishnu.sharma@hkmjaipur.org</a><br>
                    For any questions or clarifications about this verification, please contact Vishnu Sharma.
                </p>
            </div>
        </div>
    </div>
    """
    
    return html


def send_verification_email(concerned_person, test_mode=True):
    """
    Send supplier verification email to concerned person
    
    Args:
        concerned_person: Email ID of the concerned person
        test_mode: If True, sends email to TEST_EMAIL instead
    """
    
    try:
        # Get suppliers for this concerned person
        suppliers = get_concerned_person_suppliers(concerned_person)
        
        if not suppliers:
            return {
                "success": False,
                "message": f"No suppliers found for {concerned_person}"
            }
        
        # Check if user is disabled
        user = frappe.get_doc("User", concerned_person)
        user_name = user.full_name or concerned_person.split('@')[0]
        is_disabled = user.enabled == 0
        
        vishnu_email = "vishnu.sharma@hkmjaipur.org"
        
        # If user is disabled, send to Vishnu Sharma as SPOC
        if is_disabled and not test_mode:
            recipient = vishnu_email
            user_status = " - User Disabled, SPOC Required"
        else:
            recipient = TEST_EMAIL if test_mode else concerned_person
            user_status = ""
        
        # Generate email HTML
        email_html = generate_verification_email_html(concerned_person, suppliers)
        
        # Prepare CC list
        # Always CC Vishnu Sharma (except when he's the main recipient)
        if is_disabled and not test_mode:
            # If disabled, Vishnu is main recipient, no need for CC
            cc_list = []
        else:
            # Always CC Vishnu (in both test and production mode)
            cc_list = [vishnu_email]
        
        # Send email with CC to Vishnu Sharma and reply-to
        frappe.sendmail(
            recipients=[recipient],
            cc=cc_list,
            subject=f"Supplier Verification - {user_name} ({len(suppliers)} suppliers){user_status}",
            message=email_html,
            header=["Supplier Verification", "orange"],
            reply_to=vishnu_email,  # Replies go to Vishnu Sharma
        )
        
        return {
            "success": True,
            "message": f"Email sent to {recipient}{' (user disabled - sent to Vishnu)' if is_disabled else ''}",
            "supplier_count": len(suppliers),
            "concerned_person": concerned_person,
            "user_disabled": is_disabled
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


def send_verification_to_all_concerned_persons(test_mode=True):
    """
    Send verification emails to all concerned persons
    
    Args:
        test_mode: If True, sends all emails to TEST_EMAIL instead
    """
    
    frappe.init(site='hkmjerp.in')
    frappe.connect()
    
    try:
        # Get all concerned persons with suppliers
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
        print(f"Sending Supplier Verification Emails to All Concerned Persons")
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
            print(f"[{idx}/{len(concerned_persons)}] Sending to {cp.custom_concerned_person} ({cp.supplier_count} suppliers)...")
            
            result = send_verification_email(
                concerned_person=cp.custom_concerned_person,
                test_mode=test_mode
            )
            
            if result["success"]:
                if result.get("user_disabled"):
                    print(f"  ✓ Sent successfully (User Disabled - Sent to Vishnu Sharma)")
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


def test_verification_email():
    """Send a test verification email to TEST_EMAIL"""
    
    frappe.init(site='hkmjerp.in')
    frappe.connect()
    
    try:
        # Find a concerned person with decent number of suppliers
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
        print(f"TEST - Supplier Verification Email")
        print(f"{'='*100}")
        print(f"Concerned Person: {concerned_person}")
        print(f"Supplier Count: {supplier_count}")
        print(f"Test Email: {TEST_EMAIL}")
        print(f"{'='*100}\n")
        
        # Send verification email
        result = send_verification_email(
            concerned_person=concerned_person,
            test_mode=True
        )
        
        if result["success"]:
            print("✓ SUCCESS!")
            print(f"  Email sent to: {TEST_EMAIL}")
            print(f"  Suppliers listed: {result['supplier_count']}")
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


def test_disabled_user_email():
    """Test email routing for disabled user - should go to Vishnu Sharma"""
    
    frappe.init(site='hkmjerp.in')
    frappe.connect()
    
    try:
        # Find a disabled user with suppliers
        disabled_user = frappe.db.sql("""
            SELECT 
                u.name,
                u.full_name,
                COUNT(s.name) as supplier_count
            FROM tabUser u
            INNER JOIN tabSupplier s ON s.custom_concerned_person = u.name
            WHERE u.enabled = 0
                AND s.disabled = 0
            GROUP BY u.name
            ORDER BY supplier_count DESC
            LIMIT 1
        """, as_dict=1)
        
        if not disabled_user:
            print("No disabled users with suppliers found")
            return
        
        user_email = disabled_user[0].name
        user_name = disabled_user[0].full_name
        supplier_count = disabled_user[0].supplier_count
        
        print(f"\n{'='*100}")
        print(f"TEST - Disabled User Email Routing")
        print(f"{'='*100}")
        print(f"Disabled User: {user_name} ({user_email})")
        print(f"Supplier Count: {supplier_count}")
        print(f"In Production Mode, email would go to: Vishnu Sharma (vishnu.sharma@hkmjaipur.org)")
        print(f"Test Mode Email: {TEST_EMAIL}")
        print(f"{'='*100}\n")
        
        # Send in test mode
        result = send_verification_email(user_email, test_mode=True)
        
        if result["success"]:
            print("✓ SUCCESS!")
            print(f"  User Status: {'DISABLED' if result.get('user_disabled') else 'ENABLED'}")
            print(f"  Email sent to: {TEST_EMAIL}")
            print(f"  Suppliers: {result['supplier_count']}")
            print(f"  In Production: Would send to Vishnu Sharma as SPOC")
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
    test_verification_email()

