"""
RTL Project Email Notifications
Handles automated email communications for RTL Projects
"""

import frappe
from frappe.utils import getdate, nowdate, add_days, date_diff, formatdate
from frappe import _


def send_project_creation_email(project_doc):
    """
    Send email to assignee when a new project is created.
    Called from RTL Project after_insert hook.
    """
    try:
        # Get assignee details
        user = frappe.get_doc("User", project_doc.assigned_to)
        
        # Prepare email content
        subject = f"New Project Assigned: {project_doc.project_name}"
        
        # Build email message
        message = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2563eb; border-bottom: 2px solid #2563eb; padding-bottom: 10px;">
                New Project Assigned to You
            </h2>
            
            <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #1e293b; margin-top: 0;">Project Details</h3>
                
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold; color: #475569; width: 40%;">Project Name:</td>
                        <td style="padding: 8px 0; color: #1e293b;">{project_doc.project_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold; color: #475569;">Status:</td>
                        <td style="padding: 8px 0; color: #1e293b;">{project_doc.status}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold; color: #475569;">End Date:</td>
                        <td style="padding: 8px 0; color: #ef4444; font-weight: bold;">
                            {formatdate(project_doc.end_date, "dd MMM yyyy")}
                        </td>
                    </tr>
                    {f'''<tr>
                        <td style="padding: 8px 0; font-weight: bold; color: #475569;">Start Date:</td>
                        <td style="padding: 8px 0; color: #1e293b;">{formatdate(project_doc.start_date, "dd MMM yyyy")}</td>
                    </tr>''' if project_doc.start_date else ''}
                </table>
            </div>
            
            {f'''<div style="background-color: #fff7ed; padding: 15px; border-left: 4px solid #f97316; margin: 20px 0;">
                <h4 style="color: #9a3412; margin-top: 0;">Description:</h4>
                <p style="color: #78350f; margin: 0; white-space: pre-wrap;">{project_doc.description}</p>
            </div>''' if project_doc.description else ''}
            
            <div style="margin-top: 30px; padding: 15px; background-color: #eff6ff; border-radius: 8px;">
                <p style="margin: 0; color: #1e40af;">
                    <strong>Action Required:</strong> Please review this project and start working on it as per the timeline.
                </p>
            </div>
            
            <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #e2e8f0; color: #64748b; font-size: 12px;">
                <p style="margin: 0;">This is an automated notification from the RTL Project Management System.</p>
            </div>
        </div>
        """
        
        # Send email
        frappe.sendmail(
            recipients=[project_doc.assigned_to],
            subject=subject,
            message=message,
            delayed=False,
            reference_doctype="RTL Project",
            reference_name=project_doc.name,
        )
        
        frappe.logger().info(f"Project creation email sent to {project_doc.assigned_to} for project {project_doc.name}")
        
    except Exception as e:
        frappe.logger().error(f"Error sending project creation email for {project_doc.name}: {str(e)}")
        # Don't throw error to avoid blocking project creation


def send_deadline_reminder_emails():
    """
    Send deadline reminder emails based on project status and timing.
    Called by scheduled task daily.
    
    Logic:
    - On Track: Send 1 day before end_date
    - Delayed 3-7 Days: Send on end_date + 3 days
    - Delayed 8-15 Days: Send on end_date + 8 days
    - Delayed >15 Days: Send on end_date + 15 days
    - No Status: Send 1 day before end_date
    """
    try:
        today = getdate(nowdate())
        
        # Get all in-process projects
        projects = frappe.get_all(
            "RTL Project",
            filters={"status": "In Process"},
            fields=["name", "project_name", "description", "assigned_to", "end_date", "start_date"],
        )
        
        if not projects:
            return
        
        # Get latest status for each project - optimized query
        project_names = [p.name for p in projects]
        latest_statuses = {}
        
        if project_names:
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
                WHERE rds.project IN %(projects)s
            """, {"projects": project_names}, as_dict=True)
            
            latest_statuses = {entry.project: entry.progress_status for entry in status_entries}
        
        # Process each project
        emails_sent = 0
        for project in projects:
            end_date = getdate(project.end_date)
            status = latest_statuses.get(project.name)
            
            should_send = False
            
            if status == "On Track" or not status:
                # Send 1 day before end date
                if today == add_days(end_date, -1):
                    should_send = True
            elif status == "Delayed 3-7 Days":
                # Send on end_date + 3 days
                if today == add_days(end_date, 3):
                    should_send = True
            elif status == "Delayed 8-15 Days":
                # Send on end_date + 8 days
                if today == add_days(end_date, 8):
                    should_send = True
            elif status == "Delayed >15 Days (Need Help)":
                # Send on end_date + 15 days
                if today == add_days(end_date, 15):
                    should_send = True
            
            if should_send:
                _send_deadline_reminder(project, status, end_date)
                emails_sent += 1
        
        if emails_sent > 0:
            frappe.logger().info(f"Sent {emails_sent} deadline reminder emails")
            
    except Exception as e:
        frappe.logger().error(f"Error in send_deadline_reminder_emails: {str(e)}")


def _send_deadline_reminder(project, status, end_date):
    """Send individual deadline reminder email"""
    try:
        # Get assignee details
        user = frappe.get_doc("User", project.assigned_to)
        
        # Calculate days info
        today = getdate(nowdate())
        days_diff = date_diff(end_date, today)
        
        if days_diff >= 0:
            urgency_text = f"in {days_diff} day{'s' if days_diff != 1 else ''}"
            urgency_color = "#ef4444"
        else:
            urgency_text = f"{abs(days_diff)} day{'s' if abs(days_diff) != 1 else ''} overdue"
            urgency_color = "#dc2626"
        
        # Status badge
        status_badge = ""
        if status:
            status_colors = {
                "On Track": "#22c55e",
                "Delayed 3-7 Days": "#facc15",
                "Delayed 8-15 Days": "#f97316",
                "Delayed >15 Days (Need Help)": "#ef4444",
            }
            status_color = status_colors.get(status, "#64748b")
            status_badge = f'''
            <div style="display: inline-block; background-color: {status_color}; color: white; 
                        padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: bold; margin-top: 10px;">
                {status}
            </div>
            '''
        
        subject = f"⚠️ Project Deadline Alert: {project.project_name}"
        
        message = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #dc2626; border-bottom: 2px solid #dc2626; padding-bottom: 10px;">
                ⚠️ Project Deadline Alert
            </h2>
            
            <div style="background-color: #fef2f2; padding: 20px; border-left: 4px solid #dc2626; margin: 20px 0;">
                <h3 style="color: #991b1b; margin-top: 0;">Urgent: Action Required</h3>
                <p style="color: #7f1d1d; font-size: 16px; margin: 10px 0;">
                    This project is reaching its deadline very soon. Please focus and complete it immediately.
                </p>
            </div>
            
            <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #1e293b; margin-top: 0;">Project Details</h3>
                
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold; color: #475569; width: 40%;">Project Name:</td>
                        <td style="padding: 8px 0; color: #1e293b;">{project.project_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold; color: #475569;">Deadline:</td>
                        <td style="padding: 8px 0; color: {urgency_color}; font-weight: bold;">
                            {formatdate(end_date, "dd MMM yyyy")} ({urgency_text})
                        </td>
                    </tr>
                    {f'''<tr>
                        <td style="padding: 8px 0; font-weight: bold; color: #475569;">Start Date:</td>
                        <td style="padding: 8px 0; color: #1e293b;">{formatdate(project.start_date, "dd MMM yyyy")}</td>
                    </tr>''' if project.start_date else ''}
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold; color: #475569;">Current Status:</td>
                        <td style="padding: 8px 0;">{status_badge if status else '<span style="color: #64748b;">No status reported</span>'}</td>
                    </tr>
                </table>
            </div>
            
            {f'''<div style="background-color: #fff7ed; padding: 15px; border-left: 4px solid #f97316; margin: 20px 0;">
                <h4 style="color: #9a3412; margin-top: 0;">Description:</h4>
                <p style="color: #78350f; margin: 0; white-space: pre-wrap;">{project.description}</p>
            </div>''' if project.description else ''}
            
            <div style="margin-top: 30px; padding: 15px; background-color: #eff6ff; border-radius: 8px;">
                <p style="margin: 0; color: #1e40af;">
                    <strong>Next Steps:</strong> Please prioritize this project and update your progress status in the RTL Project Dashboard.
                </p>
            </div>
            
            <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #e2e8f0; color: #64748b; font-size: 12px;">
                <p style="margin: 0;">This is an automated reminder from the RTL Project Management System.</p>
            </div>
        </div>
        """
        
        frappe.sendmail(
            recipients=[project.assigned_to],
            subject=subject,
            message=message,
            delayed=False,
            reference_doctype="RTL Project",
            reference_name=project.name,
        )
        
        frappe.logger().info(f"Deadline reminder sent to {project.assigned_to} for project {project.name}")
        
    except Exception as e:
        frappe.logger().error(f"Error sending deadline reminder for {project.name}: {str(e)}")


def send_daily_status_matrix_to_hods():
    """
    Send daily status matrix email to all Department HODs at 7 PM.
    Called by scheduled task daily.
    """
    from hkm.erpnext___custom.doctype.rtl_project.rtl_email_html_builder import build_hod_status_email
    
    try:
        # Get all active departments
        departments = frappe.get_all(
            "RTL Department",
            filters={"is_active": 1},
            fields=["name", "department_name", "head_of_department"],
        )
        
        if not departments:
            return
        
        emails_sent = 0
        for dept in departments:
            try:
                build_hod_status_email(dept)
                emails_sent += 1
            except Exception as e:
                frappe.logger().error(f"Error sending status email to HOD of {dept.name}: {str(e)}")
                continue
        
        if emails_sent > 0:
            frappe.logger().info(f"Sent {emails_sent} daily status matrix emails to HODs")
            
    except Exception as e:
        frappe.logger().error(f"Error in send_daily_status_matrix_to_hods: {str(e)}")


def send_daily_status_reminders():
    """
    Send daily status reminder emails to assignees who haven't updated all their projects.
    Called by scheduled task daily at configured time (default 6 PM).
    
    Logic:
    - Skip if today is a holiday
    - Skip if employee is on approved leave
    - Find users with active projects who haven't updated daily status for all projects
    - Send reminder with counts of missing updates and not started projects
    """
    try:
        today = getdate(nowdate())
        
        # Check if today is a holiday
        if _is_today_holiday(today):
            frappe.logger().info("Skipping daily status reminders - today is a holiday")
            return
        
        # Get all users on approved leave today
        users_on_leave = _get_users_on_leave_today(today)
        
        # Get all active projects grouped by assignee
        projects_by_user = {}
        all_projects = frappe.get_all(
            "RTL Project",
            filters={"status": ["in", ["Not Started", "In Process"]]},
            fields=["name", "project_name", "assigned_to", "status", "missed_daily_status_count"],
        )
        
        for project in all_projects:
            if project.assigned_to not in projects_by_user:
                projects_by_user[project.assigned_to] = []
            projects_by_user[project.assigned_to].append(project)
        
        # Get today's status updates
        today_statuses = {}
        if all_projects:
            project_names = [p.name for p in all_projects]
            status_entries = frappe.db.sql("""
                SELECT project, progress_status
                FROM `tabRTL Project Daily Status`
                WHERE project IN %(projects)s
                AND log_date = %(today)s
            """, {"projects": project_names, "today": today}, as_dict=True)
            
            for entry in status_entries:
                today_statuses[entry.project] = entry.progress_status
        
        # Process each user
        reminders_sent = 0
        for user_email, projects in projects_by_user.items():
            # Skip if user is on leave
            if user_email in users_on_leave:
                continue
            
            # Count projects without today's status update and total missed
            not_updated_count = 0
            not_started_count = 0
            total_missed_count = 0
            
            for project in projects:
                if project.status == "Not Started":
                    not_started_count += 1
                elif project.name not in today_statuses:
                    # In Process project without today's status
                    not_updated_count += 1
                
                # Add to total missed count (from the field)
                total_missed_count += project.get("missed_daily_status_count", 0)
            
            # Send reminder if there are projects that need updates
            if not_updated_count > 0:
                _send_daily_status_reminder(user_email, not_updated_count, not_started_count, total_missed_count)
                reminders_sent += 1
        
        if reminders_sent > 0:
            frappe.logger().info(f"Sent {reminders_sent} daily status reminder emails")
            
    except Exception as e:
        frappe.logger().error(f"Error in send_daily_status_reminders: {str(e)}")


def _is_today_holiday(today):
    """Check if today is a holiday based on RTL Project Settings"""
    try:
        settings = frappe.get_single("RTL Project Settings")
        
        # Check regular holiday day
        weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        today_weekday = weekday_names[today.weekday()]
        
        if settings.regular_holiday_day == today_weekday:
            return True
        
        # Check holiday list
        if settings.holiday_list:
            for holiday in settings.holiday_list:
                if getdate(holiday.holiday_date) == today:
                    return True
        
        return False
    except Exception as e:
        frappe.logger().error(f"Error checking holiday status: {str(e)}")
        return False


def _get_users_on_leave_today(today):
    """Get list of users on approved leave today"""
    users_on_leave = frappe.db.sql("""
        SELECT DISTINCT employee
        FROM `tabRTL Leaves`
        WHERE approved = 1
        AND %(today)s BETWEEN from_date AND to_date
    """, {"today": today}, pluck="employee")
    
    return set(users_on_leave or [])


def _send_daily_status_reminder(user_email, not_updated_count, not_started_count, total_missed_count=0):
    """Send individual daily status reminder email"""
    try:
        # Get user details
        user = frappe.get_doc("User", user_email)
        
        subject = f"📋 Daily RTL Project Status Update Required - {not_updated_count} Pending"
        
        # Build project status message
        status_parts = []
        if not_updated_count > 0:
            status_parts.append(f"• <strong style='color: #dc2626;'>{not_updated_count}</strong> project{'s' if not_updated_count != 1 else ''} need{'s' if not_updated_count == 1 else ''} today's status update")
        if not_started_count > 0:
            status_parts.append(f"• <strong>{not_started_count}</strong> project{'s' if not_started_count != 1 else ''} not yet started")
        if total_missed_count > 0:
            status_parts.append(f"• <strong style='color: #ef4444;'>{total_missed_count}</strong> total missed update{'s' if total_missed_count != 1 else ''} (cumulative)")
        
        status_summary = "\n".join(status_parts)
        
        message = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #f59e0b; border-bottom: 2px solid #f59e0b; padding-bottom: 10px;">
                📋 Daily Project Status Update Required
            </h2>
            
            <div style="background-color: #fef3c7; padding: 20px; border-left: 4px solid #f59e0b; margin: 20px 0;">
                <h3 style="color: #92400e; margin-top: 0;">⚠️ Action Required - Status Not Updated Today</h3>
                <p style="color: #78350f; font-size: 16px; margin: 10px 0;">
                    You have <strong>{not_updated_count}</strong> project{'s' if not_updated_count != 1 else ''} that need daily status updates for today.
                </p>
            </div>
            
            <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #1e293b; margin-top: 0;">Status Summary</h3>
                <div style="color: #475569; line-height: 1.8; font-size: 15px;">
                    {status_summary.replace(chr(10), '<br>')}
                </div>
            </div>
            
            {f'''<div style="background-color: #fee2e2; padding: 15px; border-left: 4px solid #dc2626; margin: 20px 0;">
                <h4 style="color: #991b1b; margin-top: 0;">📊 Total Missed Updates</h4>
                <p style="color: #7f1d1d; margin: 0; font-size: 15px;">
                    You have <strong>{total_missed_count}</strong> cumulative missed update{'s' if total_missed_count != 1 else ''} across all your projects. 
                    Please ensure daily updates are completed on time going forward.
                </p>
            </div>''' if total_missed_count > 0 else ''}
            
            <div style="margin-top: 30px; padding: 15px; background-color: #eff6ff; border-radius: 8px;">
                <p style="margin: 0; color: #1e40af; font-size: 15px;">
                    <strong>Next Steps:</strong> Please log in to the RTL Project Dashboard and update the daily status for all your assigned projects immediately.
                </p>
            </div>
            
            <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #e2e8f0; color: #64748b; font-size: 12px;">
                <p style="margin: 0;">This is an automated reminder from the RTL Project Management System.</p>
                <p style="margin: 5px 0 0 0;">Date: {formatdate(nowdate(), "dd MMM yyyy")} | Time: 7:30 PM</p>
            </div>
        </div>
        """
        
        frappe.sendmail(
            recipients=[user_email],
            subject=subject,
            message=message,
            delayed=False,
            reference_doctype="RTL Project",
        )
        
        frappe.logger().info(f"Daily status reminder sent to {user_email}: {not_updated_count} projects need update, {not_started_count} not started, {total_missed_count} total missed")
        
    except Exception as e:
        frappe.logger().error(f"Error sending daily status reminder to {user_email}: {str(e)}")


def get_rtl_settings():
    """Get RTL Project Settings"""
    try:
        return frappe.get_single("RTL Project Settings")
    except Exception as e:
        frappe.logger().error(f"Error getting RTL Project Settings: {str(e)}")
        return None


def is_holiday_today(today=None):
    """Check if today is a holiday (including regular holiday day)"""
    if not today:
        today = getdate(nowdate())
    return _is_today_holiday(today)


def is_assignee_on_leave(assignee_email, check_date=None):
    """Check if assignee has a leave on the given date"""
    if not check_date:
        check_date = getdate(nowdate())
    
    leave_exists = frappe.db.exists("RTL Leaves", {
        "employee": assignee_email,
        "from_date": ["<=", check_date],
        "to_date": [">=", check_date]
    })
    
    return bool(leave_exists)


def send_project_completion_email_to_hod(project_doc):
    """
    Send email to Department HOD when a project is completed.
    Called from RTL Project on_update hook when status changes to Completed.
    """
    try:
        # Find the department where the assignee is a member or HOD
        department = frappe.db.sql("""
            SELECT DISTINCT d.name, d.department_name, d.head_of_department
            FROM `tabRTL Department` d
            LEFT JOIN `tabRTL Department Member` dm ON dm.parent = d.name
            WHERE d.is_active = 1
            AND (d.head_of_department = %(assignee)s OR dm.user = %(assignee)s)
            LIMIT 1
        """, {"assignee": project_doc.assigned_to}, as_dict=True)
        
        if not department:
            frappe.logger().info(f"No department found for assignee {project_doc.assigned_to}")
            return
        
        hod_email = department[0].head_of_department
        
        # Don't send email if the assignee is the HOD themselves
        if hod_email == project_doc.assigned_to:
            return
        
        # Get user details
        assignee_user = frappe.get_doc("User", project_doc.assigned_to)
        assignee_name = assignee_user.full_name or project_doc.assigned_to
        
        subject = f"✅ Project Completed: {project_doc.project_name}"
        
        message = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #22c55e; border-bottom: 2px solid #22c55e; padding-bottom: 10px;">
                ✅ Project Completed
            </h2>
            
            <div style="background-color: #f0fdf4; padding: 20px; border-left: 4px solid #22c55e; margin: 20px 0;">
                <h3 style="color: #166534; margin-top: 0;">Good News!</h3>
                <p style="color: #14532d; font-size: 16px; margin: 10px 0;">
                    A project assigned to <strong>{assignee_name}</strong> has been successfully completed.
                </p>
            </div>
            
            <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #1e293b; margin-top: 0;">Project Details</h3>
                
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold; color: #475569; width: 40%;">Project Name:</td>
                        <td style="padding: 8px 0; color: #1e293b;">{project_doc.project_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold; color: #475569;">Assigned To:</td>
                        <td style="padding: 8px 0; color: #1e293b;">{assignee_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold; color: #475569;">Completed On:</td>
                        <td style="padding: 8px 0; color: #22c55e; font-weight: bold;">
                            {formatdate(project_doc.finish_date, "dd MMM yyyy")}
                        </td>
                    </tr>
                    {f'''<tr>
                        <td style="padding: 8px 0; font-weight: bold; color: #475569;">Start Date:</td>
                        <td style="padding: 8px 0; color: #1e293b;">{formatdate(project_doc.start_date, "dd MMM yyyy")}</td>
                    </tr>''' if project_doc.start_date else ''}
                    <tr>
                        <td style="padding: 8px 0; font-weight: bold; color: #475569;">End Date:</td>
                        <td style="padding: 8px 0; color: #1e293b;">{formatdate(project_doc.end_date, "dd MMM yyyy")}</td>
                    </tr>
                    {f'''<tr>
                        <td style="padding: 8px 0; font-weight: bold; color: #475569;">Missed Updates:</td>
                        <td style="padding: 8px 0; color: {"#dc2626" if project_doc.missed_daily_status_count > 0 else "#22c55e"}; font-weight: bold;">
                            {project_doc.missed_daily_status_count} day{"s" if project_doc.missed_daily_status_count != 1 else ""}
                        </td>
                    </tr>''' if hasattr(project_doc, 'missed_daily_status_count') else ''}
                </table>
            </div>
            
            {f'''<div style="background-color: #fff7ed; padding: 15px; border-left: 4px solid #f97316; margin: 20px 0;">
                <h4 style="color: #9a3412; margin-top: 0;">Description:</h4>
                <p style="color: #78350f; margin: 0; white-space: pre-wrap;">{project_doc.description}</p>
            </div>''' if project_doc.description else ''}
            
            <div style="margin-top: 30px; padding: 15px; background-color: #eff6ff; border-radius: 8px;">
                <p style="margin: 0; color: #1e40af;">
                    <strong>Department:</strong> {department[0].department_name}
                </p>
            </div>
            
            <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #e2e8f0; color: #64748b; font-size: 12px;">
                <p style="margin: 0;">This is an automated notification from the RTL Project Management System.</p>
            </div>
        </div>
        """
        
        frappe.sendmail(
            recipients=[hod_email],
            subject=subject,
            message=message,
            delayed=False,
            reference_doctype="RTL Project",
            reference_name=project_doc.name,
        )
        
        frappe.logger().info(f"Project completion email sent to HOD {hod_email} for project {project_doc.name}")
        
    except Exception as e:
        frappe.logger().error(f"Error sending project completion email for {project_doc.name}: {str(e)}")
