# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe
import json
from frappe import _
from hkm.hkm_pay.doctype.hkmp_entry.payment import update_user_balance


# Permission control - Only System Manager can access HKM Pay User Management
HKMP_USER_MANAGEMENT_ALLOWED_ROLES = [
    "System Manager",
    "Accounts User",
    "Accounts Admin",
    "Accounts Manager",
]

USER_UPDATE_ROLE = [
      "Accounts Admin",
       "System Manager",
]



@frappe.whitelist()
def get_companies(user=None):
    if user is None:
        user = frappe.session.user
    parent = frappe.db.get_value("HKMP User", {"user": user}, "name")
    if not parent:
        return []
    doc = frappe.get_all(
        "HKM Active Company",
        filters={"parenttype": "HKMP User", "parent": parent},
        fields=["company"],
    )
    return doc


@frappe.whitelist()
def get_all_companies():
    """Get all companies in the system"""
    try:
        companies = frappe.get_all(
            "HKM Active Company",
            filters={"parenttype": "HKM General Settings"},
            fields=["company as name"],
        )
        return {"status": "success", "data": companies}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error fetching companies")
        return {"status": "error", "message": str(e)}


def check_hkmp_user_management_permission(user_update = False):
    """Check if user has permission to access HKM Pay User Management"""
    user_roles = frappe.get_roles(frappe.session.user)
    has_access = any(role in HKMP_USER_MANAGEMENT_ALLOWED_ROLES for role in user_roles)

    

    if not has_access:
        frappe.throw(
            _(
                "You don't have permission to access HKM Pay User Management. Required roles: {0}"
            ).format(", ".join(HKMP_USER_MANAGEMENT_ALLOWED_ROLES)),
            frappe.PermissionError,
        )
    if user_update and  not any(role in USER_UPDATE_ROLE for role in user_roles):
        frappe.throw(
            _(
                "You don't have permission to create or edit: {0}"
            ).format(", ".join(HKMP_USER_MANAGEMENT_ALLOWED_ROLES)),
            frappe.PermissionError,
        )


@frappe.whitelist()
def get_all_hkmp_users():
    """Get all HKMP Users with spending data optimized using raw SQL"""
    check_hkmp_user_management_permission()
    try:
        # Single optimized query with LEFT JOINs to get users and spending in one go
        # Start and end of month calculated directly in SQL
        users = frappe.db.sql(
            """
            SELECT 
                hu.name,
                hu.user,
                hu.full_name,
                hu.department,
                hu.per_transaction_limit,
                hu.advance_limit,
                hu.available_amt,
                hu.daily_limit,
                hu.available_daily_limit,
                hu.enabled,
                hu.creation,
                hu.modified,
                hu.owner,
                hu.modified_by,
                COALESCE(SUM(CASE 
                    WHEN he.status = 'Success' 
                        AND DATE(he.creation) >= DATE_FORMAT(CURDATE(), '%Y-%m-01')
                        AND DATE(he.creation) <= LAST_DAY(CURDATE())
                    THEN he.amount 
                    ELSE 0 
                END), 0) as current_month_spending,
                COALESCE(SUM(CASE 
                    WHEN he.status = 'Success' 
                        AND DATE(he.creation) = CURDATE()
                    THEN he.amount 
                    ELSE 0 
                END), 0) as current_day_spending,
                COALESCE(SUM(CASE 
                    WHEN he.status = 'Success' 
                    THEN he.amount 
                    ELSE 0 
                END), 0) as total_spending
            FROM `tabHKMP User` hu
            LEFT JOIN `tabHKMP Entry` he ON he.user = hu.user
            GROUP BY hu.name, hu.user, hu.full_name, hu.department, 
                     hu.per_transaction_limit, hu.advance_limit, hu.available_amt,
                     hu.daily_limit, hu.available_daily_limit, hu.enabled, hu.creation, 
                     hu.modified, hu.owner, hu.modified_by
            ORDER BY  current_month_spending DESC, current_day_spending DESC, total_spending DESC
            """,
            as_dict=True,
        )

        return {"status": "success", "data": users}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Error fetching HKMP Users"))
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_hkmp_user(name):
    """Get single HKMP User"""
    check_hkmp_user_management_permission()
    try:
        user = frappe.get_doc("HKMP User", name)

        return {"status": "success", "data": user.as_dict()}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Error fetching HKMP User"))
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def create_hkmp_user():
    """Create new HKMP User"""

    data = json.loads(frappe.request.data)

    # frappe.log_error(title="data", message=data)

    check_hkmp_user_management_permission(user_update=True)

    # Create new document
    doc = frappe.get_doc({"doctype": "HKMP User", **data})

    role = frappe.get_doc("Role", "HKMP User")
    doc.append("roles", {"role": role.name})
    doc.insert()
    # frappe.db.commit()




    return {
        "status": "success",
        "data": doc.as_dict(),
        "message": _("HKMP User created successfully"),
    }


@frappe.whitelist()
def update_hkmp_user():
    """Update existing HKMP User"""
    check_hkmp_user_management_permission(user_update=True)
    try:
        import json

        data = json.loads(frappe.request.data)

        name = data.get("name")
        user_data = data.get("user_data")

        # Get existing document
        doc = frappe.get_doc("HKMP User", name)

        # Handle active_company child table separately
        if "active_company" in user_data:
            # Clear existing active_company entries
            doc.set("active_company", [])
            # Add new active_company entries
            for company_data in user_data.get("active_company", []):
                doc.append("active_company", company_data)
            # Remove active_company from user_data to avoid conflicts
            user_data = {k: v for k, v in user_data.items() if k != "active_company"}

        # Update other fields
        for field, value in user_data.items():
            if hasattr(doc, field):
                setattr(doc, field, value)

        doc.save()
        frappe.db.commit()  # v16: REVIEW - check if needed

        return {
            "status": "success",
            "data": doc.as_dict(),
            "message": _("HKMP User updated successfully"),
        }
    except Exception as e:
        frappe.throw(str(e))


@frappe.whitelist()
def delete_hkmp_user(name):
    """Delete HKMP User"""
    check_hkmp_user_management_permission()
    try:
        frappe.delete_doc("HKMP User", name)
        frappe.db.commit()  # v16: REVIEW - API endpoint

        return {"status": "success", "message": _("HKMP User deleted successfully")}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Error deleting HKMP User"))
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_system_users(search_term=None, limit=30):
    """Get system users for dropdown with search and pagination

    Args:
        search_term: Search by full_name or name (email)
        limit: Maximum number of users to return (default: 30)
    """
    check_hkmp_user_management_permission()
    try:
        # Ensure limit is an integer for security
        limit = int(limit) if limit else 30

        filters = {"enabled": 1, "user_type": "System User"}

        # If search term provided, add OR filters for name and full_name
        if search_term:
            users = frappe.db.sql(
                """
                SELECT name, full_name
                FROM `tabUser`
                WHERE enabled = 1
                    AND user_type = 'System User'
                    AND (
                        LOWER(full_name) LIKE %(search)s
                        OR LOWER(name) LIKE %(search)s
                    )
                ORDER BY full_name ASC
                LIMIT {limit}
            """.format(
                    limit=limit
                ),
                {"search": f"%{search_term.lower()}%"},
                as_dict=True,
            )
        else:
            # No search term - return first N users
            users = frappe.get_all(
                "User",
                filters=filters,
                fields=["name", "full_name"],
                order_by="full_name asc",
                limit=limit,
            )

        return {"status": "success", "data": users, "count": len(users)}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Error fetching System Users"))
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_departments():
    """Get all departments for dropdown"""
    check_hkmp_user_management_permission()
    try:
        departments_list = frappe.get_all(
            "Execution Department", fields=["name"], order_by="name asc"
        )

        return {"status": "success", "data": departments_list}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Error fetching Departments"))
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_user_entries(user=None, filters=None):
    """Get HKMP Entries for a specific user with optional filters.
    If user is None or empty, returns entries for all users based on filters.
    """
    check_hkmp_user_management_permission()
    try:
        import json

        if isinstance(filters, str):
            filters = json.loads(filters)

        if not filters:
            filters = {}

        # Only filter by user if provided
        if user:
            filters["user"] = user

        # Build WHERE conditions manually with proper parameterization
        conditions = []
        params = {}
        
        # Handle each filter
        for key, value in filters.items():
            if value is None or value == "":
                continue
                
            # Handle date range filters (>=, <=, between)
            if key == "creation" and isinstance(value, list):
                if value[0] == ">=":
                    conditions.append("he.creation >= %(from_date)s")
                    params["from_date"] = value[1] + " 00:00:00"
                elif value[0] == "<=":
                    conditions.append("he.creation <= %(to_date)s")
                    params["to_date"] = value[1] + " 23:59:59"
                elif value[0] == "between":
                    conditions.append("he.creation BETWEEN %(from_date)s AND %(to_date)s")
                    params["from_date"] = value[1][0] + " 00:00:00"
                    params["to_date"] = value[1][1] + " 23:59:59"
            # Handle list operators (in, not in, etc.)
            elif isinstance(value, list) and len(value) > 0:
                if value[0] == "in":
                    # Build IN clause with parameters
                    in_values = value[1] if len(value) > 1 else []
                    if in_values:
                        placeholders = []
                        for i, val in enumerate(in_values):
                            param_name = f"{key}_in_{i}"
                            placeholders.append(f"%({param_name})s")
                            params[param_name] = val
                        conditions.append(f"he.{key} IN ({', '.join(placeholders)})")
                elif value[0] in [">=", "<=", ">", "<", "!=", "="]:
                    conditions.append(f"he.{key} {value[0]} %({key})s")
                    params[key] = value[1]
            else:
                # Simple equality
                conditions.append(f"he.{key} = %({key})s")
                params[key] = value
        
        # Build WHERE clause
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # Build optimized SQL query with LEFT JOIN
        # This single query is more efficient than fetching entries and users separately
        query = """
            SELECT 
                he.name,
                he.user,
                he.status,
                he.transfer_type,
                he.amount,
                he.beneficiary_name,
                he.customer_ref_no as utr,
                he.remarks,
                he.bill_received,
                he.is_return,
                he.debited_from,
                he.company,
                he.bank_account,
                he.account_number,
                he.ifsc_code,
                he.upi_id,
                he.mobile_number,
                he.creation,
                he.modified,
                he.docstatus,
                COALESCE(hu.full_name, '') as user_full_name
            FROM `tabHKMP Entry` he
            LEFT JOIN `tabHKMP User` hu ON he.user = hu.user
            WHERE {where_clause}
            ORDER BY he.creation DESC
        """.format(where_clause=where_clause)
        
        # Execute the optimized query with LEFT JOIN
        entries = frappe.db.sql(query, params, as_dict=True)

        return {"status": "success", "data": entries}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Error fetching HKMP Entries"))
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def update_entry_status(entry_name, field, value):
    """Update bill_received or is_return status for an entry"""
    check_hkmp_user_management_permission()
    try:
        import json

        if isinstance(value, str):
            value = int(value)

        # Validate field name
        if field not in ["bill_received", "is_return"]:
            return {"status": "error", "message": "Invalid field name"}

        # Get and update the entry
        entry = frappe.get_doc("HKMP Entry", entry_name)

        # Set the field value and mark it as changed
        entry.set(field, value)

        entry.save(ignore_permissions=True)
        update_user_balance(entry.user)
        frappe.db.commit()  # v16: REVIEW - check if needed

        return {"status": "success", "message": f"Updated {field} successfully"}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Error updating entry status"))
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_user_analytics(user, from_date=None, to_date=None):
    """Get comprehensive analytics for a specific HKMP User"""
    check_hkmp_user_management_permission()
    try:
        from frappe.utils import getdate, now_datetime
        from collections import defaultdict
        import json

        # Build filters
        filters = {"user": user}

        if from_date:
            filters["creation"] = [">=", from_date]
        if to_date:
            if "creation" in filters:
                filters["creation"] = ["between", [from_date, to_date]]
            else:
                filters["creation"] = ["<=", to_date]

        # Get all entries for the user
        entries = frappe.get_all(
            "HKMP Entry",
            filters=filters,
            fields=[
                "name",
                "status",
                "transfer_type",
                "amount",
                "bill_received",
                "is_return",
                "creation",
                "docstatus",
            ],
            order_by="creation asc",
        )

        if not entries:
            return {
                "status": "success",
                "data": {
                    "total_transactions": 0,
                    "total_amount": 0,
                    "average_transaction": 0,
                    "success_rate": 0,
                    "status_breakdown": [],
                    "transfer_type_breakdown": [],
                    "transaction_trends": [],
                    "highest_transaction": 0,
                    "lowest_transaction": 0,
                    "bills_received": 0,
                    "bills_pending": 0,
                    "returns": 0,
                },
            }

        # Calculate summary statistics
        total_transactions = len(entries)
        total_amount = sum(entry.amount for entry in entries)
        average_transaction = (
            total_amount / total_transactions if total_transactions > 0 else 0
        )

        # Status breakdown
        status_counts = defaultdict(lambda: {"count": 0, "amount": 0})
        for entry in entries:
            status_counts[entry.status]["count"] += 1
            status_counts[entry.status]["amount"] += entry.amount

        status_breakdown = [
            {"status": status, "count": data["count"], "amount": data["amount"]}
            for status, data in status_counts.items()
        ]

        # Transfer type breakdown
        transfer_type_counts = defaultdict(lambda: {"count": 0, "amount": 0})
        for entry in entries:
            transfer_type_counts[entry.transfer_type]["count"] += 1
            transfer_type_counts[entry.transfer_type]["amount"] += entry.amount

        transfer_type_breakdown = [
            {"type": transfer_type, "count": data["count"], "amount": data["amount"]}
            for transfer_type, data in transfer_type_counts.items()
        ]

        # Transaction trends (daily aggregation)
        daily_trends = defaultdict(lambda: {"count": 0, "amount": 0})
        for entry in entries:
            date_key = getdate(entry.creation).strftime("%Y-%m-%d")
            daily_trends[date_key]["count"] += 1
            daily_trends[date_key]["amount"] += entry.amount

        transaction_trends = [
            {"date": date, "count": data["count"], "amount": data["amount"]}
            for date, data in sorted(daily_trends.items())
        ]

        # Calculate success rate
        success_count = sum(1 for entry in entries if entry.status == "Success")
        success_rate = (
            (success_count / total_transactions * 100) if total_transactions > 0 else 0
        )

        # Highest and lowest transactions
        amounts = [entry.amount for entry in entries]
        highest_transaction = max(amounts) if amounts else 0
        lowest_transaction = min(amounts) if amounts else 0

        # Bills and returns
        bills_received = sum(1 for entry in entries if entry.bill_received == 1)
        bills_pending = total_transactions - bills_received
        returns = sum(1 for entry in entries if entry.is_return == 1)

        # Most used payment method
        most_used_method = (
            max(transfer_type_counts.items(), key=lambda x: x[1]["count"])[0]
            if transfer_type_counts
            else None
        )

        # Pending amount
        pending_amount = sum(
            entry.amount
            for entry in entries
            if entry.status in ["Pending", "Processing"]
        )

        return {
            "status": "success",
            "data": {
                "total_transactions": total_transactions,
                "total_amount": total_amount,
                "average_transaction": average_transaction,
                "success_rate": success_rate,
                "status_breakdown": status_breakdown,
                "transfer_type_breakdown": transfer_type_breakdown,
                "transaction_trends": transaction_trends,
                "highest_transaction": highest_transaction,
                "lowest_transaction": lowest_transaction,
                "bills_received": bills_received,
                "bills_pending": bills_pending,
                "returns": returns,
                "most_used_method": most_used_method,
                "pending_amount": pending_amount,
                "success_count": success_count,
                "failed_count": sum(1 for entry in entries if entry.status == "Failed"),
            },
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Error fetching user analytics"))
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_total_spend_bank_account_wise():
    check_hkmp_user_management_permission()

    result = frappe.db.sql(
        """
        SELECT
            debited_from,
            company,
             COALESCE(SUM(CASE 
                    WHEN DATE(creation) >= DATE_FORMAT(CURDATE(), '%Y-%m-01')
                        AND DATE(creation) <= LAST_DAY(CURDATE())
                    THEN amount 
                    ELSE 0 
                END), 0) as current_month_spending,
                COALESCE(SUM(amount), 0) as total_spending ,
                COALESCE(SUM(CASE 
                    WHEN DATE(creation) >= DATE_FORMAT(CURDATE(), '%Y-%m-01')
                        AND DATE(creation) <= LAST_DAY(CURDATE())
                    THEN amount 
                    ELSE 0 
                END), 0) / NULLIF(DAY(CURDATE()), 0) as average_daily_spending
        FROM `tabHKMP Entry`
        WHERE
            status = 'Success'
        GROUP BY
            debited_from, company 
        """,
        as_dict=True,
    )

    return {"status": "success", "data": result}
