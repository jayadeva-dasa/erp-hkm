"""
Dashboard Session Management
Thin wrapper to create web sessions after mobile app OTP verification
"""

import frappe
from hkm.mobile_app.auth import verify_otp


@frappe.whitelist(allow_guest=True)
def verify_and_login(otp, mobile=None, email=None):
    """
    Verify OTP using mobile app auth and create web session
    """
    try:
        # Use mobile app's verify_otp to validate
        result = verify_otp(otp=otp, mobile=mobile, email=email)
        
        # If OTP is valid, mobile app returns api_key and api_secret
        if result and 'api_key' in result:
            # Get user email
            if mobile:
                import re
                mobile = re.sub(r"\D", "", mobile)[-10:]
                user_doc = frappe.get_doc("User", {"mobile_no": mobile})
                user_email = user_doc.name
            else:
                user_email = email
            
            # Login user to create Frappe web session
            frappe.local.login_manager.login_as(user_email)
            
            # Get user details with roles
            user = frappe.get_doc("User", user_email)
            roles = [r.role for r in user.roles]
            
            return {
                "success": True,
                "message": "Login successful",
                "user": {
                    "email": user.email,
                    "full_name": user.full_name,
                    "user_image": user.user_image,
                    "roles": roles
                }
            }
        else:
            return {
                "success": False,
                "message": "Invalid OTP"
            }
            
    except Exception as e:
        frappe.log_error(f"Dashboard login error: {str(e)}")
        return {
            "success": False,
            "message": str(e)
        }


@frappe.whitelist()
def get_current_user():
    """Get current logged-in user details"""
    try:
        user = frappe.get_doc("User", frappe.session.user)
        roles = [r.role for r in user.roles]
        
        return {
            "success": True,
            "user": {
                "email": user.email,
                "full_name": user.full_name,
                "user_image": user.user_image,
                "roles": roles
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

