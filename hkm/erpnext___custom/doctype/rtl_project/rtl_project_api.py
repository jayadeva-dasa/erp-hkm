"""
RTL Project API
Centralized API endpoints for RTL Project management
"""

import frappe
from frappe.utils import nowdate
from hkm.erpnext___custom.utils.rtl_permissions import (
    get_user_department_info,
    get_accessible_users_for_filter,
)


def _is_admin(user: str | None = None) -> bool:
    """Check if user is RTL Admin"""
    user = user or frappe.session.user
    return user == "Administrator" or "RTL Admin" in frappe.get_roles(user)


def _get_progress_options():
    """Get progress status options from DocType meta"""
    meta = frappe.get_meta("RTL Project Daily Status")
    field = meta.get_field("progress_status")
    options = (field.options or "").split("\n") if field else []
    return [opt.strip() for opt in options if opt.strip()]


@frappe.whitelist()
def get_dashboard_context(assignee: str | None = None):
    """Get dashboard context with projects grouped by status"""
    user = frappe.session.user
    dept_info = get_user_department_info(user)

    # Determine which users this user can view
    accessible_users = dept_info["accessible_users"]

    # If assignee filter is provided, validate access
    if assignee:
        if assignee not in accessible_users:
            frappe.throw("You do not have permission to view this user's projects.")
        filters = {"assigned_to": assignee}
    else:
        # Show all accessible users' projects
        filters = {"assigned_to": ["in", accessible_users]}

    projects = frappe.get_all(
        "RTL Project",
        filters=filters,
        fields=["name", "project_name", "description", "assigned_to", "end_date", "start_date", "finish_date", "status"],
        order_by="status, assigned_to, project_name",
    )

    # If no projects, return early
    if not projects:
        return {
            "is_rtl_admin": dept_info["is_rtl_admin"],
            "is_hod": dept_info["is_hod"],
            "department": dept_info["department"],
            "assignee": assignee,
            "projects": {
                "not_started": [],
                "in_process": [],
                "completed": [],
            },
            "progress_options": _get_progress_options(),
            "progress_colors": {
                "On Track": "#22c55e",
                "Delayed 3-7 Days": "#facc15",
                "Delayed 8-15 Days": "#f97316",
                "Delayed >15 Days (Need Help)": "#ef4444",
            },
            "assignees": get_accessible_users_for_filter(user),
            "today": nowdate(),
            "total_missed_daily_status": 0,
        }
    
    # Get user full names
    unique_users = list(set([p["assigned_to"] for p in projects]))
    user_data = frappe.get_all("User", filters={"name": ["in", unique_users]}, fields=["name", "full_name"])
    user_names = {u.name: u.full_name or u.name for u in user_data}
    
    # Add full names to projects
    for project in projects:
        project["assigned_to_name"] = user_names.get(project.assigned_to, project.assigned_to)
    
    # Optimized: Get latest status and today's status
    project_names = [p["name"] for p in projects]
    today = nowdate()
    
    # Get latest status for each project
    latest_statuses = frappe.db.sql(
        """
        SELECT ds.project, ds.log_date, ds.progress_status, ds.remarks
        FROM `tabRTL Project Daily Status` ds
        INNER JOIN (
            SELECT project, MAX(log_date) as max_date
            FROM `tabRTL Project Daily Status`
            WHERE project IN %(projects)s
            GROUP BY project
        ) latest ON ds.project = latest.project AND ds.log_date = latest.max_date
        WHERE ds.project IN %(projects)s
        """,
        {"projects": tuple(project_names)},
        as_dict=True,
    )
    
    latest_status_map = {}
    for row in latest_statuses:
        latest_status_map[row.project] = {
            "log_date": row.log_date,
            "progress_status": row.progress_status,
            "remarks": row.remarks,
        }
    
    # Get today's status entries
    today_statuses = frappe.get_all(
        "RTL Project Daily Status",
        filters={"project": ["in", project_names], "log_date": today},
        fields=["project"],
    )
    today_status_map = {row.project: True for row in today_statuses}

    buckets = {
        "not_started": [],
        "in_process": [],
        "completed": [],
    }

    for proj in projects:
        info = frappe._dict(proj)
        info["latest_status"] = latest_status_map.get(proj.name)
        info["today_filed"] = today_status_map.get(proj.name, False)

        if proj.status == "Not Started":
            buckets["not_started"].append(info)
        else:
            target_bucket = "completed" if proj.status == "Completed" else "in_process"
            buckets[target_bucket].append(info)

    # Get assignees for filter dropdown
    assignees = get_accessible_users_for_filter(user)

    # Calculate total missed daily status updates for all projects
    total_missed_count = 0
    for project in projects:
        total_missed_count += project.get("missed_daily_status_count", 0)

    return {
        "is_rtl_admin": dept_info["is_rtl_admin"],
        "is_hod": dept_info["is_hod"],
        "department": dept_info["department"],
        "assignee": assignee,
        "projects": buckets,
        "progress_options": _get_progress_options(),
        "progress_colors": {
            "On Track": "#22c55e",
            "Delayed 3-7 Days": "#facc15",
            "Delayed 8-15 Days": "#f97316",
            "Delayed >15 Days (Need Help)": "#ef4444",
        },
        "assignees": assignees,
        "today": nowdate(),
        "total_missed_daily_status": total_missed_count,
    }


@frappe.whitelist()
def create_project(data: dict | str):
    """Create a new RTL Project"""
    from hkm.erpnext___custom.utils.rtl_permissions import can_create_project_for_user

    user = frappe.session.user
    values = frappe.parse_json(data) if isinstance(data, str) else data
    assignee = values.get("assigned_to")

    if not can_create_project_for_user(user, assignee):
        frappe.throw("You do not have permission to create projects for this user.")

    doc = frappe.new_doc("RTL Project")
    doc.project_name = values.get("project_name")
    doc.description = values.get("description")
    doc.assigned_to = assignee
    doc.end_date = values.get("end_date")
    doc.status = "Not Started"
    doc.insert(ignore_permissions=True)
    return doc.as_dict()


@frappe.whitelist()
def update_project_status(project: str, status: str):
    """Update project status with permission checks"""
    if status not in {"Not Started", "In Process", "Completed"}:
        frappe.throw("Invalid status supplied.")

    doc = frappe.get_doc("RTL Project", project)
    user = frappe.session.user
    is_admin = _is_admin(user)

    if status == "Completed" and doc.assigned_to != user and not is_admin:
        frappe.throw("Only the assigned user or RTL Admin can mark project as completed.")

    if status == "Not Started" and not is_admin:
        frappe.throw("Only RTL Admin can reset to Not Started.")

    if doc.assigned_to != user and not is_admin:
        frappe.throw("You can only update your assigned projects.")

    doc.status = status
    doc.save(ignore_permissions=False)
    return doc.as_dict()


@frappe.whitelist()
def bulk_daily_status(entries: list | str):
    """Bulk create daily status entries for multiple projects with validation"""
    payload = frappe.parse_json(entries) if isinstance(entries, str) else entries
    if not isinstance(payload, list):
        frappe.throw("Invalid payload. Expected a list of status records.")

    created = []
    errors = []
    
    for row in payload:
        if not row or not isinstance(row, dict):
            continue
            
        project = row.get("project")
        progress_status = row.get("progress_status")
        
        if not project or not progress_status:
            errors.append(f"Missing project or status in entry: {row}")
            continue

        try:
            # Validate project exists and is in process
            project_doc = frappe.get_doc("RTL Project", project)
            if project_doc.status != "In Process":
                errors.append(f"Project {project} is not in process")
                continue
                
            # Check if today's status already exists
            today = nowdate()
            existing = frappe.db.exists("RTL Project Daily Status", {
                "project": project,
                "log_date": today
            })
            
            if existing:
                errors.append(f"Status for {project} already exists for today")
                continue

            doc = frappe.new_doc("RTL Project Daily Status")
            doc.project = project
            doc.log_date = today
            doc.progress_status = progress_status
            doc.remarks = row.get("remarks") or ""
            doc.insert(ignore_permissions=True)
            created.append(doc.name)
            
        except frappe.DoesNotExistError:
            errors.append(f"Project {project} does not exist")
        except Exception as e:
            frappe.log_error(f"Error creating status for project {project}: {str(e)}")
            errors.append(f"Error creating status for {project}: {str(e)}")

    result = {
        "success": len(created) > 0,
        "created": created,
        "created_count": len(created)
    }
    
    if errors:
        result["errors"] = errors
        result["error_count"] = len(errors)
        
    return result


@frappe.whitelist()
def get_project(project_name: str):
    """Get a project with permission checks for HOD/Admin"""
    user = frappe.session.user
    dept_info = get_user_department_info(user)
    
    # Get the project document (ignore permissions since we validate manually)
    doc = frappe.get_doc("RTL Project", project_name, ignore_permissions=True)
    
    # Check permissions: Admin, HOD with access, or assignee
    if not dept_info["is_rtl_admin"]:
        if dept_info["is_hod"]:
            # HOD can access department members' projects
            accessible_users = dept_info["accessible_users"]
            if doc.assigned_to not in accessible_users:
                frappe.throw("You do not have permission to view this project.")
        elif user != doc.assigned_to:
            # Regular users can only access their own projects
            frappe.throw("You do not have permission to view this project.")
    
    return doc.as_dict()


@frappe.whitelist()
def update_project(project_name: str, values: dict | str):
    """Update an existing RTL Project - only for RTL Admin or HOD"""
    user = frappe.session.user
    dept_info = get_user_department_info(user)
    
    # Only RTL Admin or HOD can update projects
    if not (dept_info["is_rtl_admin"] or dept_info["is_hod"]):
        frappe.throw("Only RTL Admin or Department HOD can edit projects.")
    
    # Parse values if it's a JSON string
    if isinstance(values, str):
        values = frappe.parse_json(values)
    
    # Get the project document (ignore permissions since we validate manually)
    doc = frappe.get_doc("RTL Project", project_name, ignore_permissions=True)
    
    # Check if HOD has access to this project's assignee
    if dept_info["is_hod"] and not dept_info["is_rtl_admin"]:
        accessible_users = dept_info["accessible_users"]
        if doc.assigned_to not in accessible_users:
            frappe.throw("You do not have permission to edit this project.")
        
        # Also check if the new assignee is accessible
        new_assignee = values.get("assigned_to")
        if new_assignee and new_assignee not in accessible_users:
            frappe.throw("You can only assign projects to users in your department.")
    
    # Update fields
    if "project_name" in values:
        doc.project_name = values["project_name"]
    if "description" in values:
        doc.description = values["description"]
    if "assigned_to" in values:
        doc.assigned_to = values["assigned_to"]
    if "end_date" in values:
        doc.end_date = values["end_date"]
    
    doc.save(ignore_permissions=True)
    return doc.as_dict()


@frappe.whitelist()
def delete_project(project_name: str):
    """Delete an RTL Project - only for RTL Admin or HOD"""
    user = frappe.session.user
    dept_info = get_user_department_info(user)
    
    # Only RTL Admin or HOD can delete projects
    if not (dept_info["is_rtl_admin"] or dept_info["is_hod"]):
        frappe.throw("Only RTL Admin or Department HOD can delete projects.")
    
    # Get the project document (ignore permissions since we validate manually)
    doc = frappe.get_doc("RTL Project", project_name, ignore_permissions=True)
    
    # Check if HOD has access to this project's assignee
    if dept_info["is_hod"] and not dept_info["is_rtl_admin"]:
        accessible_users = dept_info["accessible_users"]
        if doc.assigned_to not in accessible_users:
            frappe.throw("You do not have permission to delete this project.")
    
    # Delete the project
    frappe.delete_doc("RTL Project", project_name, ignore_permissions=True)
    
    return {"success": True, "message": "Project deleted successfully"}


@frappe.whitelist()
def create_project_schedule(values: dict | str):
    """Create a new RTL Project Schedule - only for RTL Admin or HOD"""
    user = frappe.session.user
    dept_info = get_user_department_info(user)
    
    # Only RTL Admin or HOD can create schedules
    if not (dept_info["is_rtl_admin"] or dept_info["is_hod"]):
        frappe.throw("Only RTL Admin or Department HOD can create project schedules.")
    
    # Parse values if it's a JSON string
    if isinstance(values, str):
        values = frappe.parse_json(values)
    
    # Validate assignee access for HOD
    assignee = values.get("assigned_to")
    if dept_info["is_hod"] and not dept_info["is_rtl_admin"]:
        accessible_users = dept_info["accessible_users"]
        if assignee not in accessible_users:
            frappe.throw("You can only create schedules for users in your department.")
    
    # Create the schedule
    doc = frappe.new_doc("RTL Project Schedule")
    doc.schedule_name = values.get("schedule_name")
    doc.project_template = values.get("project_template")
    doc.description = values.get("description")
    doc.frequency = values.get("frequency")
    doc.start_day = values.get("start_day")
    doc.duration_days = values.get("duration_days")
    doc.assigned_to = assignee
    doc.first_run_date = values.get("first_run_date")
    doc.is_active = 1
    doc.insert(ignore_permissions=True)
    
    return doc.as_dict()


@frappe.whitelist()
def get_project_schedules():
    """Get all project schedules accessible to the user"""
    user = frappe.session.user
    dept_info = get_user_department_info(user)
    
    # Determine accessible users
    accessible_users = dept_info["accessible_users"]
    
    # Get schedules
    schedules = frappe.get_all(
        "RTL Project Schedule",
        filters={"assigned_to": ["in", accessible_users]},
        fields=[
            "name",
            "schedule_name",
            "project_template",
            "frequency",
            "duration_days",
            "assigned_to",
            "is_active",
            "first_run_date",
            "next_creation_date",
            "last_created_project",
            "last_run_date"
        ],
        order_by="creation desc"
    )
    
    return schedules


@frappe.whitelist()
def toggle_schedule_status(schedule_name: str, is_active: int):
    """Toggle schedule active status - only for RTL Admin or HOD"""
    user = frappe.session.user
    dept_info = get_user_department_info(user)
    
    # Only RTL Admin or HOD can toggle schedules
    if not (dept_info["is_rtl_admin"] or dept_info["is_hod"]):
        frappe.throw("Only RTL Admin or Department HOD can manage schedules.")
    
    doc = frappe.get_doc("RTL Project Schedule", schedule_name)
    
    # Check if HOD has access
    if dept_info["is_hod"] and not dept_info["is_rtl_admin"]:
        accessible_users = dept_info["accessible_users"]
        if doc.assigned_to not in accessible_users:
            frappe.throw("You do not have permission to modify this schedule.")
    
    doc.is_active = is_active
    doc.save(ignore_permissions=True)
    
    return {"success": True}


@frappe.whitelist()
def delete_schedule(schedule_name: str):
    """Delete a project schedule - only for RTL Admin or HOD"""
    user = frappe.session.user
    dept_info = get_user_department_info(user)
    
    # Only RTL Admin or HOD can delete schedules
    if not (dept_info["is_rtl_admin"] or dept_info["is_hod"]):
        frappe.throw("Only RTL Admin or Department HOD can delete schedules.")
    
    doc = frappe.get_doc("RTL Project Schedule", schedule_name)
    
    # Check if HOD has access
    if dept_info["is_hod"] and not dept_info["is_rtl_admin"]:
        accessible_users = dept_info["accessible_users"]
        if doc.assigned_to not in accessible_users:
            frappe.throw("You do not have permission to delete this schedule.")
    
    frappe.delete_doc("RTL Project Schedule", schedule_name, ignore_permissions=True)
    
    return {"success": True}

