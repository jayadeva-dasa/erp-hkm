import frappe


@frappe.whitelist()
def get_context(assignee: str | None = None):
    """Get dashboard context - delegates to RTL Project API"""
    from hkm.erpnext___custom.doctype.rtl_project import rtl_project_api
    
    return rtl_project_api.get_dashboard_context(assignee)


@frappe.whitelist()
def create_project(data):
    """Create project - delegates to RTL Project API"""
    from hkm.erpnext___custom.doctype.rtl_project import rtl_project_api
    
    return rtl_project_api.create_project(data)


@frappe.whitelist()
def update_project_status(project: str, status: str):
    """Update project status - delegates to RTL Project API"""
    from hkm.erpnext___custom.doctype.rtl_project import rtl_project_api
    
    return rtl_project_api.update_project_status(project, status)


@frappe.whitelist()
def bulk_log_daily_status(entries):
    """Bulk log daily status - delegates to RTL Project API"""
    from hkm.erpnext___custom.doctype.rtl_project import rtl_project_api
    
    return rtl_project_api.bulk_daily_status(entries)


@frappe.whitelist()
def get_progress_options():
    meta = frappe.get_meta("RTL Project Daily Status")
    field = meta.get_field("progress_status")
    if not field:
        return []
    options = (field.options or "").split("\n")
    return [opt.strip() for opt in options if opt.strip()]


@frappe.whitelist()
def get_assignees():
    frappe.only_for("RTL Admin")
    return frappe.get_all(
        "User",
        filters={"enabled": 1, "user_type": "System User"},
        fields=["name", "full_name", "email"],
        order_by="full_name"
    )


@frappe.whitelist()
def search_assignees(query: str = "", limit: int = 20):
    frappe.only_for("RTL Admin")
    query = (query or "").strip()
    limit = min(max(int(limit or 20), 1), 50)

    filters = {
        "enabled": 1,
        "user_type": "System User",
    }

    if query:
        like_value = f"%{query}%"
        or_filters = {
            "name": ["like", like_value],
            "email": ["like", like_value],
            "full_name": ["like", like_value],
        }
    else:
        or_filters = None

    rows = frappe.get_all(
        "User",
        filters=filters,
        or_filters=or_filters,
        fields=["name", "full_name", "email"],
        order_by="full_name",
        limit=limit,
    )

    return [
        {
            "value": row.name,
            "label": f"{row.full_name or row.name} ({row.email})" if row.email else (row.full_name or row.name),
        }
        for row in rows
    ]


@frappe.whitelist()
def get_matrix_data(assignee=None):
    """Get consolidated status matrix for all users and projects."""
    from hkm.erpnext___custom.utils.rtl_permissions import (
        get_user_department_info,
    )
    from datetime import date
    
    user = frappe.session.user
    dept_info = get_user_department_info(user)
    accessible_users = dept_info["accessible_users"]

    # If assignee filter is provided, validate access
    if assignee:
        if assignee not in accessible_users:
            frappe.throw("You do not have permission to view this user's data.")
        filters = {"status": "In Process", "assigned_to": assignee}
    else:
        # Show all accessible users' projects
        filters = {"status": "In Process", "assigned_to": ["in", accessible_users]}

    projects = frappe.get_all(
        "RTL Project",
        filters=filters,
        fields=["name", "project_name", "assigned_to", "missed_daily_status_count"],
        order_by="assigned_to, project_name",
    )

    # Get latest status for each project
    latest_statuses = {}
    if projects:
        project_names = [p.name for p in projects]
        status_entries = frappe.db.sql("""
            SELECT 
                rds.project,
                rds.progress_status,
                rds.log_date
            FROM `tabRTL Project Daily Status` rds
            INNER JOIN (
                SELECT project, MAX(log_date) as max_date
                FROM `tabRTL Project Daily Status`
                WHERE project IN %(projects)s
                GROUP BY project
            ) latest ON rds.project = latest.project AND rds.log_date = latest.max_date
        """, {"projects": project_names}, as_dict=True)
        
        for entry in status_entries:
            latest_statuses[entry.project] = {
                "status": entry.progress_status,
                "date": entry.log_date,
            }

    # Get user full names
    user_names = {}
    if projects:
        unique_users = list(set([p.assigned_to for p in projects]))
        user_data = frappe.get_all("User", filters={"name": ["in", unique_users]}, fields=["name", "full_name"])
        user_names = {u.name: u.full_name or u.name for u in user_data}

    # Group projects by assignee
    assignee_projects = {}
    for project in projects:
        if project.assigned_to not in assignee_projects:
            assignee_projects[project.assigned_to] = []
        
        project_data = {
            "id": project.name,
            "name": project.project_name,
            "status": None,
            "status_date": None,
        }
        
        if project.name in latest_statuses:
            project_data["status"] = latest_statuses[project.name]["status"]
            project_data["status_date"] = latest_statuses[project.name]["date"]
        
        assignee_projects[project.assigned_to].append(project_data)

    # Find max projects per user
    max_projects = max([len(projs) for projs in assignee_projects.values()]) if assignee_projects else 0

    # Calculate total missed updates for each assignee from project field
    missed_updates = {}
    for assignee_email in assignee_projects.keys():
        total_missed = sum(
            p.get("missed_daily_status_count", 0) 
            for p in projects 
            if p.assigned_to == assignee_email
        )
        missed_updates[assignee_email] = total_missed

    # Build matrix rows
    rows = []
    for assignee_email in sorted(assignee_projects.keys()):
        user_projects = assignee_projects[assignee_email]
        row = {
            "assignee": user_names.get(assignee_email, assignee_email),
            "assignee_email": assignee_email,
            "projects": user_projects,
            "missed_updates": missed_updates.get(assignee_email, 0),
        }
        rows.append(row)

    # Get progress colors
    progress_colors = _get_progress_colors()

    return {
        "rows": rows,
        "max_projects": max_projects,
        "colors": progress_colors,
    }


def _get_progress_colors():
    return {
        "On Track": "#22c55e",
        "Delayed 3-7 Days": "#facc15",
        "Delayed 8-15 Days": "#f97316",
        "Delayed >15 Days (Need Help)": "#ef4444",
    }
