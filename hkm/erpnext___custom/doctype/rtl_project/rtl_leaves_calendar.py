"""
RTL Leaves Calendar API - Get leaves and holidays for next 30 days
"""

import frappe
from frappe.utils import getdate, nowdate, add_days
from datetime import datetime, timedelta


@frappe.whitelist()
def get_leaves_and_holidays_calendar(user=None, days=30):
    """
    Get all leaves and holidays for the next N days for the current user or specified user.
    Returns a list of dates with leaves/holidays (only dates with events, not all dates).
    """
    if not user:
        user = frappe.session.user
    
    # Convert days to integer if it's a string
    days = int(days) if isinstance(days, str) else days
    
    today = getdate(nowdate())
    end_date = add_days(today, days)
    
    events_list = []
    
    # Get all leaves for this user in the date range
    leaves = frappe.get_all("RTL Leaves",
        filters={
            "employee": user,
            "from_date": ["<=", end_date],
            "to_date": [">=", today]
        },
        fields=["name", "from_date", "to_date", "reason"]
    )
    
    # Add leaves to events list
    for leave in leaves:
        current_date = getdate(leave.from_date)
        while current_date <= getdate(leave.to_date):
            events_list.append({
                "date": current_date.isoformat(),
                "date_formatted": current_date.strftime("%d %b %Y"),
                "type": "leave",
                "description": f"Leave - {leave.reason}" if leave.reason else "Leave",
                "leave_id": leave.name
            })
            current_date = add_days(current_date, 1)
    
    # Get holidays from RTL Project Settings
    try:
        settings = frappe.get_single("RTL Project Settings")
        
        # Add configured holidays
        if settings.holiday_list:
            for holiday in settings.holiday_list:
                holiday_date = getdate(holiday.holiday_date)
                if today <= holiday_date <= end_date:
                    events_list.append({
                        "date": holiday_date.isoformat(),
                        "date_formatted": holiday_date.strftime("%d %b %Y"),
                        "type": "holiday",
                        "description": f"Holiday - {holiday.description}" if holiday.description else "Holiday"
                    })
        
        # Add regular holiday day (e.g., Sunday)
        if settings.regular_holiday_day:
            weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            holiday_weekday = weekday_names.index(settings.regular_holiday_day)
            
            current_date = today
            while current_date <= end_date:
                if current_date.weekday() == holiday_weekday:
                    events_list.append({
                        "date": current_date.isoformat(),
                        "date_formatted": current_date.strftime("%d %b %Y"),
                        "type": "regular_holiday",
                        "description": f"{settings.regular_holiday_day} (Weekly Holiday)"
                    })
                current_date = add_days(current_date, 1)
    except:
        pass
    
    # Remove duplicates and sort by date
    seen_dates = set()
    unique_events = []
    for event in sorted(events_list, key=lambda x: x["date"]):
        key = (event["date"], event["type"], event["description"])
        if key not in seen_dates:
            seen_dates.add(key)
            unique_events.append(event)
    
    return {
        "events": unique_events,
        "user": user,
        "start_date": today.isoformat(),
        "end_date": end_date.isoformat(),
        "total_days": days,
        "total_events": len(unique_events)
    }


@frappe.whitelist()
def create_leave(from_date, to_date, reason=None, user=None):
    """
    Create a new leave for the current user or specified user.
    Auto-saves the leave record.
    """
    if not user:
        user = frappe.session.user

    try:
        # Validate dates
        if getdate(to_date) < getdate(from_date):
            return {
                "success": False,
                "message": "To Date cannot be earlier than From Date"
            }

        # Check for overlapping leaves
        overlapping_leaves = frappe.db.sql("""
            SELECT name, from_date, to_date
            FROM `tabRTL Leaves`
            WHERE employee = %s
            AND (
                (from_date BETWEEN %s AND %s) OR
                (to_date BETWEEN %s AND %s) OR
                (%s BETWEEN from_date AND to_date) OR
                (%s BETWEEN from_date AND to_date)
            )
        """, (user, from_date, to_date, from_date, to_date, from_date, to_date))

        if overlapping_leaves:
            return {
                "success": False,
                "message": f"There are overlapping leaves for this employee: {overlapping_leaves[0][0]}"
            }

        # Create new leave document
        leave = frappe.get_doc({
            "doctype": "RTL Leaves",
            "employee": user,
            "from_date": from_date,
            "to_date": to_date,
            "reason": reason or ""
        })

        leave.insert()
        frappe.db.commit()  # v16: REVIEW - check if needed

        return {
            "success": True,
            "leave_id": leave.name,
            "message": f"Leave created successfully from {from_date} to {to_date}"
        }
    except Exception as e:
        frappe.log_error(f"Error creating leave for {user}: {str(e)}", "RTL Leave Create Error")
        return {
            "success": False,
            "message": f"Error creating leave: {str(e)}"
        }


@frappe.whitelist()
def update_leave(leave_id, from_date, to_date, reason=None):
    """
    Update an existing leave record.
    Only the assignee can update their own future leaves.
    """
    try:
        leave_doc = frappe.get_doc("RTL Leaves", leave_id)

        # Check if user owns this leave
        if leave_doc.employee != frappe.session.user:
            return {
                "success": False,
                "message": "You can only edit your own leaves"
            }

        # Check if leave is in the future (not passed)
        today = getdate(nowdate())
        if getdate(leave_doc.from_date) < today:
            return {
                "success": False,
                "message": "You can only edit future leaves"
            }

        # Validate dates
        if getdate(to_date) < getdate(from_date):
            return {
                "success": False,
                "message": "To Date cannot be earlier than From Date"
            }

        # Check for overlapping leaves
        overlapping_leaves = frappe.db.sql("""
            SELECT name, from_date, to_date
            FROM `tabRTL Leaves`
            WHERE employee = %s
            AND name != %s
            AND (
                (from_date BETWEEN %s AND %s) OR
                (to_date BETWEEN %s AND %s) OR
                (%s BETWEEN from_date AND to_date) OR
                (%s BETWEEN from_date AND to_date)
            )
        """, (leave_doc.employee, leave_id, from_date, to_date,
              from_date, to_date, from_date, to_date))

        if overlapping_leaves:
            return {
                "success": False,
                "message": f"There are overlapping leaves for this employee: {overlapping_leaves[0][0]}"
            }

        # Update the leave
        leave_doc.from_date = from_date
        leave_doc.to_date = to_date
        leave_doc.reason = reason or ""
        leave_doc.save()
        frappe.db.commit()  # v16: REVIEW - check if needed

        return {
            "success": True,
            "leave_id": leave_doc.name,
            "message": f"Leave updated successfully from {from_date} to {to_date}"
        }
    except Exception as e:
        frappe.log_error(f"Error updating leave {leave_id}: {str(e)}", "RTL Leave Update Error")
        return {
            "success": False,
            "message": f"Error updating leave: {str(e)}"
        }


@frappe.whitelist()
def delete_leave(leave_id):
    """
    Delete a leave record.
    Only the assignee can delete their own future leaves.
    """
    try:
        leave_doc = frappe.get_doc("RTL Leaves", leave_id)
        
        # Check if user owns this leave
        if leave_doc.employee != frappe.session.user:
            return {
                "success": False,
                "message": "You can only delete your own leaves"
            }
        
        # Check if leave is in the future (not passed)
        today = getdate(nowdate())
        if getdate(leave_doc.from_date) < today:
            return {
                "success": False,
                "message": "You can only delete future leaves"
            }
        
        # Delete with ignore_permissions since we've already checked ownership
        frappe.delete_doc("RTL Leaves", leave_id, ignore_permissions=True)
        frappe.db.commit()  # v16: REVIEW - check if needed
        return {
            "success": True,
            "message": f"Leave {leave_id} deleted successfully"
        }
    except Exception as e:
        frappe.log_error(f"Error deleting leave {leave_id}: {str(e)}", "RTL Leave Delete Error")
        return {
            "success": False,
            "message": f"Error deleting leave: {str(e)}"
        }
