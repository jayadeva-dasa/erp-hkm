"""
RTL Permission utilities for department-based access control.
"""

import frappe


def get_user_department_info(user=None):
    """
    Get department information for a user.
    Returns dict with:
    - is_rtl_admin: bool
    - is_hod: bool
    - department: str or None
    - accessible_users: list of user emails
    """
    if not user:
        user = frappe.session.user

    # Check if RTL Admin
    is_rtl_admin = "RTL Admin" in frappe.get_roles(user)

    if is_rtl_admin:
        # RTL Admin can see all users
        all_users = frappe.get_all("User", filters={"enabled": 1}, pluck="name")
        return {
            "is_rtl_admin": True,
            "is_hod": False,
            "department": None,
            "accessible_users": all_users,
        }

    # Check if user is HOD of any department
    hod_dept = frappe.db.get_value(
        "RTL Department",
        {"head_of_department": user, "is_active": 1},
        ["name", "head_of_department"],
        as_dict=True,
    )

    if hod_dept:
        # Get all members of this department
        members = frappe.get_all(
            "RTL Department Member",
            filters={"parent": hod_dept.name},
            pluck="user",
        )
        # Include HOD in accessible users
        accessible_users = [user] + members
        return {
            "is_rtl_admin": False,
            "is_hod": True,
            "department": hod_dept.name,
            "accessible_users": accessible_users,
        }

    # Check if user is a member of any department
    member_dept = frappe.db.sql(
        """
        SELECT parent as department
        FROM `tabRTL Department Member`
        WHERE user = %(user)s
        AND parenttype = 'RTL Department'
        AND EXISTS (
            SELECT 1 FROM `tabRTL Department`
            WHERE name = parent AND is_active = 1
        )
        LIMIT 1
    """,
        {"user": user},
        as_dict=True,
    )

    if member_dept:
        dept_name = member_dept[0].department
        # Get HOD and all members of this department
        dept = frappe.get_doc("RTL Department", dept_name)
        members = [m.user for m in dept.department_members]
        accessible_users = [dept.head_of_department] + members

        return {
            "is_rtl_admin": False,
            "is_hod": False,
            "department": dept_name,
            "accessible_users": accessible_users,
        }

    # User not in any department - can only see their own data
    return {
        "is_rtl_admin": False,
        "is_hod": False,
        "department": None,
        "accessible_users": [user],
    }


def can_create_project_for_user(creator, assignee):
    """Check if creator can create a project for assignee."""
    info = get_user_department_info(creator)

    # RTL Admin can create for anyone
    if info["is_rtl_admin"]:
        return True

    # HOD can create for their department members
    if info["is_hod"] and assignee in info["accessible_users"]:
        return True

    # Regular users can only create for themselves
    return creator == assignee


def get_accessible_users_for_filter(user=None):
    """Get list of users accessible to current user for filter dropdown."""
    info = get_user_department_info(user)
    
    if not info["accessible_users"]:
        return []
    
    users = frappe.get_all(
        "User",
        filters={"name": ["in", info["accessible_users"]], "enabled": 1},
        fields=["name", "full_name"],
        order_by="full_name",
    )
    
    return users
