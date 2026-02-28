import frappe
from frappe.model.document import Document
from frappe.utils import getdate, nowdate


class RTLProject(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        assigned_to: DF.Link
        description: DF.SmallText | None
        end_date: DF.Date
        finish_date: DF.Date | None
        missed_daily_status_count: DF.Int
        project_name: DF.Data
        start_date: DF.Date | None
        status: DF.Literal["Not Started", "In Process", "Completed"]
    # end: auto-generated types
    def validate(self):
        self._ensure_end_date_not_past_start()
        self._enforce_user_permissions()
        self._ensure_assignee_exists()

    def before_save(self):
        self._set_start_date_if_needed()
        self._set_finish_dates()

    def after_insert(self):
        """Send email notification after project creation"""
        from hkm.erpnext___custom.doctype.rtl_project.rtl_email_notifications import send_project_creation_email
        send_project_creation_email(self)
    
    def on_update(self):
        """Send email notification to HOD when project is completed"""
        previous_status = self.get_db_value("status") if not self.is_new() else None
        if self.status == "Completed" and previous_status != "Completed":
            from hkm.erpnext___custom.doctype.rtl_project.rtl_email_notifications import send_project_completion_email_to_hod
            send_project_completion_email_to_hod(self)
    
    def on_trash(self):
        """Delete all related RTL Project Daily Status records when project is deleted"""
        # Get all daily status records for this project
        daily_status_records = frappe.get_all(
            "RTL Project Daily Status",
            filters={"project": self.name},
            pluck="name"
        )
        
        # Delete each daily status record
        for status_name in daily_status_records:
            frappe.delete_doc("RTL Project Daily Status", status_name, force=True)
        
        if daily_status_records:
            frappe.logger().info(f"Deleted {len(daily_status_records)} daily status records for project {self.name}")

    def _ensure_assignee_exists(self):
        if not self.assigned_to:
            frappe.throw("Assigned To is required.")
        user_exists = frappe.db.exists(
            "User",
            {
                "name": self.assigned_to,
                "user_type": "System User",
                "enabled": 1,
            },
        )
        if not user_exists:
            frappe.throw("Assigned To must be an active System User.")

    def _ensure_end_date_not_past_start(self):
        if self.start_date and self.end_date and getdate(self.end_date) < getdate(self.start_date):
            frappe.throw("End Date cannot be earlier than Start Date.")

    def _set_start_date_if_needed(self):
        previous_status = self.get_db_value("status") if not self.is_new() else None
        if self.status == "In Process" and not self.start_date:
            self.start_date = nowdate()
        if previous_status == "In Process" and self.status == "Not Started":
            # allow admin to reset; they can clear start date manually if desired
            pass

    def _set_finish_dates(self):
        previous_status = self.get_db_value("status") if not self.is_new() else None
        if self.status == "Completed" and previous_status != "Completed":
            user = frappe.session.user
            is_admin = user == "Administrator" or "RTL Admin" in frappe.get_roles(user)
            if self.assigned_to != user and not is_admin:
                frappe.throw("Only the assigned user or RTL Admin can complete the project.")
            self.finish_date = nowdate()
        elif previous_status == "Completed" and self.status != "Completed":
            # clearing completion dates when reopening
            self.finish_date = None

    def _enforce_user_permissions(self):
        user = frappe.session.user
        if user == "Guest":
            frappe.throw("You need to log in to access this project.")
        is_admin = user == "Administrator" or "RTL Admin" in frappe.get_roles(user)
        if is_admin:
            return

        # Check if user is HOD and has access to this project's assignee
        from hkm.erpnext___custom.utils.rtl_permissions import can_create_project_for_user
        
        if self.is_new():
            # For new projects, check if user can create for this assignee
            if not can_create_project_for_user(user, self.assigned_to):
                frappe.throw("You are not permitted to create projects for this user.")
            return  # HOD can create, so skip further checks
        
        # For existing projects, check if user is assignee OR HOD with access
        is_hod_with_access = False
        if user != self.assigned_to:
            # Check if user is HOD who can manage this assignee's projects
            if not can_create_project_for_user(user, self.assigned_to):
                frappe.throw("You are not permitted to access this project.")
            else:
                is_hod_with_access = True

        # Check if non-allowed fields were changed (only for regular users, not HODs/Admins)
        if not self.is_new() and not is_hod_with_access:
            # Only restrict field changes for regular users (assignees)
            # HODs and Admins can edit all fields
            if user == self.assigned_to:
                # Fields that regular users are allowed to change
                allowed_fields = {"status", "start_date", "finish_date"}
                # User-editable fields to check
                user_fields = {"project_name", "description", "assigned_to", "end_date"}
                
                # Check if any user-editable field (except allowed ones) was changed
                changed_restricted_fields = []
                for field in user_fields:
                    if field not in allowed_fields:
                        old_value = self.get_db_value(field)
                        new_value = self.get(field)
                        if old_value != new_value:
                            changed_restricted_fields.append(field)
                
                if changed_restricted_fields:
                    frappe.throw(
                        f"You are only allowed to update Status. Cannot modify: {', '.join(changed_restricted_fields)}"
                    )

        # Only allow HODs/Admins to reset to "Not Started"
        if self.status == "Not Started" and self.get_db_value("status") != "Not Started":
            if not is_hod_with_access:
                frappe.throw("You cannot reset the project to Not Started.")

        # allow transition to in process; start date auto-set in before_save
        if self.status == "In Process" and self.get_db_value("status") == "Not Started":
            return

    def check_and_increment_missed_count_for_today(self):
        """
        Check if today's status was updated. If not, increment the missed count by 1.
        This is called daily at midnight to efficiently track missed updates.
        
        Only increments if:
        - Project is "In Process"
        - Today is not a holiday
        - Assignee is not on approved leave
        - No daily status update exists for today
        """
        if self.status != "In Process" or not self.start_date:
            return False

        from hkm.erpnext___custom.doctype.rtl_project.rtl_email_notifications import (
            is_holiday_today, is_assignee_on_leave
        )
        from frappe.utils import getdate, nowdate

        today = getdate(nowdate())

        # Skip if today is a holiday
        if is_holiday_today(today):
            return False

        # Skip if assignee is on approved leave
        if is_assignee_on_leave(self.assigned_to, today):
            return False

        # Check if daily status was updated for today
        status_exists = frappe.db.exists("RTL Project Daily Status", {
            "project": self.name,
            "log_date": today
        })

        # If status does NOT exist for today, increment the missed count
        if not status_exists:
            new_count = self.missed_daily_status_count + 1
            self.db_set("missed_daily_status_count", new_count)
            return True

        return False
@frappe.whitelist()
def reopen_project(project_name: str):
    doc = frappe.get_doc("RTL Project", project_name)
    frappe.only_for("RTL Admin")
    doc.db_set(
        {
            "status": "In Process",
            "finish_date": None,
        }
    )
    return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def update_all_missed_daily_status_counts():
    """
    Daily midnight task: Check all in-process projects and increment missed count if today's status not updated.
    This is efficient - only checks today, doesn't recalculate entire history.
    """
    projects = frappe.get_all("RTL Project",
        filters={"status": "In Process"},
        fields=["name", "assigned_to", "missed_daily_status_count"]
    )

    updated_count = 0
    for project_data in projects:
        try:
            project = frappe.get_doc("RTL Project", project_data.name)
            if project.check_and_increment_missed_count_for_today():
                updated_count += 1
                frappe.logger().info(f"Incremented missed count for {project_data.name} to {project_data.missed_daily_status_count + 1}")
        except Exception as e:
            frappe.logger().error(f"Error checking missed count for project {project_data.name}: {str(e)}")

    frappe.logger().info(f"Daily midnight check: Incremented missed count for {updated_count} projects")
    return {"projects_incremented": updated_count, "total_projects_checked": len(projects)}
