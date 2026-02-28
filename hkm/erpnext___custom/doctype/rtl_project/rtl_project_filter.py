import frappe


def list(user):
    """Filter RTL Projects based on user permissions"""
    if not user:
        user = frappe.session.user

    user_roles = frappe.get_roles(user)

    # RTL Admin and Administrator have full access
    full_access = user == "Administrator" or "RTL Admin" in user_roles

    if full_access:
        return "( 1 )"

    # HODs can see projects assigned to users in their department
    is_hod = "RTL HOD" in user_roles
    if is_hod:
        # Get department members
        dept_members = frappe.db.sql("""
            SELECT DISTINCT dm.user
            FROM `tabRTL Department Member` dm
            INNER JOIN `tabRTL Department` d ON dm.parent = d.name
            WHERE d.hod = %s
        """, (user,), as_dict=False)
        
        if dept_members:
            members = [m[0] for m in dept_members]
            members.append(user)  # Include HOD themselves
            members_str = ",".join([f"'{m}'" for m in members])
            return f" ( `assigned_to` in ( {members_str} ) ) "

    # Regular users can only see their own projects
    return f" ( `assigned_to` = '{user}' ) "


def single(doc, user=None, permission_type=None):
    """Check if user has permission to access a specific RTL Project"""
    if not user:
        user = frappe.session.user

    user_roles = frappe.get_roles(user)

    # RTL Admin and Administrator have full access
    full_access = user == "Administrator" or "RTL Admin" in user_roles

    if full_access:
        return True

    # User can access their own projects
    if doc.assigned_to == user:
        return True

    # HODs can access projects assigned to users in their department
    is_hod = "RTL HOD" in user_roles
    if is_hod:
        dept_members = frappe.db.sql("""
            SELECT DISTINCT dm.user
            FROM `tabRTL Department Member` dm
            INNER JOIN `tabRTL Department` d ON dm.parent = d.name
            WHERE d.hod = %s
        """, (user,), as_dict=False)
        
        if dept_members:
            members = [m[0] for m in dept_members]
            if doc.assigned_to in members:
                return True

    return False
