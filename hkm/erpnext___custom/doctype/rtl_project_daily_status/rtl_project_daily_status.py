import frappe
from frappe.model.document import Document
from frappe.utils import nowdate


class RTLProjectDailyStatus(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        log_date: DF.Date
        naming_series: DF.Literal["RTLD-.YYYY.-"]
        progress_status: DF.Literal["On Track", "Delayed 3-7 Days", "Delayed 8-15 Days", "Delayed >15 Days (Need Help)"]
        project: DF.Link
        remarks: DF.SmallText | None
    # end: auto-generated types
    def validate(self):
        self._enforce_permissions()
        self._ensure_project_in_process()
        self._ensure_single_entry_per_day()

    def before_insert(self):
        if not self.log_date:
            self.log_date = nowdate()

    def _enforce_permissions(self):
        user = frappe.session.user
        is_admin = user == "Administrator" or "RTL Admin" in frappe.get_roles(user)
        if user == "Guest" or is_admin:
            return

        project = frappe.db.get_value("RTL Project", self.project, ["assigned_to"], as_dict=True)
        if not project:
            frappe.throw("Selected project does not exist.")
        if project.assigned_to != user:
            frappe.throw("You can only log status for your own projects.")

    def _ensure_project_in_process(self):
        status = frappe.db.get_value("RTL Project", self.project, "status")
        if status != "In Process":
            frappe.throw("Daily status can only be added when project is In Process.")
    def _ensure_single_entry_per_day(self):
        if not self.log_date:
            return
        filters = {
            "project": self.project,
            "log_date": self.log_date,
        }
        if self.name:
            filters["name"] = ["!=", self.name]
        exists = frappe.db.exists("RTL Project Daily Status", filters)
        if exists:
            frappe.throw("A status entry already exists for this project on the selected date.")
