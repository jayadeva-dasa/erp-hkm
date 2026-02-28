import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, add_days, get_first_day, get_last_day, add_months, getdate, now_datetime
from datetime import datetime


class RTLProjectSchedule(Document):
    def validate(self):
        """Validate schedule configuration"""
        if not self.first_run_date:
            frappe.throw("First Run Date is required")

        first_run = getdate(self.first_run_date)

        # Validate start_day for monthly/quarterly schedules
        if self.frequency in ["Monthly", "Quarterly"]:
            if not self.start_day or self.start_day < 1 or self.start_day > 28:
                frappe.throw("Day of Month must be between 1 and 28")

        # Validate duration
        if not self.duration_days or self.duration_days < 1:
            frappe.throw("Duration must be at least 1 day")

        # Ensure next creation date reflects the first run while schedule hasn't executed yet
        if not self.last_run_date:
            self.next_creation_date = self.first_run_date
        elif not self.next_creation_date:
            # Fallback in case next_creation_date was cleared manually
            last_run = getdate(self.last_run_date)
            self.next_creation_date = self.calculate_next_date(last_run)
    
    def calculate_next_date(self, from_date=None):
        """Calculate the next project creation date based on frequency"""
        if not from_date:
            from_date = getdate(nowdate())
        
        if self.frequency == "Daily":
            return add_days(from_date, 1)
        
        elif self.frequency == "Weekly":
            return add_days(from_date, 7)
        
        elif self.frequency == "Monthly":
            # Get next month's specified day
            next_month = add_months(from_date, 1)
            first_day = get_first_day(next_month)
            target_date = add_days(first_day, self.start_day - 1)
            return target_date
        
        elif self.frequency == "Quarterly":
            # Get next quarter's specified day
            next_quarter = add_months(from_date, 3)
            first_day = get_first_day(next_quarter)
            target_date = add_days(first_day, self.start_day - 1)
            return target_date
        
        return from_date
    
    def create_project(self):
        """Create a new RTL Project from this schedule"""
        if not self.is_active:
            return None
        
        # Generate project name from template
        project_name = self.generate_project_name()
        
        # Calculate dates
        start_date = getdate(nowdate())
        end_date = add_days(start_date, self.duration_days)
        
        # Create the project
        project = frappe.get_doc({
            "doctype": "RTL Project",
            "project_name": project_name,
            "description": self.description or "",
            "assigned_to": self.assigned_to,
            "start_date": start_date,
            "end_date": end_date,
            "status": "Not Started",
            "created_from_schedule": self.name
        })
        project.insert(ignore_permissions=True)
        
        # Update schedule
        self.last_created_project = project.name
        self.last_run_date = now_datetime()
        self.next_creation_date = self.calculate_next_date(start_date)
        self.save(ignore_permissions=True)
        
        return project
    
    def generate_project_name(self):
        """Generate project name from template with placeholders"""
        today = datetime.now()
        
        name = self.project_template
        name = name.replace("{month}", today.strftime("%B"))
        name = name.replace("{year}", str(today.year))
        name = name.replace("{date}", today.strftime("%Y-%m-%d"))
        name = name.replace("{day}", str(today.day))
        
        return name


def run_scheduled_projects():
    """Scheduled task to create projects from active schedules"""
    today = getdate(nowdate())
    
    # Get all active schedules where next_creation_date is today or earlier
    schedules = frappe.get_all(
        "RTL Project Schedule",
        filters={
            "is_active": 1,
            "next_creation_date": ["<=", today]
        },
        pluck="name"
    )
    
    created_count = 0
    for schedule_name in schedules:
        try:
            schedule = frappe.get_doc("RTL Project Schedule", schedule_name)
            project = schedule.create_project()
            if project:
                created_count += 1
                frappe.logger().info(f"Created project {project.name} from schedule {schedule_name}")
        except Exception as e:
            frappe.logger().error(f"Error creating project from schedule {schedule_name}: {str(e)}")
            continue
    
    if created_count > 0:
        frappe.db.commit()  # v16: REVIEW - check if needed
        frappe.logger().info(f"Created {created_count} scheduled projects")
