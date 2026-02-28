"""
Dashboard Configuration API
Simple wrapper for dashboard access configuration
"""

import frappe
import os
import json
from pathlib import Path


@frappe.whitelist()
def get_config():
    """Get dashboard configuration filtered by user roles"""
    try:
        config_path = Path(__file__).parent.parent.parent / "config" / "dashboard_access_config.json"
        if config_path.exists():
        with open(config_path, 'r') as f:
                return json.load(f)
        else:
            return {"error": "Config file not found"}
    except Exception as e:
        frappe.log_error(f"Dashboard config error: {str(e)}")
        return {"modules": {}, "settings": {}}


@frappe.whitelist()
def check_module_access(module_name):
    """Check if user has access to a specific module"""
    try:
        config = get_config()
        if "error" in config:
            return {"allowed": False, "message": config["error"]}
        
        user_roles = frappe.get_roles()
        module_config = config.get("modules", {}).get(module_name, {})
        required_roles = module_config.get("allowed_roles", [])
        
        if not required_roles:
            return {"allowed": True}
        
        has_access = any(role in user_roles for role in required_roles)
        return {"allowed": has_access, "required_roles": required_roles}
    except Exception as e:
        frappe.log_error(f"Module access check error: {str(e)}")
        return {"has_access": False}

