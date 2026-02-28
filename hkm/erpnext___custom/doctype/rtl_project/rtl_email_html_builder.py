"""
RTL Project Email HTML Builder
Builds HTML content for HOD status emails
"""

import frappe
from frappe.utils import getdate, nowdate, date_diff, formatdate


def build_hod_status_email(dept):
    """Build and send status matrix email to a single HOD"""
    try:
        # Get department members
        members = frappe.get_all(
            "RTL Department Member",
            filters={"parent": dept.name},
            pluck="user",
        )
        
        # Include HOD in the list
        all_users = [dept.head_of_department] + members
        
        if not all_users:
            return
        
        # Get all projects for department members
        all_projects = frappe.get_all(
            "RTL Project",
            filters={"assigned_to": ["in", all_users]},
            fields=["name", "project_name", "assigned_to", "status", "end_date", "start_date", "finish_date"],
            order_by="assigned_to, status, project_name",
        )
        
        if not all_projects:
            # No projects for this department
            return
        
        # Get user full names
        user_data = frappe.get_all(
            "User",
            filters={"name": ["in", all_users]},
            fields=["name", "full_name"],
        )
        user_names = {u.name: u.full_name or u.name for u in user_data}
        
        # Get latest status for all projects - optimized query
        project_names = [p.name for p in all_projects]
        latest_statuses = {}
        
        if project_names:
            status_entries = frappe.db.sql("""
                SELECT 
                    rds.project,
                    rds.progress_status,
                    rds.log_date,
                    rds.remarks
                FROM `tabRTL Project Daily Status` rds
                INNER JOIN (
                    SELECT project, MAX(log_date) as max_date
                    FROM `tabRTL Project Daily Status`
                    WHERE project IN %(projects)s
                    GROUP BY project
                ) latest ON rds.project = latest.project AND rds.log_date = latest.max_date
                WHERE rds.project IN %(projects)s
            """, {"projects": project_names}, as_dict=True)
            
            latest_statuses = {
                entry.project: {
                    "status": entry.progress_status,
                    "date": entry.log_date,
                    "remarks": entry.remarks,
                }
                for entry in status_entries
            }
        
        # Get projects completed today
        today = getdate(nowdate())
        completed_today = [
            p for p in all_projects
            if p.status == "Completed" and p.finish_date and getdate(p.finish_date) == today
        ]
        
        # Categorize projects
        not_started = [p for p in all_projects if p.status == "Not Started"]
        in_process = [p for p in all_projects if p.status == "In Process"]
        completed = [p for p in all_projects if p.status == "Completed"]
        
        # Build HTML sections
        matrix_html = _build_status_matrix_html(in_process, latest_statuses, user_names)
        warnings_html = _build_warnings_html(in_process, latest_statuses, user_names)
        completed_today_html = _build_completed_today_html(completed_today, user_names)
        
        # Build summary stats
        summary_html = f"""
        <div style="display: flex; gap: 15px; margin: 20px 0; flex-wrap: wrap;">
            <div style="flex: 1; min-width: 150px; background-color: #f1f5f9; padding: 15px; border-radius: 8px; text-align: center;">
                <div style="font-size: 32px; font-weight: bold; color: #64748b;">{len(not_started)}</div>
                <div style="color: #475569; font-size: 14px; margin-top: 5px;">Not Started</div>
            </div>
            <div style="flex: 1; min-width: 150px; background-color: #dbeafe; padding: 15px; border-radius: 8px; text-align: center;">
                <div style="font-size: 32px; font-weight: bold; color: #2563eb;">{len(in_process)}</div>
                <div style="color: #1e40af; font-size: 14px; margin-top: 5px;">In Process</div>
            </div>
            <div style="flex: 1; min-width: 150px; background-color: #dcfce7; padding: 15px; border-radius: 8px; text-align: center;">
                <div style="font-size: 32px; font-weight: bold; color: #16a34a;">{len(completed)}</div>
                <div style="color: #15803d; font-size: 14px; margin-top: 5px;">Completed</div>
            </div>
        </div>
        """
        
        # Build email
        subject = f"Daily RTL Project Status Report - {dept.department_name}"
        
        message = f"""
        <div style="font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto;">
            <h2 style="color: #2563eb; border-bottom: 2px solid #2563eb; padding-bottom: 10px;">
                Daily RTL Project Status Report
            </h2>
            
            <div style="background-color: #f8fafc; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p style="margin: 0; color: #475569;">
                    <strong>Department:</strong> {dept.department_name}<br>
                    <strong>Date:</strong> {formatdate(today, "dd MMM yyyy")}
                </p>
            </div>
            
            <h3 style="color: #1e293b; margin-top: 30px;">📊 Project Summary</h3>
            {summary_html}
            
            {completed_today_html}
            
            {warnings_html}
            
            <h3 style="color: #1e293b; margin-top: 30px;">📋 Status Matrix</h3>
            <p style="color: #64748b; font-size: 14px; margin-bottom: 15px;">
                Current status overview for all in-process projects
            </p>
            {matrix_html}
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0; color: #64748b; font-size: 12px;">
                <p style="margin: 0;">This is an automated daily report from the RTL Project Management System.</p>
                <p style="margin: 5px 0 0 0;">Generated at {frappe.utils.now_datetime().strftime("%I:%M %p")}</p>
            </div>
        </div>
        """
        
        frappe.sendmail(
            recipients=[dept.head_of_department],
            subject=subject,
            message=message,
            delayed=False,
        )
        
        frappe.logger().info(f"Daily status email sent to HOD {dept.head_of_department} for department {dept.name}")
        
    except Exception as e:
        frappe.logger().error(f"Error sending HOD status email for {dept.name}: {str(e)}")
        raise


def _build_status_matrix_html(in_process_projects, latest_statuses, user_names):
    """Build HTML for status matrix table"""
    if not in_process_projects:
        return '<p style="color: #64748b; font-style: italic;">No in-process projects at this time.</p>'
    
    # Group by assignee
    assignee_projects = {}
    for project in in_process_projects:
        if project.assigned_to not in assignee_projects:
            assignee_projects[project.assigned_to] = []
        assignee_projects[project.assigned_to].append(project)
    
    # Find max projects per user
    max_projects = max([len(projs) for projs in assignee_projects.values()])
    
    # Status colors
    status_colors = {
        "On Track": "#22c55e",
        "Delayed 3-7 Days": "#facc15",
        "Delayed 8-15 Days": "#f97316",
        "Delayed >15 Days (Need Help)": "#ef4444",
    }
    
    # Build table
    html = '<div style="overflow-x: auto;">'
    html += '<table style="width: 100%; border-collapse: collapse; font-size: 13px;">'
    
    # Header
    html += '<thead><tr style="background-color: #f1f5f9;">'
    html += '<th style="padding: 12px; text-align: left; border: 1px solid #e2e8f0; font-weight: 600; color: #475569;">Assignee</th>'
    html += '<th style="padding: 12px; text-align: center; border: 1px solid #e2e8f0; font-weight: 600; color: #475569;">Projects</th>'
    html += '<th style="padding: 12px; text-align: center; border: 1px solid #e2e8f0; font-weight: 600; color: #475569;">Missed Updates</th>'
    for i in range(max_projects):
        html += f'<th style="padding: 12px; text-align: center; border: 1px solid #e2e8f0; font-weight: 600; color: #475569;">Project {i+1}</th>'
    html += '</tr></thead>'
    
    # Body
    html += '<tbody>'
    for assignee in sorted(assignee_projects.keys()):
        projects = assignee_projects[assignee]
        
        # Calculate total missed updates for this assignee
        total_missed = sum(p.get("missed_daily_status_count", 0) for p in in_process_projects if p.assigned_to == assignee)
        missed_color = "#dc2626" if total_missed > 5 else ("#f59e0b" if total_missed > 0 else "#22c55e")
        
        html += '<tr>'
        html += f'<td style="padding: 12px; border: 1px solid #e2e8f0; font-weight: 500; color: #1e293b;">{user_names.get(assignee, assignee)}</td>'
        html += f'<td style="padding: 12px; border: 1px solid #e2e8f0; text-align: center; font-weight: bold; color: #2563eb;">{len(projects)}</td>'
        html += f'<td style="padding: 12px; border: 1px solid #e2e8f0; text-align: center; font-weight: 600; color: {missed_color};">{total_missed}</td>'
        
        for i in range(max_projects):
            if i < len(projects):
                project = projects[i]
                status_info = latest_statuses.get(project.name)
                
                if status_info:
                    status = status_info["status"]
                    bg_color = status_colors.get(status, "#e2e8f0")
                    text_color = "#ffffff" if status != "Delayed 3-7 Days" else "#000000"
                    
                    html += f'''<td style="padding: 8px; border: 1px solid #e2e8f0; background-color: {bg_color}; color: {text_color}; text-align: center;">
                        <div style="font-weight: 500; font-size: 12px;">{project.project_name[:30]}{'...' if len(project.project_name) > 30 else ''}</div>
                    </td>'''
                else:
                    html += f'''<td style="padding: 8px; border: 1px solid #e2e8f0; background-color: #e2e8f0; color: #64748b; text-align: center;">
                        <div style="font-weight: 500; font-size: 12px;">{project.project_name[:30]}{'...' if len(project.project_name) > 30 else ''}</div>
                        <div style="font-size: 10px; margin-top: 2px;">No Status</div>
                    </td>'''
            else:
                html += '<td style="padding: 8px; border: 1px solid #e2e8f0; background-color: #fafafa;"></td>'
        
        html += '</tr>'
    html += '</tbody>'
    html += '</table>'
    html += '</div>'
    
    # Legend
    html += '<div style="margin-top: 15px; padding: 10px; background-color: #f8fafc; border-radius: 6px;">'
    html += '<div style="font-weight: 600; color: #475569; margin-bottom: 8px; font-size: 12px;">Status Legend:</div>'
    html += '<div style="display: flex; gap: 15px; flex-wrap: wrap;">'
    for status, color in status_colors.items():
        text_color = "#ffffff" if status != "Delayed 3-7 Days" else "#000000"
        html += f'<div style="display: flex; align-items: center; gap: 5px;">'
        html += f'<div style="width: 16px; height: 16px; background-color: {color}; border-radius: 3px;"></div>'
        html += f'<span style="font-size: 11px; color: #64748b;">{status}</span>'
        html += '</div>'
    html += '<div style="display: flex; align-items: center; gap: 5px;">'
    html += '<div style="width: 16px; height: 16px; background-color: #e2e8f0; border-radius: 3px;"></div>'
    html += '<span style="font-size: 11px; color: #64748b;">No Status</span>'
    html += '</div>'
    html += '</div></div>'
    
    return html


def _build_warnings_html(in_process_projects, latest_statuses, user_names):
    """Build HTML for warnings and alerts section"""
    warnings = []
    
    today = getdate(nowdate())
    
    for project in in_process_projects:
        status_info = latest_statuses.get(project.name)
        status = status_info["status"] if status_info else None
        
        # Check for critical delays
        if status == "Delayed >15 Days (Need Help)":
            warnings.append({
                "level": "critical",
                "message": f"<strong>{project.project_name}</strong> assigned to {user_names.get(project.assigned_to, project.assigned_to)} is severely delayed and needs immediate attention.",
            })
        elif status == "Delayed 8-15 Days":
            warnings.append({
                "level": "warning",
                "message": f"<strong>{project.project_name}</strong> assigned to {user_names.get(project.assigned_to, project.assigned_to)} is significantly delayed.",
            })
        
        # Check for no status updates
        if not status_info:
            warnings.append({
                "level": "info",
                "message": f"<strong>{project.project_name}</strong> assigned to {user_names.get(project.assigned_to, project.assigned_to)} has no status update yet.",
            })
        
        # Check for approaching deadlines
        end_date = getdate(project.end_date)
        days_remaining = date_diff(end_date, today)
        if days_remaining <= 2 and days_remaining >= 0 and status == "On Track":
            warnings.append({
                "level": "info",
                "message": f"<strong>{project.project_name}</strong> assigned to {user_names.get(project.assigned_to, project.assigned_to)} is due in {days_remaining} day{'s' if days_remaining != 1 else ''}.",
            })
    
    if not warnings:
        return ""
    
    html = '<h3 style="color: #1e293b; margin-top: 30px;">⚠️ Alerts & Warnings</h3>'
    
    # Group by level
    critical = [w for w in warnings if w["level"] == "critical"]
    warning = [w for w in warnings if w["level"] == "warning"]
    info = [w for w in warnings if w["level"] == "info"]
    
    if critical:
        html += '<div style="background-color: #fef2f2; border-left: 4px solid #dc2626; padding: 15px; margin: 10px 0; border-radius: 4px;">'
        html += '<div style="font-weight: bold; color: #991b1b; margin-bottom: 8px;">🚨 Critical Issues</div>'
        html += '<ul style="margin: 0; padding-left: 20px; color: #7f1d1d;">'
        for w in critical:
            html += f'<li style="margin: 5px 0;">{w["message"]}</li>'
        html += '</ul></div>'
    
    if warning:
        html += '<div style="background-color: #fff7ed; border-left: 4px solid #f97316; padding: 15px; margin: 10px 0; border-radius: 4px;">'
        html += '<div style="font-weight: bold; color: #9a3412; margin-bottom: 8px;">⚠️ Warnings</div>'
        html += '<ul style="margin: 0; padding-left: 20px; color: #78350f;">'
        for w in warning:
            html += f'<li style="margin: 5px 0;">{w["message"]}</li>'
        html += '</ul></div>'
    
    if info:
        html += '<div style="background-color: #eff6ff; border-left: 4px solid #3b82f6; padding: 15px; margin: 10px 0; border-radius: 4px;">'
        html += '<div style="font-weight: bold; color: #1e40af; margin-bottom: 8px;">ℹ️ Information</div>'
        html += '<ul style="margin: 0; padding-left: 20px; color: #1e3a8a;">'
        for w in info:
            html += f'<li style="margin: 5px 0;">{w["message"]}</li>'
        html += '</ul></div>'
    
    return html


def _build_completed_today_html(completed_today, user_names):
    """Build HTML for projects completed today"""
    if not completed_today:
        return ""
    
    html = '<h3 style="color: #1e293b; margin-top: 30px;">✅ Completed Today</h3>'
    html += '<div style="background-color: #f0fdf4; border-left: 4px solid #22c55e; padding: 15px; margin: 10px 0; border-radius: 4px;">'
    html += '<ul style="margin: 0; padding-left: 20px; color: #15803d;">'
    for project in completed_today:
        html += f'<li style="margin: 5px 0;"><strong>{project.project_name}</strong> by {user_names.get(project.assigned_to, project.assigned_to)}</li>'
    html += '</ul></div>'
    
    return html
