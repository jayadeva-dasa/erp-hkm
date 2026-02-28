# Copyright (c) 2025, HKM Jaipur
# Backend APIs for Eagle View Report in HKM Dashboard

import frappe
from frappe import _
from frappe.utils import (
    data,
    cstr,
    getdate,
    add_days,
    get_first_day,
    get_last_day,
    add_to_date,
)
from typing import List, Dict, Optional, Tuple, Any
import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


# ==================== CONSTANTS ====================

DIMENSION_VIEW = "Dimension View"
ACCOUNT_VIEW = "Account View"
VOUCHER_VIEW = "Voucher View"
MULTI_DIMENSION_VIEW = "Multi Dimension View"

CUMULATIVE = "Cumulative"
DAY_WISE = "Day Wise"
WEEK_WISE = "Week Wise"
MONTH_WISE = "Month Wise"
QUARTER_WISE = "Quarter Wise"

SUMMARY = "Both Income and Expenses"
ONLY_INCOME = "Only Incomes"
ONLY_EXPENSE = "Only Expense"
NET_PROFIT = "Net Profit"
DETAILED_INCOME = "Detailed Income"
DETAILED_EXPENSE = "Detailed Expense"

ALL_ACCESS_ROLE = [
    "Accounts Manager",
    "Accounts User",
    "Accounts Admin",
    "System Manager",
]


# ==================== HELPER FUNCTIONS ====================


def has_all_access():
    """Check if current user has all access roles"""
    user_roles = frappe.get_roles(frappe.session.user)
    return any(role in ALL_ACCESS_ROLE for role in user_roles)


def get_cost_head_values():
    """Get Cost Heads accessible to current user"""
    user = frappe.session.user
    cost_heads = frappe.db.sql_list(
        """
        SELECT ch.name
        FROM `tabCost Head` ch
        JOIN `tabCost Head Concerned Person` c ON ch.name = c.parent
        WHERE c.user = %s AND ch.disabled = 0
        """,
        (user,),
    )

    if not cost_heads:
        return []

    dimension_meta = frappe.get_meta("Cost Head")
    all_heads = []

    for c in cost_heads:
        all_heads.extend(get_descendants_list(dimension_meta.name, c))

    return list(set(all_heads))


def get_descendants_list(doctype, name):
    """Get all descendants of a node in a tree"""
    if not frappe.db.exists(doctype, name):
        return [name]

    lft, rgt = frappe.db.get_value(doctype, name, ["lft", "rgt"])

    # Build filters - only add disabled/enabled filter if field exists
    filters = {"lft": [">", lft], "rgt": ["<", rgt]}

    # Check if disabled/enabled field exists before adding to filter
    dimension_meta = frappe.get_meta(doctype)
    if dimension_meta.has_field("disabled"):
        filters["disabled"] = 0
    elif dimension_meta.has_field("enabled"):
        filters["enabled"] = 1

    descendants = frappe.get_list(
        doctype,
        filters=filters,
        pluck="name",
    )

    descendants.append(name)
    return descendants


def expand_dimension_values(dimension, values):
    """Expand dimension values to include all descendants (for tree dimensions)"""
    if not values:
        return []

    dimension_meta = frappe.get_meta(dimension)
    all_values = []

    for val in values:
        if val == "Not Tagged":
            all_values.append(val)
            continue

        if dimension_meta.is_tree:
            # Expand to include all descendants
            all_values.extend(get_descendants_list(dimension, val))
        else:
            all_values.append(val)

    return list(set(all_values))


def get_period_buckets(from_date, to_date, time_period):
    """Generate period buckets based on time_period"""
    from_date = getdate(from_date)
    to_date = getdate(to_date)
    buckets = []

    if time_period == DAY_WISE:
        current = from_date
        while current <= to_date:
            buckets.append(
                {
                    "key": current.strftime("%Y-%m-%d"),
                    "label": current.strftime("%d %b %Y"),
                    "from_date": current,
                    "to_date": current,
                }
            )
            current = add_days(current, 1)

    elif time_period == WEEK_WISE:
        current = from_date
        while current <= to_date:
            week_end = add_days(current, 6)
            if week_end > to_date:
                week_end = to_date
            buckets.append(
                {
                    "key": f"{current.strftime('%Y-%m-%d')}_to_{week_end.strftime('%Y-%m-%d')}",
                    "label": f"{current.strftime('%d %b')} - {week_end.strftime('%d %b %Y')}",
                    "from_date": current,
                    "to_date": week_end,
                }
            )
            current = add_days(week_end, 1)

    elif time_period == MONTH_WISE:
        current = from_date
        while current <= to_date:
            month_end = get_last_day(current)
            if month_end > to_date:
                month_end = to_date
            buckets.append(
                {
                    "key": current.strftime("%Y-%m"),
                    "label": current.strftime("%b %Y"),
                    "from_date": current if current >= from_date else from_date,
                    "to_date": month_end,
                }
            )
            # Move to first day of next month
            current = add_to_date(month_end, days=1)

    elif time_period == QUARTER_WISE:
        current = from_date
        while current <= to_date:
            quarter = ((current.month - 1) // 3) + 1
            quarter_start = datetime(current.year, (quarter - 1) * 3 + 1, 1).date()
            quarter_end = quarter_start + relativedelta(months=3, days=-1)

            # Adjust to filter range
            bucket_start = max(quarter_start, from_date)
            bucket_end = min(quarter_end, to_date)

            buckets.append(
                {
                    "key": f"{current.year}-Q{quarter}",
                    "label": f"Q{quarter} {current.year}",
                    "from_date": bucket_start,
                    "to_date": bucket_end,
                }
            )

            # Move to next quarter
            current = add_to_date(quarter_end, days=1)

    return buckets


def get_heads_data(dimension, dimension_values, include_disabled=False):
    """Get heads data for dimension"""
    dimension_meta = frappe.get_meta(dimension)
    disabled_filter = {}

    if not include_disabled:
        if dimension_meta.has_field("disabled"):
            disabled_filter = {"disabled": 0}
        elif dimension_meta.has_field("enabled"):
            disabled_filter = {"enabled": 1}

    # If no specific values selected, get all
    if not dimension_values:
        if not has_all_access() and dimension == "Cost Head":
            allowed_heads = get_cost_head_values()
            if not allowed_heads:
                frappe.throw(
                    _(
                        "You are not authorized to view any Cost Head. Please set value in Cost Head Concerned Person."
                    )
                )
            disabled_filter["name"] = ["in", allowed_heads]

        if dimension_meta.is_tree:
            heads = frappe.get_all(
                dimension,
                filters=disabled_filter,
                fields=[
                    "name",
                    f"parent_{frappe.scrub(dimension)}",
                    "lft",
                    "rgt",
                    "is_group",
                ],
                order_by="lft",
            )
        else:
            heads = frappe.get_all(dimension, filters=disabled_filter, fields=["name"])
    else:
        # Get selected values and their descendants
        all_values = []
        for val in dimension_values:
            if dimension_meta.is_tree:
                all_values.extend(get_descendants_list(dimension, val))
            else:
                all_values.append(val)

        all_values = list(set(all_values))

        # Verify user is authorized for selected heads (if Cost Head)
        if not has_all_access() and dimension == "Cost Head":
            allowed_heads = get_cost_head_values()
            if not allowed_heads:
                frappe.throw(
                    _(
                        "You are not authorized to view any Cost Head. Please set value in Cost Head Concerned Person."
                    )
                )
            # Check if any selected head is not in allowed heads
            unauthorized_heads = [
                h for h in all_values if h != "Not Tagged" and h not in allowed_heads
            ]
            if unauthorized_heads:
                frappe.throw(
                    _(
                        "You are not authorized to view the selected Cost Head(s): {0}"
                    ).format(", ".join(unauthorized_heads))
                )

        disabled_filter["name"] = ["in", all_values]

        if dimension_meta.is_tree:
            heads = frappe.get_all(
                dimension,
                filters=disabled_filter,
                fields=[
                    "name",
                    f"parent_{frappe.scrub(dimension)}",
                    "lft",
                    "rgt",
                    "is_group",
                ],
                order_by="lft",
            )
        else:
            heads = frappe.get_all(dimension, filters=disabled_filter, fields=["name"])

    # Convert to dictionary for easy access
    heads_dict = {}
    
    # If include_disabled is True, fetch disabled/enabled status for all heads
    disabled_status_map = {}
    if include_disabled:
        head_names = [h.name for h in heads]
        if head_names:
            if dimension_meta.has_field("disabled"):
                disabled_records = frappe.get_all(
                    dimension,
                    filters={"name": ["in", head_names]},
                    fields=["name", "disabled"]
                )
                disabled_status_map = {r.name: r.disabled for r in disabled_records}
            elif dimension_meta.has_field("enabled"):
                enabled_records = frappe.get_all(
                    dimension,
                    filters={"name": ["in", head_names]},
                    fields=["name", "enabled"]
                )
                # enabled=0 means disabled, enabled=1 means enabled
                disabled_status_map = {r.name: 0 if r.enabled else 1 for r in enabled_records}
    
    for head in heads:
        head_data = {"name": head.name}
        
        # Add disabled status if include_disabled is True
        if include_disabled:
            is_disabled = disabled_status_map.get(head.name, 0)
            head_data["disabled"] = is_disabled
        
        if dimension_meta.is_tree:
            head_data.update(
                {
                    f"parent_{frappe.scrub(dimension)}": head.get(
                        f"parent_{frappe.scrub(dimension)}"
                    ),
                    "lft": head.get("lft", 0),
                    "rgt": head.get("rgt", 0),
                    "is_group": head.get("is_group", 0),
                    "indent": 0,  # Will be calculated later
                }
            )
        heads_dict[head.name] = head_data

    # Calculate indent levels based on tree hierarchy
    if dimension_meta.is_tree:
        for head_name in heads_dict.keys():
            if head_name == "Not Tagged":
                continue

            indent = 0
            current = head_name
            parent_field = f"parent_{frappe.scrub(dimension)}"

            # Count parents to determine indent level
            while current in heads_dict:
                parent = heads_dict[current].get(parent_field)
                if parent and parent in heads_dict:
                    indent += 1
                    current = parent
                else:
                    break

            heads_dict[head_name]["indent"] = indent

    # Note: "Not Tagged" will be added later during data processing if needed

    return heads_dict


# ==================== API ENDPOINTS ====================


@frappe.whitelist()
def get_accounting_dimensions():
    """Get all accounting dimensions"""
    try:
        dimensions = frappe.get_all(
            "Accounting Dimension",
            fields=["label", "document_type", "fieldname"],
            limit=100,
        )

        base_dimensions = ["Cost Head", "Cost Center", "Project"]
        result = []

        for dim in base_dimensions:
            result.append({"value": dim, "label": dim, "fieldname": frappe.scrub(dim)})

        for dim in dimensions:
            if dim.document_type not in base_dimensions:
                result.append(
                    {
                        "value": dim.document_type,
                        "label": dim.label or dim.document_type,
                        "fieldname": dim.fieldname,
                    }
                )

        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_dimension_values(dimension, txt=""):
    """Get values for a specific dimension - searches across all relevant fields"""
    try:
        dimension_meta = frappe.get_meta(dimension)
        filters = {}
        or_filters = []

        # Add disabled filter
        if dimension_meta.has_field("disabled"):
            filters["disabled"] = 0
        elif dimension_meta.has_field("enabled"):
            filters["enabled"] = 1

        # Permission check for Cost Head
        permission_filter = None
        if dimension == "Cost Head" and not has_all_access():
            allowed_heads = get_cost_head_values()
            if not allowed_heads:
                return {"status": "error", "message": "No Cost Heads accessible"}
            permission_filter = allowed_heads

        # Build search filters - search across multiple relevant fields (optimized)
        # Limit results early for better performance when searching
        limit_count = (
            500 if txt else 1000
        )  # Reduced limit when searching for faster response

        if txt:
            # Always search name field
            or_filters.append(["name", "like", f"%{txt}%"])

            # Search label field if it exists (common in many doctypes)
            if dimension_meta.has_field("label"):
                or_filters.append(["label", "like", f"%{txt}%"])

            # Search account_name field if it exists (for Account dimension)
            if dimension_meta.has_field("account_name"):
                or_filters.append(["account_name", "like", f"%{txt}%"])

            # Search title field if it exists (common in many doctypes)
            if dimension_meta.has_field("title"):
                or_filters.append(["title", "like", f"%{txt}%"])

            # Search full_name field if it exists (common in person-related doctypes)
            if dimension_meta.has_field("full_name"):
                or_filters.append(["full_name", "like", f"%{txt}%"])

        # Fetch all values that match the filters
        if permission_filter:
            # If permission filter exists, combine with search filters
            filter_list = [["name", "in", permission_filter]]

            # Add disabled/enabled filter only if field exists
            if dimension_meta.has_field("disabled"):
                filter_list.append(["disabled", "=", 0])
            elif dimension_meta.has_field("enabled"):
                filter_list.append(["enabled", "=", 1])

            # Use or_filters for search if search term provided
            search_or_filters = or_filters if txt else []

            values = frappe.get_all(
                dimension,
                filters=filter_list,
                or_filters=search_or_filters,
                fields=["name"],
                limit=limit_count if txt else 1000,
                order_by="name",
            )
        else:
            # No permission restrictions - use or_filters for search
            values = frappe.get_all(
                dimension,
                filters=filters,
                or_filters=or_filters if txt else [],
                fields=["name"],
                limit=limit_count if txt else 1000,
                order_by="name",
            )

        result = [{"value": v.name, "label": v.name} for v in values]
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_accounts(txt=""):
    """Get accounts list - optimized for fast searching"""
    try:
        # Use SQL query for better performance with LIKE searches
        if txt:
            # Search in both name and account_name fields - optimized query
            accounts = frappe.db.sql(
                """
                SELECT name, account_name
                FROM `tabAccount`
                WHERE (name LIKE %(txt)s OR account_name LIKE %(txt)s)
                ORDER BY name
                LIMIT 1000
            """,
                {"txt": f"%{txt}%"},
                as_dict=True,
            )
        else:
            # No search term - return all accounts (limited for performance)
            accounts = frappe.get_all(
                "Account", fields=["name", "account_name"], limit=1000, order_by="name"
            )

        result = [{"value": acc.name, "label": acc.name} for acc in accounts]
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_companies():
    """Get companies list"""
    try:
        companies = frappe.get_all(
            "Company", fields=["name"], limit=1000, order_by="name"
        )
        result = [{"value": comp.name, "label": comp.name} for comp in companies]
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_internal_adjustment_types():
    """Get internal adjustment types"""
    try:
        types = frappe.get_all(
            "Internal Adjustment Type", fields=["name"], limit=1000, order_by="name"
        )
        result = [{"value": t.name, "label": t.name} for t in types]
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_eagle_view_data(filters):
    """Main API to get Eagle View report data"""
    try:
        if isinstance(filters, str):
            filters = json.loads(filters)

        # Validate required filters
        report_view = filters.get("report_view")
        time_period = filters.get("time_period", CUMULATIVE)

        # Base required fields
        required_fields = ["report_view"]

        # For Multi Dimension View, require main_dimension and secondary_dimension instead of dimension
        if report_view == MULTI_DIMENSION_VIEW:
            required_fields.extend(
                ["main_dimension", "secondary_dimension", "from_date", "to_date"]
            )
        else:
            required_fields.append("dimension")

        # For Cumulative Dimension View, dates are optional (not used)
        # For all other views (including Multi Dimension View), dates are required
        if not (report_view == DIMENSION_VIEW and time_period == CUMULATIVE):
            if (
                "from_date" not in required_fields
            ):  # Only add if not already added for Multi Dimension View
                required_fields.extend(["from_date", "to_date"])

        for field in required_fields:
            if not filters.get(field):
                return {
                    "status": "error",
                    "message": f"Missing required field: {field}",
                }

        # PERMISSION CHECK: If user doesn't have all access, dimension must be Cost Head
        if not has_all_access():
            dimension = filters.get("dimension")
            main_dimension = filters.get("main_dimension")

            # For Multi Dimension View, check main_dimension
            if report_view == MULTI_DIMENSION_VIEW:
                if main_dimension != "Cost Head":
                    return {
                        "status": "error",
                        "message": "You must select Cost Head as the main dimension. Please select Cost Head or contact your administrator for access.",
                    }
            # For other views, check dimension
            elif dimension != "Cost Head":
                return {
                    "status": "error",
                    "message": "You must select Cost Head as the dimension. Please select Cost Head or contact your administrator for access.",
                }

        if report_view == DIMENSION_VIEW:
            data = get_dimension_view_data(filters)
        elif report_view == ACCOUNT_VIEW:
            data = get_account_view_data(filters)
        elif report_view == VOUCHER_VIEW:
            data = get_voucher_view_data(filters)
        elif report_view == MULTI_DIMENSION_VIEW:
            data = get_multi_dimension_view_data(filters)
        else:
            return {"status": "error", "message": "Invalid report view"}

        return {"status": "success", "data": data}
    except Exception as e:
        # Log to console only, not to database to avoid character limit issues
        import traceback

        traceback.print_exc()
        return {"status": "error", "message": str(e)}


def get_dimension_view_data(filters):
    """Get data for Dimension View"""
    dimension = filters.get("dimension")
    dimension_values = filters.get("dimension_value", [])
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    report_type = filters.get("report_type", SUMMARY)
    time_period = filters.get("time_period", CUMULATIVE)
    include_adjustment = filters.get("include_adjustment", True)
    internal_adjustment_type = filters.get("internal_adjustment_type", [])
    include_stock_asset = filters.get("include_stock_asset", True)
    include_disabled = filters.get("include_disabled_dimension", False)
    exclude_period_closing = filters.get("exclude_period_closing_entries", True)
    company = filters.get("company")
    account = filters.get("account")
    render_as_tree_view = filters.get("render_as_tree_view", True)
    # Get heads data
    heads = get_heads_data(dimension, dimension_values, include_disabled)

    # Get dimension fieldname
    dimension_fieldname = frappe.scrub(dimension)
    dim_doc = frappe.db.get_value(
        "Accounting Dimension", {"document_type": dimension}, "fieldname"
    )
    if dim_doc:
        dimension_fieldname = dim_doc

    # Check if period-wise reporting is needed
    if time_period != CUMULATIVE:
        return get_period_wise_data(
            heads,
            dimension,
            dimension_fieldname,
            filters,
            report_type,
            render_as_tree_view,
        )

    # For Cumulative Dimension View, don't use date filters
    # Set dates to None so they won't be used in queries
    cumulative_from_date = None
    cumulative_to_date = None

    # Build query conditions
    additional_accounts = filters.get("additional_accounts", [])
    additional_dimensions = filters.get("additional_dimensions", [])

    conditions = build_gl_conditions(
        dimension_fieldname,
        list(heads.keys()) if dimension_values else None,
        cumulative_from_date,
        cumulative_to_date,
        company,
        account,
        include_stock_asset,
        exclude_period_closing,
        dimension,
        additional_accounts,
        additional_dimensions,
    )

    # Get GL data
    gl_data = fetch_gl_entries(
        conditions,
        dimension_fieldname,
        report_type,
        include_stock_asset,
        cumulative_from_date,
        cumulative_to_date,
        company,
        exclude_period_closing,
        additional_accounts,
        additional_dimensions,
        dimension,
    )

    # Process data into heads
    process_gl_data_into_heads(
        heads, gl_data, dimension, report_type, render_as_tree_view
    )

    # Process adjustment data if enabled (CUMULATIVE only)
    if include_adjustment:
        adjustment_data = fetch_adjustment_data(
            dimension_fieldname,
            list(heads.keys()) if dimension_values else None,
            cumulative_from_date,
            cumulative_to_date,
            company,
            internal_adjustment_type,
            report_type,
            dimension,
            additional_accounts,
            additional_dimensions,
        )

        process_adjustment_data_into_heads(
            heads, adjustment_data, dimension, report_type, render_as_tree_view
        )

    # Check if render_as_tree_view is enabled

    # Accumulate parent values for tree structure only if render_as_tree_view is True
    if frappe.get_meta(dimension).is_tree and render_as_tree_view:
        accumulate_parent_values(
            heads, dimension, report_type, include_adjustment, internal_adjustment_type
        )

    # Convert to list and calculate indents
    result = []
    for head_name, head_data in heads.items():
        row = {"name": head_name}
        row.update(head_data)
        # Remove internal keys before sending to frontend
        row.pop("_adjustment_keys", None)
        result.append(row)

    # Sort by lft for tree display (always sort by lft if tree dimension)
    if frappe.get_meta(dimension).is_tree:
        result = sorted(result, key=lambda x: x.get("lft", 0))

        # If not rendering as tree, remove parent groups (keep only leaf nodes) and reset indents
        if not render_as_tree_view:
            # Filter out groups, but keep groups that have their own data (not just from children)
            # A group has its own data if it has non-zero values in any amount field
            filtered_result = []
            for row in result:
                # Check if this is a group
                if row.get("is_group") == 1:
                    # Check if group has its own data (not just aggregated from children)
                    has_own_data = False
                    for key, value in row.items():
                        # Skip non-numeric metadata fields
                        if key in [
                            "name",
                            "indent",
                            "is_group",
                            "lft",
                            "rgt",
                            "_adjustment_keys",
                        ]:
                            continue
                        # Check if field is amount-related
                        if (
                            key.endswith("_inc")
                            or key.endswith("_exp")
                            or key.endswith("_net")
                            or key.startswith("total_")
                        ):
                            if isinstance(value, (int, float)) and value != 0:
                                has_own_data = True
                                break

                    # Only include group if it has its own data
                    if not has_own_data:
                        continue

                # Reset indent for all rows when not rendering as tree
                row["indent"] = 0
                filtered_result.append(row)

            result = filtered_result

    # Note: Empty row filtering is now done in the frontend

    return result


def get_period_wise_data(
    heads,
    dimension,
    dimension_fieldname,
    filters,
    report_type,
    render_as_tree_view=True,
):
    """Get period-wise data for dimension view"""
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    time_period = filters.get("time_period")
    company = filters.get("company")
    account = filters.get("account")
    include_stock_asset = filters.get("include_stock_asset", True)
    exclude_period_closing = filters.get("exclude_period_closing_entries", True)
    dimension_values = filters.get("dimension_value", [])

    # Generate period buckets
    buckets = get_period_buckets(from_date, to_date, time_period)

    # Initialize heads with period columns
    for head_name in heads.keys():
        heads[head_name]["periods"] = {}
        for bucket in buckets:
            heads[head_name]["periods"][bucket["key"]] = {
                "income": 0.0,
                "expense": 0.0,
                "net": 0.0,
            }

    # Fetch GL data with posting_date for each period
    additional_accounts = filters.get("additional_accounts", [])
    additional_dimensions = filters.get("additional_dimensions", [])
    include_adjustment = filters.get("include_adjustment", True)
    internal_adjustment_type = filters.get("internal_adjustment_type", [])
    report_type = filters.get("report_type", SUMMARY)

    # Track if we need to add "Not Tagged" later (after we see the data)
    needs_not_tagged = False

    for bucket in buckets:
        conditions = build_gl_conditions(
            dimension_fieldname,
            list(heads.keys()) if dimension_values else None,
            bucket["from_date"],
            bucket["to_date"],
            company,
            account,
            include_stock_asset,
            exclude_period_closing,
            dimension,
            additional_accounts,
            additional_dimensions,
        )

        # Fetch GL data for this period with posting_date
        query = f"""
            SELECT 
                gl.{dimension_fieldname} as dimension_value,
                gl.posting_date,
                tac.root_type,
                SUM(gl.debit) as total_debit,
                SUM(gl.credit) as total_credit
            FROM `tabGL Entry` gl
            JOIN `tabAccount` tac ON tac.name = gl.account
            WHERE {conditions}
            GROUP BY gl.{dimension_fieldname}, gl.posting_date, tac.root_type
        """

        # Add UNION ALL for stock/asset accrual expenses if include_stock_asset is True
        if include_stock_asset:
            stock_asset_conditions = """
                gl.is_cancelled = 0
                AND tac.report_type = 'Balance Sheet'
                AND gl.voucher_type = 'Purchase Invoice'
                AND (
                    gl.account LIKE '%Asset Received But Not Billed%'
                    OR
                    gl.account LIKE '%Stock Received But Not Billed%'
                )
            """
            stock_asset_conditions += f" AND gl.posting_date BETWEEN '{bucket['from_date']}' AND '{bucket['to_date']}'"

            if company:
                stock_asset_conditions += f" AND gl.company = '{company}'"

            # Apply additional accounts filter
            if additional_accounts:
                all_accounts = []
                if isinstance(additional_accounts, list):
                    all_accounts.extend(additional_accounts)
                else:
                    all_accounts.append(additional_accounts)

                if all_accounts:
                    acc_str = "', '".join(all_accounts)
                    stock_asset_conditions += f" AND gl.account IN ('{acc_str}')"

            # Apply dimension filter
            if dimension_values:
                values_str = "', '".join(
                    [str(h) for h in heads.keys() if h != "Not Tagged"]
                )
                if values_str:
                    stock_asset_conditions += (
                        f" AND gl.{dimension_fieldname} IN ('{values_str}')"
                    )

            # Apply additional dimensions filters
            if additional_dimensions:
                for dim_filter in additional_dimensions:
                    if not dim_filter.get("dimension") or not dim_filter.get("values"):
                        continue

                    add_dim = dim_filter["dimension"]
                    add_values = dim_filter["values"]

                    if add_dim == dimension:
                        continue

                    expanded_values = expand_dimension_values(add_dim, add_values)
                    add_dim_field = frappe.scrub(add_dim)
                    add_dim_doc = frappe.db.get_value(
                        "Accounting Dimension", {"document_type": add_dim}, "fieldname"
                    )
                    if add_dim_doc:
                        add_dim_field = add_dim_doc

                    if add_dim == "Cost Head" and not has_all_access():
                        allowed_heads = get_cost_head_values()
                        if allowed_heads:
                            filtered_values = [
                                v
                                for v in expanded_values
                                if v != "Not Tagged" and v in allowed_heads
                            ]
                            if filtered_values:
                                values_str = "', '".join(
                                    [str(v) for v in filtered_values]
                                )
                                stock_asset_conditions += (
                                    f" AND gl.{add_dim_field} IN ('{values_str}')"
                                )
                    else:
                        if expanded_values:
                            values_str = "', '".join(
                                [str(v) for v in expanded_values if v != "Not Tagged"]
                            )
                            if values_str:
                                stock_asset_conditions += (
                                    f" AND gl.{add_dim_field} IN ('{values_str}')"
                                )

            if exclude_period_closing:
                stock_asset_conditions += (
                    " AND gl.voucher_type != 'Period Closing Voucher'"
                )

            query += f"""
            UNION ALL
            SELECT 
                gl.{dimension_fieldname} as dimension_value,
                gl.posting_date,
                'Expense' as root_type,
                SUM(gl.debit) as total_debit,
                SUM(gl.credit) as total_credit
            FROM `tabGL Entry` gl
            JOIN `tabAccount` tac ON tac.name = gl.account
            WHERE {stock_asset_conditions}
            GROUP BY gl.{dimension_fieldname}, gl.posting_date
            """

        gl_data = frappe.db.sql(query, as_dict=True)

        # Check if there's any "Not Tagged" data in GL entries for this period
        has_not_tagged = any(
            (entry.get("dimension_value") or "Not Tagged") == "Not Tagged"
            for entry in gl_data
        )

        # Add "Not Tagged" to heads dict only if there's actually untagged data and it doesn't exist yet
        if has_not_tagged and "Not Tagged" not in heads:
            parent_field = f"parent_{frappe.scrub(dimension)}"
            heads["Not Tagged"] = {
                "name": "Not Tagged",
                parent_field: None,
                "lft": 99999,  # High number to sort at end
                "rgt": 99999,
                "is_group": 0,
                "indent": 0,
                "periods": {}
            }
            # Initialize periods for "Not Tagged"
            for b in buckets:
                heads["Not Tagged"]["periods"][b["key"]] = {
                    "income": 0.0,
                    "expense": 0.0,
                    "net": 0.0,
                }
            needs_not_tagged = True

        # Process data into period buckets
        for entry in gl_data:
            dim_value = entry.get("dimension_value") or "Not Tagged"
            if dim_value in heads:
                if entry.root_type == "Income":
                    amount = entry.total_credit - entry.total_debit
                    heads[dim_value]["periods"][bucket["key"]]["income"] += amount
                    heads[dim_value]["periods"][bucket["key"]]["net"] += amount
                elif entry.root_type == "Expense":
                    amount = entry.total_debit - entry.total_credit
                    heads[dim_value]["periods"][bucket["key"]]["expense"] += amount
                    heads[dim_value]["periods"][bucket["key"]]["net"] -= amount

        # Process adjustment data for this period if enabled
        if include_adjustment:
            adjustment_data = fetch_adjustment_data(
                dimension_fieldname,
                list(heads.keys()) if dimension_values else None,
                bucket["from_date"],
                bucket["to_date"],
                company,
                internal_adjustment_type,
                report_type,
                dimension,
                additional_accounts,
                additional_dimensions,
            )

            # Check if there's any "Not Tagged" data in adjustment entries for this period
            has_not_tagged_adj = any(
                (adj_row.get("head") or "Not Tagged") == "Not Tagged"
                for adj_row in adjustment_data
            )

            # Add "Not Tagged" to heads dict if there's untagged adjustment data and it doesn't exist yet
            if has_not_tagged_adj and "Not Tagged" not in heads:
                parent_field = f"parent_{frappe.scrub(dimension)}"
                heads["Not Tagged"] = {
                    "name": "Not Tagged",
                    parent_field: None,
                    "lft": 99999,
                    "rgt": 99999,
                    "is_group": 0,
                    "indent": 0,
                    "periods": {}
                }
                # Initialize periods for "Not Tagged"
                for b in buckets:
                    heads["Not Tagged"]["periods"][b["key"]] = {
                        "income": 0.0,
                        "expense": 0.0,
                        "net": 0.0,
                    }
                needs_not_tagged = True

            for adj_row in adjustment_data:
                adj_head = adj_row.get("head") or "Not Tagged"
                if adj_head in heads:
                    if report_type == NET_PROFIT:
                        amount = adj_row.get("net_profit", 0) or 0
                        heads[adj_head]["periods"][bucket["key"]]["net"] += amount
                    else:
                        inc_amount = adj_row.get("total_inc", 0) or 0
                        exp_amount = adj_row.get("total_exp", 0) or 0
                        heads[adj_head]["periods"][bucket["key"]][
                            "income"
                        ] += inc_amount
                        heads[adj_head]["periods"][bucket["key"]][
                            "expense"
                        ] += exp_amount
                        heads[adj_head]["periods"][bucket["key"]]["net"] += (
                            inc_amount - exp_amount
                        )

    # Accumulate parent values for tree structure only if render_as_tree_view is True
    if frappe.get_meta(dimension).is_tree and render_as_tree_view:
        parent_field = f"parent_{frappe.scrub(dimension)}"

        # Sort by lft descending to process children first (same as accumulate_parent_values)
        sorted_heads = sorted(
            [(name, data) for name, data in heads.items() if name != "Not Tagged"],
            key=lambda x: x[1].get("lft", 0),
            reverse=True,
        )

        for head_name, head_data in sorted_heads:
            parent = head_data.get(parent_field)
            if parent and parent in heads:
                for bucket in buckets:
                    for key in ["income", "expense", "net"]:
                        heads[parent]["periods"][bucket["key"]][key] += heads[
                            head_name
                        ]["periods"][bucket["key"]][key]

    # Convert to list and flatten periods into columns
    result = []
    for head_name, head_data in heads.items():
        row = {
            "name": head_name,
            "indent": head_data.get("indent", 0),
            "is_group": head_data.get("is_group", 0),
            "lft": head_data.get("lft", 0),
        }

        # Add period columns based on report_type
        for bucket in buckets:
            period_data = head_data["periods"][bucket["key"]]

            if report_type == SUMMARY:
                row[f"{bucket['key']}_inc"] = period_data["income"]
                row[f"{bucket['key']}_exp"] = period_data["expense"]
            elif report_type == ONLY_INCOME:
                row[f"{bucket['key']}_inc"] = period_data["income"]
            elif report_type == ONLY_EXPENSE:
                row[f"{bucket['key']}_exp"] = period_data["expense"]
            elif report_type == NET_PROFIT:
                row[f"{bucket['key']}_net"] = period_data["net"]

        result.append(row)

    # Sort by lft for tree display
    if frappe.get_meta(dimension).is_tree:
        result = sorted(result, key=lambda x: x.get("lft", 0))

        # If not rendering as tree, remove parent groups (keep only leaf nodes) and reset indents
        if not render_as_tree_view:
            # Filter out groups, but keep groups that have their own data (not just from children)
            # A group has its own data if it has non-zero values in any period
            filtered_result = []
            for row in result:
                # Check if this is a group
                if row.get("is_group") == 1:
                    # Check if group has its own data (not just aggregated from children)
                    has_own_data = False
                    for key, value in row.items():
                        # Skip non-numeric metadata fields
                        if key in ["name", "indent", "is_group", "lft", "rgt"]:
                            continue
                        # Check if field is amount-related (period columns)
                        if (
                            key.endswith("_inc")
                            or key.endswith("_exp")
                            or key.endswith("_net")
                        ):
                            if isinstance(value, (int, float)) and value != 0:
                                has_own_data = True
                                break

                    # Only include group if it has its own data
                    if not has_own_data:
                        continue

                # Reset indent for all rows when not rendering as tree
                row["indent"] = 0
                filtered_result.append(row)

            result = filtered_result

    # Note: Empty row filtering is now done in the frontend

    # Add period metadata to response
    period_metadata = {
        "periods": [{"key": b["key"], "label": b["label"]} for b in buckets],
        "has_periods": True,
    }

    return {"data": result, "metadata": period_metadata}


def get_account_view_data(filters):
    """Get data for Account View"""
    dimension = filters.get("dimension")
    dimension_values = filters.get("dimension_value", [])
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    report_type = filters.get("report_type", SUMMARY)
    time_period = filters.get("time_period", CUMULATIVE)
    company = filters.get("company")
    account_filter = filters.get("account")
    include_disabled = filters.get("include_disabled_dimension", False)

    dimension_fieldname = frappe.scrub(dimension)
    dim_doc = frappe.db.get_value(
        "Accounting Dimension", {"document_type": dimension}, "fieldname"
    )
    if dim_doc:
        dimension_fieldname = dim_doc

    # Get all descendant heads if dimension values are selected
    # IMPORTANT: For Cost Head, always check permissions even if no values selected
    all_heads = None
    if dimension_values:
        heads_dict = get_heads_data(dimension, dimension_values, include_disabled)
        all_heads = list(heads_dict.keys())

        # If dimension is Cost Head, verify user is authorized for selected heads
        if dimension == "Cost Head" and not has_all_access():
            allowed_heads = get_cost_head_values()
            if not allowed_heads:
                frappe.throw(
                    _(
                        "You are not authorized to view any Cost Head. Please set value in Cost Head Concerned Person."
                    )
                )
            # Verify all selected heads are in allowed heads
            unauthorized_heads = [
                h for h in all_heads if h != "Not Tagged" and h not in allowed_heads
            ]
            if unauthorized_heads:
                frappe.throw(
                    _(
                        "You are not authorized to view the selected Cost Head(s): {0}"
                    ).format(", ".join(unauthorized_heads))
                )
    elif dimension == "Cost Head" and not has_all_access():
        # No dimension values selected, but Cost Head requires permission check
        allowed_heads = get_cost_head_values()
        if not allowed_heads:
            frappe.throw(
                _(
                    "You are not authorized to view any Cost Head. Please set value in Cost Head Concerned Person."
                )
            )
        # Use allowed heads as filter
        all_heads = allowed_heads

    # Check if period-wise reporting is needed
    if time_period != CUMULATIVE:
        return get_account_view_period_wise_data(
            dimension_fieldname,
            all_heads,
            filters,
            report_type,
            time_period,
            from_date,
            to_date,
            company,
            account_filter,
            dimension,
        )

    # Cumulative data
    additional_accounts = filters.get("additional_accounts", [])
    additional_dimensions = filters.get("additional_dimensions", [])
    include_stock_asset = filters.get("include_stock_asset", True)
    include_adjustment = filters.get("include_adjustment", True)
    internal_adjustment_type = filters.get("internal_adjustment_type", [])
    exclude_period_closing = filters.get("exclude_period_closing_entries", True)

    conditions = build_gl_conditions(
        dimension_fieldname,
        all_heads,
        from_date,
        to_date,
        company,
        account_filter,
        include_stock_asset,
        exclude_period_closing,
        dimension,
        additional_accounts,
        additional_dimensions,
    )

    # Add account disabled filter to conditions if include_disabled is False
    account_disabled_filter = ""
    if not include_disabled:
        account_disabled_filter = " AND tac.disabled = 0"
    
    query = f"""
        SELECT 
            gl.account,
            tac.root_type,
            SUM(CASE WHEN tac.root_type = 'Income' THEN gl.credit - gl.debit ELSE 0 END) as total_inc,
            SUM(CASE WHEN tac.root_type = 'Expense' THEN gl.debit - gl.credit ELSE 0 END) as total_exp
        FROM `tabGL Entry` gl
        JOIN `tabAccount` tac ON tac.name = gl.account
        WHERE {conditions}{account_disabled_filter}
        GROUP BY gl.account, tac.root_type
    """

    # Add UNION ALL for stock/asset accrual expenses if include_stock_asset is True
    if include_stock_asset:
        stock_asset_conditions = """
            gl.is_cancelled = 0
            AND tac.report_type = 'Balance Sheet'
            AND gl.voucher_type = 'Purchase Invoice'
            AND (
                gl.account LIKE '%Asset Received But Not Billed%'
                OR
                gl.account LIKE '%Stock Received But Not Billed%'
            )
        """

        if from_date and to_date:
            stock_asset_conditions += (
                f" AND gl.posting_date BETWEEN '{from_date}' AND '{to_date}'"
            )

        if company:
            stock_asset_conditions += f" AND gl.company = '{company}'"

        # Apply account filter
        if account_filter or additional_accounts:
            all_accounts = []
            if account_filter:
                if isinstance(account_filter, list):
                    all_accounts.extend(account_filter)
                else:
                    all_accounts.append(account_filter)
            if additional_accounts:
                if isinstance(additional_accounts, list):
                    all_accounts.extend(additional_accounts)
                else:
                    all_accounts.append(additional_accounts)
            all_accounts = list(set(all_accounts))
            if all_accounts:
                acc_str = "', '".join(all_accounts)
                stock_asset_conditions += f" AND gl.account IN ('{acc_str}')"

        # Apply dimension filter
        if all_heads:
            heads_filtered = [h for h in all_heads if h != "Not Tagged"]
            if heads_filtered:
                heads_str = "', '".join([str(h) for h in heads_filtered])
                stock_asset_conditions += (
                    f" AND gl.{dimension_fieldname} IN ('{heads_str}')"
                )

        # Apply additional dimensions filters
        if additional_dimensions:
            for dim_filter in additional_dimensions:
                if not dim_filter.get("dimension") or not dim_filter.get("values"):
                    continue

                add_dim = dim_filter["dimension"]
                add_values = dim_filter["values"]

                if add_dim == dimension:
                    continue

                expanded_values = expand_dimension_values(add_dim, add_values)
                add_dim_field = frappe.scrub(add_dim)
                add_dim_doc = frappe.db.get_value(
                    "Accounting Dimension", {"document_type": add_dim}, "fieldname"
                )
                if add_dim_doc:
                    add_dim_field = add_dim_doc

                if add_dim == "Cost Head" and not has_all_access():
                    allowed_heads = get_cost_head_values()
                    if allowed_heads:
                        filtered_values = [
                            v
                            for v in expanded_values
                            if v != "Not Tagged" and v in allowed_heads
                        ]
                        if filtered_values:
                            values_str = "', '".join([str(v) for v in filtered_values])
                            stock_asset_conditions += (
                                f" AND gl.{add_dim_field} IN ('{values_str}')"
                            )
                else:
                    if expanded_values:
                        values_str = "', '".join(
                            [str(v) for v in expanded_values if v != "Not Tagged"]
                        )
                        if values_str:
                            stock_asset_conditions += (
                                f" AND gl.{add_dim_field} IN ('{values_str}')"
                            )

        if exclude_period_closing:
            stock_asset_conditions += " AND gl.voucher_type != 'Period Closing Voucher'"

        # Add account disabled filter to stock/asset conditions if include_disabled is False
        if not include_disabled:
            stock_asset_conditions += " AND tac.disabled = 0"
        
        query += f"""
        UNION ALL
        SELECT 
            gl.account,
            'Expense' as root_type,
            0 as total_inc,
            SUM(gl.debit - gl.credit) as total_exp
        FROM `tabGL Entry` gl
        JOIN `tabAccount` tac ON tac.name = gl.account
        WHERE {stock_asset_conditions}
        GROUP BY gl.account
        """

    data = frappe.db.sql(query, as_dict=True)

    # Get all unique account names from the data
    account_names = list(set([row.account for row in data]))
    
    # If include_disabled is True, fetch disabled status for all accounts
    disabled_status_map = {}
    if include_disabled and account_names:
        account_records = frappe.get_all(
            "Account",
            filters={"name": ["in", account_names]},
            fields=["name", "disabled"]
        )
        disabled_status_map = {r.name: r.disabled for r in account_records}

    # Group by account
    accounts = {}
    for row in data:
        acc = row.account
        if acc not in accounts:
            accounts[acc] = {"account": acc, "total_inc": 0, "total_exp": 0}
            # Add disabled status if include_disabled is True
            if include_disabled:
                accounts[acc]["disabled"] = disabled_status_map.get(acc, 0)
        accounts[acc]["total_inc"] += row.total_inc or 0
        accounts[acc]["total_exp"] += row.total_exp or 0

    # Process adjustment data if enabled (grouped by account)
    if include_adjustment:
        adjustment_data = fetch_adjustment_data_by_account(
            dimension_fieldname,
            all_heads,
            from_date,
            to_date,
            company,
            internal_adjustment_type,
            dimension,
            additional_accounts,
            additional_dimensions,
        )

        # Add adjustment amounts to accounts
        for adj_row in adjustment_data:
            acc = adj_row.get("account")
            if not acc:
                continue

            if acc not in accounts:
                accounts[acc] = {"account": acc, "total_inc": 0, "total_exp": 0}
                # Add disabled status if include_disabled is True
                if include_disabled:
                    # Fetch disabled status if not already in map
                    if acc not in disabled_status_map:
                        acc_disabled = frappe.db.get_value("Account", acc, "disabled") or 0
                        disabled_status_map[acc] = acc_disabled
                    accounts[acc]["disabled"] = disabled_status_map.get(acc, 0)

            accounts[acc]["total_inc"] += adj_row.get("total_inc", 0) or 0
            accounts[acc]["total_exp"] += adj_row.get("total_exp", 0) or 0

    # Note: Empty row filtering is now done in the frontend
    result = list(accounts.values())

    return result


def get_account_view_period_wise_data(
    dimension_fieldname,
    all_heads,
    filters,
    report_type,
    time_period,
    from_date,
    to_date,
    company,
    account_filter,
    dimension,
):
    """Get period-wise data for Account View"""
    buckets = get_period_buckets(from_date, to_date, time_period)
    accounts_data = {}

    additional_accounts = filters.get("additional_accounts", [])
    additional_dimensions = filters.get("additional_dimensions", [])
    include_stock_asset = filters.get("include_stock_asset", True)
    include_adjustment = filters.get("include_adjustment", True)
    internal_adjustment_type = filters.get("internal_adjustment_type", [])
    exclude_period_closing = filters.get("exclude_period_closing_entries", True)
    include_disabled = filters.get("include_disabled_dimension", False)

    for bucket in buckets:
        conditions = build_gl_conditions(
            dimension_fieldname,
            all_heads,
            bucket["from_date"],
            bucket["to_date"],
            company,
            account_filter,
            include_stock_asset,
            exclude_period_closing,
            dimension,
            additional_accounts,
            additional_dimensions,
        )

        # Add account disabled filter to conditions if include_disabled is False
        account_disabled_filter = ""
        if not include_disabled:
            account_disabled_filter = " AND tac.disabled = 0"
        
        query = f"""
            SELECT 
                gl.account,
                tac.root_type,
                SUM(CASE WHEN tac.root_type = 'Income' THEN gl.credit - gl.debit ELSE 0 END) as income,
                SUM(CASE WHEN tac.root_type = 'Expense' THEN gl.debit - gl.credit ELSE 0 END) as expense
            FROM `tabGL Entry` gl
            JOIN `tabAccount` tac ON tac.name = gl.account
            WHERE {conditions}{account_disabled_filter}
            GROUP BY gl.account, tac.root_type
        """

        # Add UNION ALL for stock/asset accrual expenses if include_stock_asset is True
        if include_stock_asset:
            stock_asset_conditions = """
                gl.is_cancelled = 0
                AND tac.report_type = 'Balance Sheet'
                AND gl.voucher_type = 'Purchase Invoice'
                AND (
                    gl.account LIKE '%Asset Received But Not Billed%'
                    OR
                    gl.account LIKE '%Stock Received But Not Billed%'
                )
            """
            stock_asset_conditions += f" AND gl.posting_date BETWEEN '{bucket['from_date']}' AND '{bucket['to_date']}'"

            if company:
                stock_asset_conditions += f" AND gl.company = '{company}'"

            # Apply account filter
            if account_filter or additional_accounts:
                all_accounts = []
                if account_filter:
                    if isinstance(account_filter, list):
                        all_accounts.extend(account_filter)
                    else:
                        all_accounts.append(account_filter)
                if additional_accounts:
                    if isinstance(additional_accounts, list):
                        all_accounts.extend(additional_accounts)
                    else:
                        all_accounts.append(additional_accounts)
                all_accounts = list(set(all_accounts))
                if all_accounts:
                    acc_str = "', '".join(all_accounts)
                    stock_asset_conditions += f" AND gl.account IN ('{acc_str}')"

            # Apply dimension filter
            if all_heads:
                heads_filtered = [h for h in all_heads if h != "Not Tagged"]
                if heads_filtered:
                    heads_str = "', '".join([str(h) for h in heads_filtered])
                    stock_asset_conditions += (
                        f" AND gl.{dimension_fieldname} IN ('{heads_str}')"
                    )

            # Apply additional dimensions filters
            if additional_dimensions:
                for dim_filter in additional_dimensions:
                    if not dim_filter.get("dimension") or not dim_filter.get("values"):
                        continue

                    add_dim = dim_filter["dimension"]
                    add_values = dim_filter["values"]

                    if add_dim == dimension:
                        continue

                    expanded_values = expand_dimension_values(add_dim, add_values)
                    add_dim_field = frappe.scrub(add_dim)
                    add_dim_doc = frappe.db.get_value(
                        "Accounting Dimension", {"document_type": add_dim}, "fieldname"
                    )
                    if add_dim_doc:
                        add_dim_field = add_dim_doc

                    if add_dim == "Cost Head" and not has_all_access():
                        allowed_heads = get_cost_head_values()
                        if allowed_heads:
                            filtered_values = [
                                v
                                for v in expanded_values
                                if v != "Not Tagged" and v in allowed_heads
                            ]
                            if filtered_values:
                                values_str = "', '".join(
                                    [str(v) for v in filtered_values]
                                )
                                stock_asset_conditions += (
                                    f" AND gl.{add_dim_field} IN ('{values_str}')"
                                )
                    else:
                        if expanded_values:
                            values_str = "', '".join(
                                [str(v) for v in expanded_values if v != "Not Tagged"]
                            )
                            if values_str:
                                stock_asset_conditions += (
                                    f" AND gl.{add_dim_field} IN ('{values_str}')"
                                )

            if exclude_period_closing:
                stock_asset_conditions += (
                    " AND gl.voucher_type != 'Period Closing Voucher'"
                )
            
            # Add account disabled filter to stock/asset conditions if include_disabled is False
            if not include_disabled:
                stock_asset_conditions += " AND tac.disabled = 0"

            query += f"""
            UNION ALL
            SELECT 
                gl.account,
                'Expense' as root_type,
                0 as income,
                SUM(gl.debit - gl.credit) as expense
            FROM `tabGL Entry` gl
            JOIN `tabAccount` tac ON tac.name = gl.account
            WHERE {stock_asset_conditions}
            GROUP BY gl.account
            """

        data = frappe.db.sql(query, as_dict=True)

        for row in data:
            acc = row.account
            if acc not in accounts_data:
                accounts_data[acc] = {"account": acc, "periods": {}}

            if bucket["key"] not in accounts_data[acc]["periods"]:
                accounts_data[acc]["periods"][bucket["key"]] = {
                    "income": 0,
                    "expense": 0,
                }

            accounts_data[acc]["periods"][bucket["key"]]["income"] += row.income or 0
            accounts_data[acc]["periods"][bucket["key"]]["expense"] += row.expense or 0

        # Process adjustment data for this period if enabled (grouped by account)
        if include_adjustment:
            adjustment_data = fetch_adjustment_data_by_account(
                dimension_fieldname,
                all_heads,
                bucket["from_date"],
                bucket["to_date"],
                company,
                internal_adjustment_type,
                dimension,
                additional_accounts,
                additional_dimensions,
            )

            for adj_row in adjustment_data:
                acc = adj_row.get("account")
                if not acc:
                    continue

                if acc not in accounts_data:
                    accounts_data[acc] = {"account": acc, "periods": {}}

                if bucket["key"] not in accounts_data[acc]["periods"]:
                    accounts_data[acc]["periods"][bucket["key"]] = {
                        "income": 0,
                        "expense": 0,
                    }

                accounts_data[acc]["periods"][bucket["key"]]["income"] += (
                    adj_row.get("total_inc", 0) or 0
                )
                accounts_data[acc]["periods"][bucket["key"]]["expense"] += (
                    adj_row.get("total_exp", 0) or 0
                )

    # If include_disabled is True, fetch disabled status for all accounts
    disabled_status_map = {}
    if include_disabled and accounts_data:
        account_names = list(accounts_data.keys())
        account_records = frappe.get_all(
            "Account",
            filters={"name": ["in", account_names]},
            fields=["name", "disabled"]
        )
        disabled_status_map = {r.name: r.disabled for r in account_records}
    
    # Convert to result format
    result = []
    for acc_name, acc_data in accounts_data.items():
        row = {"account": acc_name}
        # Add disabled status if include_disabled is True
        if include_disabled:
            row["disabled"] = disabled_status_map.get(acc_name, 0)

        for bucket in buckets:
            period_data = acc_data["periods"].get(
                bucket["key"], {"income": 0, "expense": 0}
            )

            if report_type == SUMMARY:
                row[f"{bucket['key']}_inc"] = period_data["income"]
                row[f"{bucket['key']}_exp"] = period_data["expense"]
            elif report_type == ONLY_INCOME:
                row[f"{bucket['key']}_inc"] = period_data["income"]
            elif report_type == ONLY_EXPENSE:
                row[f"{bucket['key']}_exp"] = period_data["expense"]
            elif report_type == NET_PROFIT:
                row[f"{bucket['key']}_net"] = (
                    period_data["income"] - period_data["expense"]
                )

        result.append(row)

    # Note: Empty row filtering is now done in the frontend

    # Add period metadata
    period_metadata = {
        "periods": [{"key": b["key"], "label": b["label"]} for b in buckets],
        "has_periods": True,
    }

    return {"data": result, "metadata": period_metadata}


def fetch_adjustment_data_detailed(
    filters,
    dimension,
    dimension_fieldname,
    all_heads,
    all_main_dimension_values,
    other_additional_dimensions,
    all_accounts,
    company,
    from_date,
    to_date,
):
    """Fetch adjustment data for detailed view (similar to hkm eagle view)"""
    report_type = filters.get("report_type", DETAILED_INCOME)
    include_adjustment = filters.get("include_adjustment", True)
    internal_adjustment_type = filters.get("internal_adjustment_type", [])

    if not include_adjustment:
        return []

    conditions = """
        ia.docstatus = 1
    """

    if from_date and to_date:
        conditions += f" AND ia.posting_date BETWEEN '{from_date}' AND '{to_date}'"

    # if company:
    #     conditions += f" AND ia.company = '{company}'"

    # Handle main dimension filtering with permission check
    if dimension == "Cost Head" and not has_all_access():
        allowed_heads = get_cost_head_values()
        if allowed_heads:
            if all_main_dimension_values:
                filtered_heads = [
                    h for h in all_main_dimension_values if h in allowed_heads
                ]
                if filtered_heads:
                    heads_str = "', '".join([str(h) for h in filtered_heads])
                    conditions += f" AND iai.{dimension_fieldname} IN ('{heads_str}')"
                else:
                    return []  # No valid heads
            else:
                allowed_str = "', '".join(allowed_heads)
                conditions += f" AND iai.{dimension_fieldname} IN ('{allowed_str}')"
        else:
            return []  # No allowed heads
    elif all_main_dimension_values:
        heads_str = "', '".join([str(h) for h in all_main_dimension_values])
        if heads_str:
            conditions += f" AND iai.{dimension_fieldname} IN ('{heads_str}')"

    # Apply additional accounts filter
    if all_accounts:
        acc_str = "', '".join(all_accounts)
        conditions += f" AND iai.account IN ('{acc_str}')"

    # Apply other additional dimensions filters (AND logic - must match all)
    if other_additional_dimensions:
        for dim_filter in other_additional_dimensions:
            add_dim = dim_filter["dimension"]
            add_values = dim_filter["values"]

            expanded_values = expand_dimension_values(add_dim, add_values)

            add_dim_field = frappe.scrub(add_dim)
            add_dim_doc = frappe.db.get_value(
                "Accounting Dimension", {"document_type": add_dim}, "fieldname"
            )
            if add_dim_doc:
                add_dim_field = add_dim_doc

            if add_dim == "Cost Head" and not has_all_access():
                allowed_heads = get_cost_head_values()
                if allowed_heads:
                    filtered_values = [
                        v
                        for v in expanded_values
                        if v != "Not Tagged" and v in allowed_heads
                    ]
                    if filtered_values:
                        values_str = "', '".join([str(v) for v in filtered_values])
                        conditions += f" AND iai.{add_dim_field} IN ('{values_str}')"
                    else:
                        return []  # No valid values
                else:
                    return []  # No allowed heads
            else:
                if expanded_values:
                    values_str = "', '".join(
                        [str(v) for v in expanded_values if v != "Not Tagged"]
                    )
                    if values_str:
                        conditions += f" AND iai.{add_dim_field} IN ('{values_str}')"

    # Filter by adjustment type if specified
    if internal_adjustment_type:
        if isinstance(internal_adjustment_type, list):
            adj_types_str = "', '".join(internal_adjustment_type)
            conditions += f" AND ia.type IN ('{adj_types_str}')"
        else:
            conditions += f" AND ia.type = '{internal_adjustment_type}'"

    # Add report type specific conditions (similar to hkm eagle view)
    if report_type == DETAILED_INCOME:
        conditions += " AND ia.adjustment_for = 'Income'"
    elif report_type == DETAILED_EXPENSE:
        conditions += " AND ia.adjustment_for = 'Expense'"
    # For other report types, include both income and expense adjustments

    # Build SELECT clause for detailed view (similar to hkm eagle view)
    if report_type == DETAILED_INCOME:
        select_logic = "SUM(iai.credit - iai.debit) AS amount"
    elif report_type == DETAILED_EXPENSE:
        select_logic = "SUM(iai.debit - iai.credit) AS amount"
    else:
        # For "Both Income and Expenses" or other types, calculate based on adjustment_for
        select_logic = """
            SUM(
                CASE 
                    WHEN ia.adjustment_for = 'Income' THEN iai.credit - iai.debit
                    ELSE iai.debit - iai.credit
                END
            ) AS amount
        """

    query = f"""
        SELECT 
            ia.adjustment_for,
            COALESCE(iai.{dimension_fieldname}, 'Not Tagged') as dimension_value,
            ia.posting_date,
            ia.name,
            ia.remarks,
            iai.account AS account_head,
            {select_logic}
        FROM `tabInternal Adjustment` ia
        JOIN `tabInternal Adjustment Detail` iai ON iai.parent = ia.name
        WHERE {conditions}
        GROUP BY iai.name
    """

    return frappe.db.sql(query, as_dict=True)


def get_voucher_view_data(filters):
    """Get data for Voucher View"""
    dimension = filters.get("dimension")
    dimension_values = filters.get("dimension_value", [])
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    report_type = filters.get("report_type", DETAILED_INCOME)
    company = filters.get("company")
    include_disabled = filters.get("include_disabled_dimension", False)
    include_adjustment = filters.get("include_adjustment", True)
    include_stock_asset = filters.get("include_stock_asset", True)
    exclude_period_closing = filters.get("exclude_period_closing_entries", True)

    dimension_fieldname = frappe.scrub(dimension)
    dim_doc = frappe.db.get_value(
        "Accounting Dimension", {"document_type": dimension}, "fieldname"
    )
    if dim_doc:
        dimension_fieldname = dim_doc

    # Get all descendant heads if dimension values are selected
    # Note: get_heads_data expands dimension values to include the selected value itself
    # and all its descendants, so groups with their own data will be included
    all_heads = []
    if dimension_values:
        heads_dict = get_heads_data(dimension, dimension_values, include_disabled)
        all_heads = list(heads_dict.keys())

    # Fetch BOTH income and expense data for Detailed View (regardless of toggle selection)
    conditions = f"""
        gl.is_cancelled = 0
        AND tac.root_type IN ('Income', 'Expense')
        AND gl.posting_date BETWEEN '{from_date}' AND '{to_date}'
    """

    if company:
        conditions += f" AND gl.company = '{company}'"

    # Collect main dimension values
    main_dimension_values = []
    if all_heads:
        main_dimension_values = [h for h in all_heads if h != "Not Tagged"]

    # Check if any additional dimension matches the main dimension
    additional_same_dimension_values = []
    other_additional_dimensions = []
    additional_dimensions = filters.get("additional_dimensions", [])

    if additional_dimensions:
        for dim_filter in additional_dimensions:
            if not dim_filter.get("dimension") or not dim_filter.get("values"):
                continue

            add_dim = dim_filter["dimension"]
            add_values = dim_filter["values"]

            # If additional dimension is same as main dimension, expand and combine values
            if add_dim == dimension:
                # Expand dimension values to include descendants (for tree dimensions)
                expanded_values = expand_dimension_values(add_dim, add_values)
                additional_same_dimension_values.extend(
                    [v for v in expanded_values if v != "Not Tagged"]
                )
            else:
                other_additional_dimensions.append(dim_filter)

    # Combine main dimension values with additional same dimension values
    all_main_dimension_values = list(
        set(main_dimension_values + additional_same_dimension_values)
    )

    # Handle main dimension filtering (using combined values)
    if all_main_dimension_values:
        values_str = "', '".join([str(h) for h in all_main_dimension_values])
        if values_str:
            conditions += f" AND gl.{dimension_fieldname} IN ('{values_str}')"

    # Handle additional accounts filter
    # If main dimension is Account, combine with dimension_values
    additional_accounts = filters.get("additional_accounts", [])
    all_accounts = []

    if dimension == "Account" and dimension_values:
        all_accounts.extend(dimension_values)

    if additional_accounts:
        if isinstance(additional_accounts, list):
            all_accounts.extend(additional_accounts)
        else:
            all_accounts.append(additional_accounts)

    # Remove duplicates
    all_accounts = list(set(all_accounts))

    if all_accounts:
        acc_str = "', '".join(all_accounts)
        conditions += f" AND gl.account IN ('{acc_str}')"

    # Handle other additional dimensions filtering (AND logic - must match all)
    # Skip dimensions that match the main dimension (already handled above)
    if other_additional_dimensions:
        for dim_filter in other_additional_dimensions:
            add_dim = dim_filter["dimension"]
            add_values = dim_filter["values"]

            # Expand dimension values to include descendants (for tree dimensions)
            expanded_values = expand_dimension_values(add_dim, add_values)

            # Get fieldname for this dimension
            add_dim_field = frappe.scrub(add_dim)
            add_dim_doc = frappe.db.get_value(
                "Accounting Dimension", {"document_type": add_dim}, "fieldname"
            )
            if add_dim_doc:
                add_dim_field = add_dim_doc

            # Handle permission check for Cost Head in additional dimensions
            if add_dim == "Cost Head" and not has_all_access():
                allowed_heads = get_cost_head_values()
                if allowed_heads:
                    # Intersect with allowed heads
                    filtered_values = [
                        v
                        for v in expanded_values
                        if v != "Not Tagged" and v in allowed_heads
                    ]
                    if filtered_values:
                        values_str = "', '".join([str(v) for v in filtered_values])
                        conditions += f" AND gl.{add_dim_field} IN ('{values_str}')"
                    else:
                        # No valid values - return empty result
                        conditions += " AND 1=0"
                else:
                    # User has no allowed heads
                    conditions += " AND 1=0"
            else:
                # No permission restrictions
                if expanded_values:
                    values_str = "', '".join(
                        [str(v) for v in expanded_values if v != "Not Tagged"]
                    )
                    if values_str:
                        conditions += f" AND gl.{add_dim_field} IN ('{values_str}')"

    # IMPORTANT: When include_stock_asset is TRUE, we EXCLUDE stock/asset expenses
    # This matches the original HKM Eagle View logic (confusing naming but correct behavior)
    if include_stock_asset:
        conditions += """
        AND NOT (
            (
                tac.root_type = 'Expense'
                AND gl.against LIKE '%Stock In Hand%'
            )
            OR
            (
                tac.root_type = 'Expense'
                AND tac.account_type = 'Depreciation'
                AND tac.name LIKE '%Depreciation%'
            )
        )
        AND NOT (
            tac.root_type = 'Expense'
            AND gl.voucher_type = 'Stock Entry'
            )

        """

    if exclude_period_closing:
        conditions += " AND gl.voucher_type != 'Period Closing Voucher'"

    query = f"""
        SELECT 
            gl.posting_date,
            gl.company,
            gl.voucher_type,
            gl.voucher_no,
            gl.{dimension_fieldname} as dimension_value,
            gl.account as account_head,
            tac.root_type,
            CASE 
                WHEN tac.root_type = 'Income' THEN gl.credit - gl.debit
                ELSE gl.debit - gl.credit
            END as amount,
            gl.remarks
        FROM `tabGL Entry` gl
        JOIN `tabAccount` tac ON tac.name = gl.account
        WHERE {conditions}
    """

    # Add UNION ALL for stock/asset accrual expenses if include_stock_asset is True
    # This matches the original HKM Eagle View logic
    if include_stock_asset:
        # Build stock/asset accrual query conditions
        stock_asset_conditions = """
            gl.is_cancelled = 0
            AND tac.report_type = 'Balance Sheet'
            AND gl.voucher_type = 'Purchase Invoice'
            AND (
                gl.account LIKE '%Asset Received But Not Billed%'
                OR
                gl.account LIKE '%Stock Received But Not Billed%'
            )
        """

        # Add date filter
        stock_asset_conditions += (
            f" AND gl.posting_date BETWEEN '{from_date}' AND '{to_date}'"
        )

        if company:
            stock_asset_conditions += f" AND gl.company = '{company}'"

        # Apply additional accounts filter
        if all_accounts:
            acc_str = "', '".join(all_accounts)
            stock_asset_conditions += f" AND gl.account IN ('{acc_str}')"

        # Handle main dimension filtering (using combined values)
        if all_main_dimension_values:
            values_str = "', '".join([str(h) for h in all_main_dimension_values])
            if values_str:
                stock_asset_conditions += (
                    f" AND gl.{dimension_fieldname} IN ('{values_str}')"
                )

        # Handle other additional dimensions filtering (AND logic - must match all)
        if other_additional_dimensions:
            for dim_filter in other_additional_dimensions:
                add_dim = dim_filter["dimension"]
                add_values = dim_filter["values"]

                # Expand dimension values to include descendants (for tree dimensions)
                expanded_values = expand_dimension_values(add_dim, add_values)

                # Get fieldname for this dimension
                add_dim_field = frappe.scrub(add_dim)
                add_dim_doc = frappe.db.get_value(
                    "Accounting Dimension", {"document_type": add_dim}, "fieldname"
                )
                if add_dim_doc:
                    add_dim_field = add_dim_doc

                # Handle permission check for Cost Head in additional dimensions
                if add_dim == "Cost Head" and not has_all_access():
                    allowed_heads = get_cost_head_values()
                    if allowed_heads:
                        # Intersect with allowed heads
                        filtered_values = [
                            v
                            for v in expanded_values
                            if v != "Not Tagged" and v in allowed_heads
                        ]
                        if filtered_values:
                            values_str = "', '".join([str(v) for v in filtered_values])
                            stock_asset_conditions += (
                                f" AND gl.{add_dim_field} IN ('{values_str}')"
                            )
                        else:
                            # No valid values - return empty result
                            stock_asset_conditions += " AND 1=0"
                    else:
                        # User has no allowed heads
                        stock_asset_conditions += " AND 1=0"
                else:
                    # No permission restrictions
                    if expanded_values:
                        values_str = "', '".join(
                            [str(v) for v in expanded_values if v != "Not Tagged"]
                        )
                        if values_str:
                            stock_asset_conditions += (
                                f" AND gl.{add_dim_field} IN ('{values_str}')"
                            )

        if exclude_period_closing:
            stock_asset_conditions += " AND gl.voucher_type != 'Period Closing Voucher'"

        # Add stock/asset query as UNION ALL
        query += f"""
        UNION ALL
        SELECT 
            gl.posting_date,
            gl.company,
            gl.voucher_type,
            gl.voucher_no,
            gl.{dimension_fieldname} as dimension_value,
            gl.account as account_head,
            'Expense' as root_type,
            CAST(gl.debit - gl.credit AS SIGNED) as amount,
            gl.remarks
        FROM `tabGL Entry` gl
        JOIN `tabAccount` tac ON tac.name = gl.account
        WHERE {stock_asset_conditions}
        """

    # Add ORDER BY and LIMIT after all queries
    query += """
        ORDER BY posting_date DESC, voucher_no
        LIMIT 1000
    """

    data = frappe.db.sql(query, as_dict=True)

    # Fetch adjustment data if enabled (similar to hkm eagle view)
    adjustment_data = []
    if include_adjustment:
        adjustment_data = fetch_adjustment_data_detailed(
            filters,
            dimension,
            dimension_fieldname,
            all_heads,
            all_main_dimension_values,
            other_additional_dimensions,
            all_accounts,
            company,
            from_date,
            to_date,
        )

    # Get all unique voucher types and numbers for attachment fetching
    vouchers = {}
    for row in data:
        row["voucher_no_link"] = frappe.utils.get_link_to_form(
            row.get("voucher_type"), row.get("voucher_no")
        )
        key = f"{row.get('voucher_type')}::{row.get('voucher_no')}"
        if key not in vouchers:
            vouchers[key] = {
                "voucher_type": row.get("voucher_type"),
                "voucher_no": row.get("voucher_no"),
            }

    # Process adjustment entries and add to data (similar to hkm eagle view)
    for adj_row in adjustment_data:
        # Format adjustment entry similar to GL entry
        adj_entry = {
            "posting_date": adj_row.get("posting_date"),
            "company": company or "",
            "voucher_type": "Internal Adjustment",
            "voucher_no": adj_row.get("name"),
            "voucher_no_link": frappe.utils.get_link_to_form(
                "Internal Adjustment", adj_row.get("name")
            ),
            "dimension_value": adj_row.get("dimension_value") or "Not Tagged",
            "account_head": adj_row.get("account_head"),
            "root_type": adj_row.get("adjustment_for"),
            "amount": adj_row.get("amount", 0),
            "remarks": "IAEC :- " + (adj_row.get("remarks") or ""),
        }
        data.append(adj_entry)

        # Add to vouchers for attachment fetching
        key = f"Internal Adjustment::{adj_row.get('name')}"
        if key not in vouchers:
            vouchers[key] = {
                "voucher_type": "Internal Adjustment",
                "voucher_no": adj_row.get("name"),
            }

    # Fetch attachments for all vouchers in bulk
    attachments_map = {}
    if vouchers:
        voucher_list = list(vouchers.values())
        attachments_map = get_voucher_attachments_bulk(voucher_list)

    # Add attachments to each row (ensure all rows have attachments field)
    for row in data:
        key = f"{row.get('voucher_type')}::{row.get('voucher_no')}"
        row["attachments"] = attachments_map.get(key, [])

    # Sort by posting_date DESC, voucher_no (to keep GL and adjustment entries together)
    data = sorted(
        data,
        key=lambda x: (x.get("posting_date") or "", x.get("voucher_no") or ""),
        reverse=True,
    )

    return data


def get_voucher_attachments_bulk(vouchers):
    """Get attachments for multiple vouchers in bulk"""
    attachments_map = {}

    # Group by doctype for efficient querying
    doctype_vouchers = {}
    for v in vouchers:
        doctype = v["voucher_type"]
        if doctype not in doctype_vouchers:
            doctype_vouchers[doctype] = []
        doctype_vouchers[doctype].append(v["voucher_no"])

    # Fetch attachments for each doctype
    for doctype, voucher_nos in doctype_vouchers.items():
        if voucher_nos:
            attachments = frappe.get_all(
                "File",
                filters={
                    "attached_to_doctype": doctype,
                    "attached_to_name": ["in", voucher_nos],
                },
                fields=[
                    "attached_to_name",
                    "file_name",
                    "file_url",
                    "file_size",
                    "is_private",
                ],
            )

            for att in attachments:
                key = f"{doctype}::{att.attached_to_name}"
                if key not in attachments_map:
                    attachments_map[key] = []

                # Determine file type
                file_ext = att.file_name.lower().split(".")[-1] if att.file_name else ""
                file_type = (
                    "pdf"
                    if file_ext == "pdf"
                    else (
                        "image"
                        if file_ext in ["jpg", "jpeg", "png", "gif", "bmp", "webp"]
                        else "other"
                    )
                )

                attachments_map[key].append(
                    {
                        "file_name": att.file_name,
                        "file_url": att.file_url,
                        "file_size": att.file_size,
                        "is_private": att.is_private,
                        "file_type": file_type,
                    }
                )

    return attachments_map


def build_gl_conditions(
    dimension_field,
    heads,
    from_date,
    to_date,
    company,
    account,
    include_stock_asset,
    exclude_period_closing,
    dimension,
    additional_accounts=None,
    additional_dimensions=None,
):

    # frappe.log_error(heads)
    # frappe.log_error(f"{dimension}: {heads}", message=heads)

    """Build SQL conditions for GL query"""
    conditions = """
        gl.is_cancelled = 0
        AND tac.report_type = 'Profit and Loss'
        AND tac.root_type IN ('Income', 'Expense')
    """

    # Only add date filter if dates are provided (not None)
    if from_date and to_date:
        conditions += f" AND gl.posting_date BETWEEN '{from_date}' AND '{to_date}'"

    if company:
        conditions += f" AND gl.company = '{company}'"

    # Combine main account filter with additional accounts
    all_accounts = []
    if account:
        if isinstance(account, list):
            all_accounts.extend(account)
        else:
            all_accounts.append(account)

    if additional_accounts:
        if isinstance(additional_accounts, list):
            all_accounts.extend(additional_accounts)
        else:
            all_accounts.append(additional_accounts)

    # Remove duplicates
    all_accounts = list(set(all_accounts))

    if all_accounts:
        acc_str = "', '".join(all_accounts)
        conditions += f" AND gl.account IN ('{acc_str}')"

    # Collect all dimension values (main + additional for same dimension)
    # This handles the case where main dimension and additional dimension are the same
    main_dimension_values = []
    if heads:
        main_dimension_values = [h for h in heads if h != "Not Tagged"]

    # frappe.log_error(f"{dimension}: {main_dimension_values}", message=main_dimension_values)

    # Check if any additional dimension matches the main dimension
    additional_same_dimension_values = []
    other_additional_dimensions = []

    if additional_dimensions:
        for dim_filter in additional_dimensions:
            if not dim_filter.get("dimension") or not dim_filter.get("values"):
                continue

            add_dim = dim_filter["dimension"]
            add_values = dim_filter["values"]

            # If additional dimension is same as main dimension, expand and combine values
            if add_dim == dimension:
                # Expand dimension values to include descendants (for tree dimensions)
                expanded_values = expand_dimension_values(add_dim, add_values)
                additional_same_dimension_values.extend(
                    [v for v in expanded_values if v != "Not Tagged"]
                )
            else:
                other_additional_dimensions.append(dim_filter)

    # Combine main dimension values with additional same dimension values
    all_main_dimension_values = list(
        set(main_dimension_values + additional_same_dimension_values)
    )

    # Handle main dimension filtering with permission check (using combined values)
    if dimension == "Cost Head" and not has_all_access():
        allowed_heads = get_cost_head_values()
        if not allowed_heads:
            # User has no allowed heads - throw error
            frappe.throw(
                _(
                    "You are not authorized to view any Cost Head. Please set value in Cost Head Concerned Person."
                )
            )

        if all_main_dimension_values:
            # If specific heads selected, verify they are in allowed heads
            unauthorized_heads = [
                h
                for h in all_main_dimension_values
                if h != "Not Tagged" and h not in allowed_heads
            ]
            if unauthorized_heads:
                frappe.throw(
                    _(
                        "You are not authorized to view the selected Cost Head(s): {0}"
                    ).format(", ".join(unauthorized_heads))
                )
            # Filter to only allowed heads
            filtered_heads = [
                h
                for h in all_main_dimension_values
                if h in allowed_heads or h == "Not Tagged"
            ]
            if filtered_heads:
                filtered_heads_str = [h for h in filtered_heads if h != "Not Tagged"]
                if filtered_heads_str:
                    heads_str = "', '".join([str(h) for h in filtered_heads_str])
                    conditions += f" AND gl.{dimension_field} IN ('{heads_str}')"
        else:
            # No specific heads selected, use all allowed heads
            allowed_str = "', '".join(allowed_heads)
            conditions += f" AND gl.{dimension_field} IN ('{allowed_str}')"
    elif all_main_dimension_values:
        # No permission restrictions or not Cost Head
        heads_str = "', '".join([str(h) for h in all_main_dimension_values])
        if heads_str:
            # frappe.log_error(heads_str)
            conditions += f" AND gl.{dimension_field} IN ('{heads_str}')"

    # Handle other additional dimensions filtering (AND logic - must match all)
    # Skip dimensions that match the main dimension (already handled above)
    if other_additional_dimensions:
        for dim_filter in other_additional_dimensions:
            add_dim = dim_filter["dimension"]
            add_values = dim_filter["values"]

            # Expand dimension values to include descendants (for tree dimensions)
            expanded_values = expand_dimension_values(add_dim, add_values)

            # Get fieldname for this dimension
            add_dim_field = frappe.scrub(add_dim)
            add_dim_doc = frappe.db.get_value(
                "Accounting Dimension", {"document_type": add_dim}, "fieldname"
            )
            if add_dim_doc:
                add_dim_field = add_dim_doc

            # Handle permission check for Cost Head in additional dimensions
            if add_dim == "Cost Head" and not has_all_access():
                allowed_heads = get_cost_head_values()
                if allowed_heads:
                    # Intersect with allowed heads
                    filtered_values = [
                        v
                        for v in expanded_values
                        if v != "Not Tagged" and v in allowed_heads
                    ]
                    if filtered_values:
                        values_str = "', '".join([str(v) for v in filtered_values])
                        conditions += f" AND gl.{add_dim_field} IN ('{values_str}')"
                    else:
                        # No valid values - return empty result
                        conditions += " AND 1=0"
                else:
                    # User has no allowed heads
                    conditions += " AND 1=0"
            else:
                # No permission restrictions
                if expanded_values:
                    values_str = "', '".join(
                        [str(v) for v in expanded_values if v != "Not Tagged"]
                    )
                    if values_str:
                        conditions += f" AND gl.{add_dim_field} IN ('{values_str}')"

    # IMPORTANT: When include_stock_asset is TRUE, we EXCLUDE stock/asset expenses
    # This matches the original HKM Eagle View logic (confusing naming but correct behavior)
    if include_stock_asset:
        conditions += """
        AND NOT (
                (tac.root_type = 'Expense' AND gl.against LIKE '%%Stock In Hand%%')
                OR
                (tac.root_type = 'Expense' AND tac.account_type = 'Depreciation' AND tac.name LIKE '%%Depreciation%%')
            )
        """

    if exclude_period_closing:
        conditions += " AND gl.voucher_type != 'Period Closing Voucher'"

    # Debug logging (commented out for production)
    # print(f"=== GL CONDITIONS DEBUG ===")
    # print(f"include_stock_asset: {include_stock_asset}")
    # print(f"Full conditions:\n{conditions}")
    # print(f"===========================\n")
    return conditions


def fetch_gl_entries(
    conditions,
    dimension_field,
    report_type,
    include_stock_asset=False,
    from_date=None,
    to_date=None,
    company=None,
    exclude_period_closing=True,
    additional_accounts=None,
    additional_dimensions=None,
    dimension=None,
):
    """Fetch GL entries from database"""
    if report_type == NET_PROFIT:
        select_clause = """
            COALESCE(gl.{dimension_field}, 'Not Tagged') as head,
            SUM(CASE WHEN tac.root_type = 'Income' THEN gl.credit - gl.debit 
                     WHEN tac.root_type = 'Expense' THEN gl.debit - gl.credit 
                     ELSE 0 END) as net_profit
        """.format(
            dimension_field=dimension_field
        )
    else:
        select_clause = """
            COALESCE(gl.{dimension_field}, 'Not Tagged') as head,
            SUM(CASE WHEN tac.root_type = 'Income' THEN gl.credit - gl.debit ELSE 0 END) as total_inc,
            SUM(CASE WHEN tac.root_type = 'Expense' THEN gl.debit - gl.credit ELSE 0 END) as total_exp
        """.format(
            dimension_field=dimension_field
        )

    query = f"""
        SELECT {select_clause}
        FROM `tabGL Entry` gl
        JOIN `tabAccount` tac ON tac.name = gl.account
        WHERE {conditions}
        GROUP BY head
    """

    # Add UNION ALL for stock/asset accrual expenses if include_stock_asset is True
    # This matches the original HKM Eagle View logic
    # Include for SUMMARY, ONLY_EXPENSE, and NET_PROFIT (expenses affect net profit)
    if include_stock_asset and report_type in [SUMMARY, ONLY_EXPENSE, NET_PROFIT]:
        # Build stock/asset accrual query conditions
        stock_asset_conditions = """
            gl.is_cancelled = 0
            AND tac.report_type = 'Balance Sheet'
            AND gl.voucher_type = 'Purchase Invoice'
            AND (
                gl.account LIKE '%Asset Received But Not Billed%'
                OR
                gl.account LIKE '%Stock Received But Not Billed%'
            )
        """

        # Only add date filter if dates are provided (not None)
        if from_date and to_date:
            stock_asset_conditions += (
                f" AND gl.posting_date BETWEEN '{from_date}' AND '{to_date}'"
            )

        if company:
            stock_asset_conditions += f" AND gl.company = '{company}'"

        # Apply additional accounts filter
        if additional_accounts:
            all_accounts = []
            if isinstance(additional_accounts, list):
                all_accounts.extend(additional_accounts)
            else:
                all_accounts.append(additional_accounts)

            if all_accounts:
                acc_str = "', '".join(all_accounts)
                stock_asset_conditions += f" AND gl.account IN ('{acc_str}')"

        # Apply additional dimensions filters (AND logic - must match all)
        if additional_dimensions and dimension:
            for dim_filter in additional_dimensions:
                if not dim_filter.get("dimension") or not dim_filter.get("values"):
                    continue

                add_dim = dim_filter["dimension"]
                add_values = dim_filter["values"]

                # Skip if this is the same as main dimension (already filtered by dimension_field in main query)
                if add_dim == dimension:
                    continue

                # Expand dimension values to include descendants (for tree dimensions)
                expanded_values = expand_dimension_values(add_dim, add_values)

                # Get fieldname for this dimension
                add_dim_field = frappe.scrub(add_dim)
                add_dim_doc = frappe.db.get_value(
                    "Accounting Dimension", {"document_type": add_dim}, "fieldname"
                )
                if add_dim_doc:
                    add_dim_field = add_dim_doc

                # Handle permission check for Cost Head in additional dimensions
                if add_dim == "Cost Head" and not has_all_access():
                    allowed_heads = get_cost_head_values()
                    if allowed_heads:
                        # Intersect with allowed heads
                        filtered_values = [
                            v
                            for v in expanded_values
                            if v != "Not Tagged" and v in allowed_heads
                        ]
                        if filtered_values:
                            values_str = "', '".join([str(v) for v in filtered_values])
                            stock_asset_conditions += (
                                f" AND gl.{add_dim_field} IN ('{values_str}')"
                            )
                        else:
                            # No valid values - return empty result
                            stock_asset_conditions += " AND 1=0"
                    else:
                        # User has no allowed heads
                        stock_asset_conditions += " AND 1=0"
                else:
                    # No permission restrictions
                    if expanded_values:
                        values_str = "', '".join(
                            [str(v) for v in expanded_values if v != "Not Tagged"]
                        )
                        if values_str:
                            stock_asset_conditions += (
                                f" AND gl.{add_dim_field} IN ('{values_str}')"
                            )

        if exclude_period_closing:
            stock_asset_conditions += " AND gl.voucher_type != 'Period Closing Voucher'"

        # Build SELECT clause for stock/asset query
        if report_type == NET_PROFIT:
            stock_select = """
                COALESCE(gl.{dimension_field}, 'Not Tagged') as head,
                CAST(0 - COALESCE(SUM(gl.debit - gl.credit), 0) AS SIGNED) AS net_profit
            """.format(
                dimension_field=dimension_field
            )
        else:
            stock_select = """
                COALESCE(gl.{dimension_field}, 'Not Tagged') as head,
                0 AS total_inc,
                CAST(COALESCE(SUM(gl.debit - gl.credit), 0) AS SIGNED) AS total_exp
            """.format(
                dimension_field=dimension_field
            )

        query += f"""
        UNION ALL
        SELECT {stock_select}
        FROM `tabGL Entry` gl
        JOIN `tabAccount` tac ON tac.name = gl.account
        WHERE {stock_asset_conditions}
        GROUP BY head
        """

    # Debug logging (commented out for production)
    # print(f"=== FINAL GL QUERY ===")
    # print(query)
    # print(f"===========================\n")

    return frappe.db.sql(query, as_dict=True)


def process_gl_data_into_heads(
    heads, gl_data, dimension, report_type, render_as_tree_view
):
    """Process GL data into heads dictionary - ONLY UPDATE LEAF NODES"""
    parent_field = f"parent_{frappe.scrub(dimension)}"

    # Check if there's any "Not Tagged" data in GL entries
    has_not_tagged = any(row.head == "Not Tagged" for row in gl_data)

    # Add "Not Tagged" to heads dict only if there's actually untagged data
    if has_not_tagged and "Not Tagged" not in heads:
        heads["Not Tagged"] = {
            "name": "Not Tagged",
            parent_field: None,
            "lft": 99999,  # High number to sort at end
            "rgt": 99999,
            "is_group": 0,
            "indent": 0,
        }

    for row in gl_data:
        head_name = row.head
        if head_name not in heads:
            continue

        head = heads[head_name]

        # Process data for all nodes (including groups that have their own data)
        # Groups will be filtered out later if render_as_tree_view is false and they don't have own data
        # CRITICAL FIX: Use += to accumulate, not = to assign!
        if report_type == NET_PROFIT:
            head["total_net"] = head.get("total_net", 0) + (row.net_profit or 0)
        else:
            head["total_inc"] = head.get("total_inc", 0) + (row.total_inc or 0)
            head["total_exp"] = head.get("total_exp", 0) + (row.total_exp or 0)
            # Calculate net for frontend display (income - expense)
            head["total_net"] = head.get("total_net", 0) + (
                (row.total_inc or 0) - (row.total_exp or 0)
            )


def fetch_adjustment_data(
    dimension_field,
    heads,
    from_date,
    to_date,
    company,
    internal_adjustment_type,
    report_type,
    dimension,
    additional_accounts=None,
    additional_dimensions=None,
):
    """Fetch adjustment data from Internal Adjustment tables"""
    conditions = """
        ia.docstatus = 1
    """

    # Only add date filter if dates are provided (not None)
    if from_date and to_date:
        conditions += f" AND ia.posting_date BETWEEN '{from_date}' AND '{to_date}'"

    # if company:
    #     conditions += f" AND ia.company = '{company}'"

    # Collect all dimension values (main + additional for same dimension)
    main_dimension_values = []
    if heads:
        main_dimension_values = [h for h in heads if h != "Not Tagged"]

    # Check if any additional dimension matches the main dimension
    additional_same_dimension_values = []
    other_additional_dimensions = []

    if additional_dimensions:
        for dim_filter in additional_dimensions:
            if not dim_filter.get("dimension") or not dim_filter.get("values"):
                continue

            add_dim = dim_filter["dimension"]
            add_values = dim_filter["values"]

            # If additional dimension is same as main dimension, expand and combine values
            if add_dim == dimension:
                # Expand dimension values to include descendants (for tree dimensions)
                expanded_values = expand_dimension_values(add_dim, add_values)
                additional_same_dimension_values.extend(
                    [v for v in expanded_values if v != "Not Tagged"]
                )
            else:
                other_additional_dimensions.append(dim_filter)

    # Combine main dimension values with additional same dimension values
    all_main_dimension_values = list(
        set(main_dimension_values + additional_same_dimension_values)
    )

    # Handle main dimension filtering with permission check (using combined values)
    if dimension == "Cost Head" and not has_all_access():
        allowed_heads = get_cost_head_values()
        if allowed_heads:
            if all_main_dimension_values:
                # If specific heads selected, intersect with allowed heads
                filtered_heads = [
                    h for h in all_main_dimension_values if h in allowed_heads
                ]
                if filtered_heads:
                    heads_str = "', '".join([str(h) for h in filtered_heads])
                    conditions += f" AND iai.{dimension_field} IN ('{heads_str}')"
                else:
                    # No valid heads after filtering - return empty result condition
                    conditions += " AND 1=0"
            else:
                # No specific heads selected, use all allowed heads
                allowed_str = "', '".join(allowed_heads)
                conditions += f" AND iai.{dimension_field} IN ('{allowed_str}')"
        else:
            # User has no allowed heads
            conditions += " AND 1=0"
    elif all_main_dimension_values:
        # No permission restrictions or not Cost Head
        heads_str = "', '".join([str(h) for h in all_main_dimension_values])
        if heads_str:
            conditions += f" AND iai.{dimension_field} IN ('{heads_str}')"

    # Apply additional accounts filter
    if additional_accounts:
        all_accounts = []
        if isinstance(additional_accounts, list):
            all_accounts.extend(additional_accounts)
        else:
            all_accounts.append(additional_accounts)

        if all_accounts:
            acc_str = "', '".join(all_accounts)
            conditions += f" AND iai.account IN ('{acc_str}')"

    # Apply other additional dimensions filters (AND logic - must match all)
    # Skip dimensions that match the main dimension (already handled above)
    if other_additional_dimensions:
        for dim_filter in other_additional_dimensions:
            add_dim = dim_filter["dimension"]
            add_values = dim_filter["values"]

            # Expand dimension values to include descendants (for tree dimensions)
            expanded_values = expand_dimension_values(add_dim, add_values)

            # Get fieldname for this dimension
            add_dim_field = frappe.scrub(add_dim)
            add_dim_doc = frappe.db.get_value(
                "Accounting Dimension", {"document_type": add_dim}, "fieldname"
            )
            if add_dim_doc:
                add_dim_field = add_dim_doc

            # Handle permission check for Cost Head in additional dimensions
            if add_dim == "Cost Head" and not has_all_access():
                allowed_heads = get_cost_head_values()
                if allowed_heads:
                    # Intersect with allowed heads
                    filtered_values = [
                        v
                        for v in expanded_values
                        if v != "Not Tagged" and v in allowed_heads
                    ]
                    if filtered_values:
                        values_str = "', '".join([str(v) for v in filtered_values])
                        conditions += f" AND iai.{add_dim_field} IN ('{values_str}')"
                    else:
                        # No valid values - return empty result
                        conditions += " AND 1=0"
                else:
                    # User has no allowed heads
                    conditions += " AND 1=0"
            else:
                # No permission restrictions
                if expanded_values:
                    values_str = "', '".join(
                        [str(v) for v in expanded_values if v != "Not Tagged"]
                    )
                    if values_str:
                        conditions += f" AND iai.{add_dim_field} IN ('{values_str}')"

    # Filter by adjustment type if specified
    if internal_adjustment_type:
        if isinstance(internal_adjustment_type, list):
            adj_types_str = "', '".join(internal_adjustment_type)
            conditions += f" AND ia.type IN ('{adj_types_str}')"
        else:
            conditions += f" AND ia.type = '{internal_adjustment_type}'"

    # Add report type specific conditions
    if report_type == ONLY_INCOME:
        conditions += " AND ia.adjustment_for = 'Income'"
    elif report_type == ONLY_EXPENSE:
        conditions += " AND ia.adjustment_for = 'Expense'"

    # Build SELECT clause based on report type
    if report_type == NET_PROFIT:
        select_clause = """
            COALESCE(iai.{dimension_field}, 'Not Tagged') as head,
            ia.adjustment_for,
            ia.type as adjustment_type,
            CAST((
                COALESCE(SUM(CASE WHEN ia.adjustment_for = 'Income' THEN iai.credit - iai.debit ELSE 0 END), 0)
                -
                COALESCE(SUM(CASE WHEN ia.adjustment_for = 'Expense' THEN iai.debit - iai.credit ELSE 0 END), 0)
            ) AS SIGNED) AS net_profit
        """.format(
            dimension_field=dimension_field
        )
    else:
        select_clause = """
            COALESCE(iai.{dimension_field}, 'Not Tagged') as head,
            ia.adjustment_for,
            ia.type as adjustment_type,
            CAST(COALESCE(SUM(CASE WHEN ia.adjustment_for = 'Income' THEN iai.credit - iai.debit ELSE 0 END), 0) AS SIGNED) AS total_inc,
            CAST(COALESCE(SUM(CASE WHEN ia.adjustment_for = 'Expense' THEN iai.debit - iai.credit ELSE 0 END), 0) AS SIGNED) AS total_exp
        """.format(
            dimension_field=dimension_field
        )

    # Build GROUP BY clause
    if report_type in [ONLY_INCOME, ONLY_EXPENSE]:
        group_by = "GROUP BY head, ia.adjustment_for, adjustment_type"
    else:
        group_by = "GROUP BY head"

    query = f"""
        SELECT {select_clause}
        FROM `tabInternal Adjustment` ia
        JOIN `tabInternal Adjustment Detail` iai ON iai.parent = ia.name
        WHERE {conditions}
        {group_by}
    """

    return frappe.db.sql(query, as_dict=True)


def fetch_adjustment_data_by_account(
    dimension_field,
    heads,
    from_date,
    to_date,
    company,
    internal_adjustment_type,
    dimension,
    additional_accounts=None,
    additional_dimensions=None,
):
    """Fetch adjustment data grouped by account (for Account View)"""
    conditions = """
        ia.docstatus = 1
    """

    # Only add date filter if dates are provided (not None)
    if from_date and to_date:
        conditions += f" AND ia.posting_date BETWEEN '{from_date}' AND '{to_date}'"

    # Collect all dimension values (main + additional for same dimension)
    main_dimension_values = []
    if heads:
        main_dimension_values = [h for h in heads if h != "Not Tagged"]

    # Check if any additional dimension matches the main dimension
    additional_same_dimension_values = []
    other_additional_dimensions = []

    if additional_dimensions:
        for dim_filter in additional_dimensions:
            if not dim_filter.get("dimension") or not dim_filter.get("values"):
                continue

            add_dim = dim_filter["dimension"]
            add_values = dim_filter["values"]

            # If additional dimension is same as main dimension, expand and combine values
            if add_dim == dimension:
                # Expand dimension values to include descendants (for tree dimensions)
                expanded_values = expand_dimension_values(add_dim, add_values)
                additional_same_dimension_values.extend(
                    [v for v in expanded_values if v != "Not Tagged"]
                )
            else:
                other_additional_dimensions.append(dim_filter)

    # Combine main dimension values with additional same dimension values
    all_main_dimension_values = list(
        set(main_dimension_values + additional_same_dimension_values)
    )

    # Handle main dimension filtering with permission check (using combined values)
    if dimension == "Cost Head" and not has_all_access():
        allowed_heads = get_cost_head_values()
        if allowed_heads:
            if all_main_dimension_values:
                # If specific heads selected, intersect with allowed heads
                filtered_heads = [
                    h for h in all_main_dimension_values if h in allowed_heads
                ]
                if filtered_heads:
                    heads_str = "', '".join([str(h) for h in filtered_heads])
                    conditions += f" AND iai.{dimension_field} IN ('{heads_str}')"
                else:
                    # No valid heads after filtering - return empty result condition
                    conditions += " AND 1=0"
            else:
                # No specific heads selected, use all allowed heads
                allowed_str = "', '".join(allowed_heads)
                conditions += f" AND iai.{dimension_field} IN ('{allowed_str}')"
        else:
            # User has no allowed heads
            conditions += " AND 1=0"
    elif all_main_dimension_values:
        # No permission restrictions or not Cost Head
        heads_str = "', '".join([str(h) for h in all_main_dimension_values])
        if heads_str:
            conditions += f" AND iai.{dimension_field} IN ('{heads_str}')"

    # Apply additional accounts filter
    if additional_accounts:
        all_accounts = []
        if isinstance(additional_accounts, list):
            all_accounts.extend(additional_accounts)
        else:
            all_accounts.append(additional_accounts)

        if all_accounts:
            acc_str = "', '".join(all_accounts)
            conditions += f" AND iai.account IN ('{acc_str}')"

    # Apply other additional dimensions filters (AND logic - must match all)
    # Skip dimensions that match the main dimension (already handled above)
    if other_additional_dimensions:
        for dim_filter in other_additional_dimensions:
            add_dim = dim_filter["dimension"]
            add_values = dim_filter["values"]

            # Expand dimension values to include descendants (for tree dimensions)
            expanded_values = expand_dimension_values(add_dim, add_values)

            # Get fieldname for this dimension
            add_dim_field = frappe.scrub(add_dim)
            add_dim_doc = frappe.db.get_value(
                "Accounting Dimension", {"document_type": add_dim}, "fieldname"
            )
            if add_dim_doc:
                add_dim_field = add_dim_doc

            # Handle permission check for Cost Head in additional dimensions
            if add_dim == "Cost Head" and not has_all_access():
                allowed_heads = get_cost_head_values()
                if allowed_heads:
                    # Intersect with allowed heads
                    filtered_values = [
                        v
                        for v in expanded_values
                        if v != "Not Tagged" and v in allowed_heads
                    ]
                    if filtered_values:
                        values_str = "', '".join([str(v) for v in filtered_values])
                        conditions += f" AND iai.{add_dim_field} IN ('{values_str}')"
                    else:
                        # No valid values - return empty result
                        conditions += " AND 1=0"
                else:
                    # User has no allowed heads
                    conditions += " AND 1=0"
            else:
                # No permission restrictions
                if expanded_values:
                    values_str = "', '".join(
                        [str(v) for v in expanded_values if v != "Not Tagged"]
                    )
                    if values_str:
                        conditions += f" AND iai.{add_dim_field} IN ('{values_str}')"

    # Filter by adjustment type if specified
    if internal_adjustment_type:
        if isinstance(internal_adjustment_type, list):
            adj_types_str = "', '".join(internal_adjustment_type)
            conditions += f" AND ia.type IN ('{adj_types_str}')"
        else:
            conditions += f" AND ia.type = '{internal_adjustment_type}'"

    # Build SELECT clause grouped by account
    select_clause = """
        iai.account,
        CAST(COALESCE(SUM(CASE WHEN ia.adjustment_for = 'Income' THEN iai.credit - iai.debit ELSE 0 END), 0) AS SIGNED) AS total_inc,
        CAST(COALESCE(SUM(CASE WHEN ia.adjustment_for = 'Expense' THEN iai.debit - iai.credit ELSE 0 END), 0) AS SIGNED) AS total_exp
    """

    query = f"""
        SELECT {select_clause}
        FROM `tabInternal Adjustment` ia
        JOIN `tabInternal Adjustment Detail` iai ON iai.parent = ia.name
        WHERE {conditions}
        GROUP BY iai.account
    """

    return frappe.db.sql(query, as_dict=True)


def process_adjustment_data_into_heads(
    heads, adjustment_data, dimension, report_type, render_as_tree_view
):
    """Process adjustment data into heads dictionary - ONLY UPDATE LEAF NODES"""
    parent_field = f"parent_{frappe.scrub(dimension)}"

    # Track adjustment keys for separate columns
    adjustment_keys_inc = []
    adjustment_keys_exp = []

    # Process all adjustment data and add to main columns
    for row in adjustment_data:
        head_name = row.get("head") or "Not Tagged"
        adjustment_type = row.get("adjustment_type")

        if head_name not in heads:
            heads[head_name] = {
                "name": head_name,
                parent_field: None,
                "lft": 99999,
                "rgt": 99999,
                "is_group": 0,
                "indent": 0,
                "total_inc": 0,
                "total_exp": 0,
                "total_net": 0,
            }

        # Process adjustment data for all nodes (including groups that have their own data)
        # Groups will be filtered out later if render_as_tree_view is false and they don't have own data
        head = heads[head_name]

        # Add to main columns (process all nodes, filter later)
        if report_type == NET_PROFIT:
            heads[head_name]["total_net"] = heads[head_name].get("total_net", 0) + (
                row.get("net_profit", 0) or 0
            )
        else:
            heads[head_name]["total_inc"] = heads[head_name].get("total_inc", 0) + (
                row.get("total_inc", 0) or 0
            )
            heads[head_name]["total_exp"] = heads[head_name].get("total_exp", 0) + (
                row.get("total_exp", 0) or 0
            )
            heads[head_name]["total_net"] = heads[head_name].get("total_net", 0) + (
                (row.get("total_inc", 0) or 0) - (row.get("total_exp", 0) or 0)
            )

        # ADDITIONAL: Create separate columns per adjustment type (only for leaf nodes)
        if adjustment_type:
            adj_type_scrubbed = frappe.scrub(adjustment_type)

            # Create income adjustment column
            adj_inc_key = f"{adj_type_scrubbed}_inc"
            if adj_inc_key not in adjustment_keys_inc:
                adjustment_keys_inc.append(adj_inc_key)

            if adj_inc_key not in heads[head_name]:
                heads[head_name][adj_inc_key] = 0
            heads[head_name][adj_inc_key] += row.get("total_inc", 0) or 0

            # Create expense adjustment column
            adj_exp_key = f"{adj_type_scrubbed}_exp"
            if adj_exp_key not in adjustment_keys_exp:
                adjustment_keys_exp.append(adj_exp_key)

            if adj_exp_key not in heads[head_name]:
                heads[head_name][adj_exp_key] = 0
            heads[head_name][adj_exp_key] += row.get("total_exp", 0) or 0

    # Store adjustment keys in all heads for parent accumulation
    all_adjustment_keys = adjustment_keys_inc + adjustment_keys_exp
    for head in heads.values():
        head["_adjustment_keys"] = all_adjustment_keys
        # Initialize adjustment keys to 0 if they don't exist
        for adj_key in all_adjustment_keys:
            if adj_key not in head:
                head[adj_key] = 0


def accumulate_parent_values(
    heads,
    dimension,
    report_type,
    include_adjustment=False,
    internal_adjustment_type=None,
):
    """Accumulate values from children to parents in tree structure"""
    parent_field = f"parent_{frappe.scrub(dimension)}"

    # Get adjustment keys if they exist
    adjustment_keys = []
    if include_adjustment:
        for head_data in heads.values():
            if "_adjustment_keys" in head_data:
                adjustment_keys = head_data["_adjustment_keys"]
                break

    # Sort by lft descending to process children first
    sorted_heads = sorted(
        [(name, data) for name, data in heads.items() if name != "Not Tagged"],
        key=lambda x: x[1].get("lft", 0),
        reverse=True,
    )

    for head_name, head_data in sorted_heads:
        parent_name = head_data.get(parent_field)
        if parent_name and parent_name in heads:
            parent = heads[parent_name]

            # Accumulate main columns (existing logic - don't change)
            if report_type == NET_PROFIT:
                parent["total_net"] = parent.get("total_net", 0) + head_data.get(
                    "total_net", 0
                )
            else:
                parent["total_inc"] = parent.get("total_inc", 0) + head_data.get(
                    "total_inc", 0
                )
                parent["total_exp"] = parent.get("total_exp", 0) + head_data.get(
                    "total_exp", 0
                )

            # ADDITIONAL: Accumulate adjustment type columns
            if include_adjustment:
                for adj_key in adjustment_keys:
                    if adj_key not in parent:
                        parent[adj_key] = 0
                    parent[adj_key] += head_data.get(adj_key, 0)


def get_multi_dimension_view_data(filters):
    """Get data for Multi Dimension View - Independent implementation"""
    # Main dimension used as rows (vertical)
    main_dimension = filters.get("main_dimension")
    main_dimension_values = filters.get("main_dimension_value", [])

    # Secondary dimension used as columns (like dates in dimension view)
    secondary_dimension = filters.get("secondary_dimension")
    secondary_dimension_values = filters.get("secondary_dimension_value", [])

    include_adjustment = filters.get("include_adjustment", True)
    internal_adjustment_type = filters.get("internal_adjustment_type", [])
    include_stock_asset = filters.get("include_stock_asset", True)
    include_disabled = filters.get("include_disabled_dimension", False)
    exclude_period_closing = filters.get("exclude_period_closing_entries", True)
    company = filters.get("company")
    account = filters.get("account")
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    render_as_tree_view = filters.get("render_as_tree_view", True)

    # Build query conditions
    additional_accounts = filters.get("additional_accounts", [])
    additional_dimensions = filters.get("additional_dimensions", [])

    # Get main dimension fieldname
    main_dimension_fieldname = frappe.scrub(main_dimension)
    dim_doc = frappe.db.get_value(
        "Accounting Dimension", {"document_type": main_dimension}, "fieldname"
    )
    if dim_doc:
        main_dimension_fieldname = dim_doc

    # Get main dimension heads (rows)
    heads = get_heads_data(main_dimension, main_dimension_values, include_disabled)

    # Initialize heads with empty secondary_dims dict
    for head_name in heads.keys():
        heads[head_name]["secondary_dims"] = {}

    # Get secondary dimension fieldname
    secondary_dimension_fieldname = frappe.scrub(secondary_dimension)
    dim_doc = frappe.db.get_value(
        "Accounting Dimension", {"document_type": secondary_dimension}, "fieldname"
    )
    if dim_doc:
        secondary_dimension_fieldname = dim_doc

    # Optimization: If secondary_dimension_values is empty, we'll fetch only dimensions that have data
    if secondary_dimension_values:
        # User provided specific values - use them
        secondary_heads = get_heads_data(
            secondary_dimension, secondary_dimension_values, include_disabled
        )
        secondary_dimension_list = list(secondary_heads.keys())
    else:
        # No values provided - will be populated from GL/adjustment data
        secondary_dimension_list = []

    # Build GL conditions with date filter
    # Don't filter by secondary dimension if we need to discover which ones have data
    conditions = build_gl_conditions(
        main_dimension_fieldname,
        list(heads.keys()) if main_dimension_values else None,
        from_date,
        to_date,
        company,
        account,
        include_stock_asset,
        exclude_period_closing,
        main_dimension,
        additional_accounts,
        additional_dimensions,
    )

    # Add secondary dimension filter if values provided
    if secondary_dimension_values:
        # Expand secondary dimension values
        expanded_secondary_values = expand_dimension_values(
            secondary_dimension, secondary_dimension_values
        )
        secondary_values_filtered = [
            v for v in expanded_secondary_values if v != "Not Tagged"
        ]

        if secondary_dimension == "Cost Head" and not has_all_access():
            allowed_heads = get_cost_head_values()
            if allowed_heads:
                if secondary_values_filtered:
                    filtered_heads = [
                        h for h in secondary_values_filtered if h in allowed_heads
                    ]
                    if filtered_heads:
                        heads_str = "', '".join([str(h) for h in filtered_heads])
                        conditions += f" AND gl.{secondary_dimension_fieldname} IN ('{heads_str}')"
                    else:
                        conditions += " AND 1=0"  # No valid heads
                else:
                    allowed_str = "', '".join(allowed_heads)
                    conditions += (
                        f" AND gl.{secondary_dimension_fieldname} IN ('{allowed_str}')"
                    )
            else:
                conditions += " AND 1=0"  # No allowed heads
        elif secondary_values_filtered:
            heads_str = "', '".join([str(h) for h in secondary_values_filtered])
            if heads_str:
                conditions += (
                    f" AND gl.{secondary_dimension_fieldname} IN ('{heads_str}')"
                )

    # Fetch GL data grouped by both dimensions
    query = f"""
    SELECT 
        COALESCE(gl.{main_dimension_fieldname}, 'Not Tagged') as main_dim_value,
        COALESCE(gl.{secondary_dimension_fieldname}, 'Not Tagged') as secondary_dim_value,
        tac.root_type,
        SUM(gl.debit) as total_debit,
        SUM(gl.credit) as total_credit
    FROM `tabGL Entry` gl
    JOIN `tabAccount` tac ON tac.name = gl.account
    WHERE {conditions}
    GROUP BY gl.{main_dimension_fieldname}, gl.{secondary_dimension_fieldname}, tac.root_type
    """

    # Add UNION ALL for stock/asset accrual expenses if include_stock_asset is True
    if include_stock_asset:
        # Build stock/asset accrual query conditions
        stock_asset_conditions = f"""
        gl.is_cancelled = 0
        AND tac.report_type = 'Balance Sheet'
        AND gl.voucher_type = 'Purchase Invoice'
        AND (
            gl.account LIKE '%Asset Received But Not Billed%'
            OR
            gl.account LIKE '%Stock Received But Not Billed%'
        )
        AND gl.posting_date BETWEEN '{from_date}' AND '{to_date}'
        """

        if company:
            stock_asset_conditions += f" AND gl.company = '{company}'"

        # Apply main dimension filter
        main_dimension_values_list = (
            list(heads.keys()) if main_dimension_values else None
        )
        main_dimension_values_filtered = []
        if main_dimension_values_list:
            main_dimension_values_filtered = [
                h for h in main_dimension_values_list if h != "Not Tagged"
            ]

        if main_dimension == "Cost Head" and not has_all_access():
            allowed_heads = get_cost_head_values()
            if allowed_heads:
                if main_dimension_values_filtered:
                    filtered_heads = [
                        h for h in main_dimension_values_filtered if h in allowed_heads
                    ]
                    if filtered_heads:
                        heads_str = "', '".join([str(h) for h in filtered_heads])
                        stock_asset_conditions += (
                            f" AND gl.{main_dimension_fieldname} IN ('{heads_str}')"
                        )
                else:
                    allowed_str = "', '".join(allowed_heads)
                    stock_asset_conditions += (
                        f" AND gl.{main_dimension_fieldname} IN ('{allowed_str}')"
                    )
        elif main_dimension_values_filtered:
            heads_str = "', '".join([str(h) for h in main_dimension_values_filtered])
            if heads_str:
                stock_asset_conditions += (
                    f" AND gl.{main_dimension_fieldname} IN ('{heads_str}')"
                )

        # Apply secondary dimension filter
        secondary_dimension_values_list = [
            h for h in secondary_dimension_list if h != "Not Tagged"
        ]
        if secondary_dimension == "Cost Head" and not has_all_access():
            allowed_heads = get_cost_head_values()
            if allowed_heads:
                if secondary_dimension_values_list:
                    filtered_heads = [
                        h for h in secondary_dimension_values_list if h in allowed_heads
                    ]
                    if filtered_heads:
                        heads_str = "', '".join([str(h) for h in filtered_heads])
                        stock_asset_conditions += f" AND gl.{secondary_dimension_fieldname} IN ('{heads_str}')"
                else:
                    allowed_str = "', '".join(allowed_heads)
                    stock_asset_conditions += (
                        f" AND gl.{secondary_dimension_fieldname} IN ('{allowed_str}')"
                    )
        elif secondary_dimension_values_list:
            heads_str = "', '".join([str(h) for h in secondary_dimension_values_list])
            if heads_str:
                stock_asset_conditions += (
                    f" AND gl.{secondary_dimension_fieldname} IN ('{heads_str}')"
                )

        # Apply additional accounts filter
        if additional_accounts:
            all_accounts = []
            if isinstance(additional_accounts, list):
                all_accounts.extend(additional_accounts)
            else:
                all_accounts.append(additional_accounts)

            if all_accounts:
                acc_str = "', '".join(all_accounts)
                stock_asset_conditions += f" AND gl.account IN ('{acc_str}')"

        # Apply additional dimensions filters
        if additional_dimensions:
            for dim_filter in additional_dimensions:
                if not dim_filter.get("dimension") or not dim_filter.get("values"):
                    continue

                add_dim = dim_filter["dimension"]
                add_values = dim_filter["values"]

                # Skip if same as main or secondary dimension
                if add_dim == main_dimension or add_dim == secondary_dimension:
                    continue

                expanded_values = expand_dimension_values(add_dim, add_values)
                add_dim_field = frappe.scrub(add_dim)
                add_dim_doc = frappe.db.get_value(
                    "Accounting Dimension", {"document_type": add_dim}, "fieldname"
                )
                if add_dim_doc:
                    add_dim_field = add_dim_doc

                if add_dim == "Cost Head" and not has_all_access():
                    allowed_heads = get_cost_head_values()
                    if allowed_heads:
                        filtered_values = [
                            v
                            for v in expanded_values
                            if v != "Not Tagged" and v in allowed_heads
                        ]
                        if filtered_values:
                            values_str = "', '".join([str(v) for v in filtered_values])
                            stock_asset_conditions += (
                                f" AND gl.{add_dim_field} IN ('{values_str}')"
                            )
                else:
                    if expanded_values:
                        values_str = "', '".join(
                            [str(v) for v in expanded_values if v != "Not Tagged"]
                        )
                        if values_str:
                            stock_asset_conditions += (
                                f" AND gl.{add_dim_field} IN ('{values_str}')"
                            )

        if exclude_period_closing:
            stock_asset_conditions += " AND gl.voucher_type != 'Period Closing Voucher'"

        # Add UNION ALL for stock/asset expenses
        query += f"""
    UNION ALL
    SELECT 
        COALESCE(gl.{main_dimension_fieldname}, 'Not Tagged') as main_dim_value,
        COALESCE(gl.{secondary_dimension_fieldname}, 'Not Tagged') as secondary_dim_value,
        'Expense' as root_type,
        SUM(gl.debit) as total_debit,
        SUM(gl.credit) as total_credit
    FROM `tabGL Entry` gl
    JOIN `tabAccount` tac ON tac.name = gl.account
    WHERE {stock_asset_conditions}
    GROUP BY gl.{main_dimension_fieldname}, gl.{secondary_dimension_fieldname}
    """

    gl_data = frappe.db.sql(query, as_dict=True)

    # Optimization: If secondary_dimension_list is empty, extract unique values from GL data
    if not secondary_dimension_list:
        unique_secondary_dims = set()
        for entry in gl_data:
            sec_dim_value = entry.get("secondary_dim_value") or "Not Tagged"
            unique_secondary_dims.add(sec_dim_value)

        if unique_secondary_dims:
            expanded_values = expand_dimension_values(
                secondary_dimension, list(unique_secondary_dims)
            )
            secondary_dimension_list = list(expanded_values)
        else:
            secondary_dimension_list = []

    # Initialize heads with secondary dimension columns
    # Track adjustment types for creating separate columns
    all_adjustment_types = set()

    for head_name in heads.keys():
        for sec_dim_value in secondary_dimension_list:
            if sec_dim_value not in heads[head_name]["secondary_dims"]:
                heads[head_name]["secondary_dims"][sec_dim_value] = {
                    "income": 0.0,
                    "expense": 0.0,
                    "net": 0.0,
                    "adjustments": {},  # Store adjustments per type
                }

    # Check if there's any "Not Tagged" data in secondary dimension
    has_not_tagged_secondary = any(
        (entry.get("secondary_dim_value") or "Not Tagged") == "Not Tagged"
        for entry in gl_data
    )

    if has_not_tagged_secondary and "Not Tagged" not in secondary_dimension_list:
        secondary_dimension_list.append("Not Tagged")
        for head_name in heads.keys():
            heads[head_name]["secondary_dims"]["Not Tagged"] = {
                "income": 0.0,
                "expense": 0.0,
                "net": 0.0,
                "adjustments": {},
            }

    # Process GL data into secondary dimension columns
    for entry in gl_data:
        main_dim_value = entry.get("main_dim_value") or "Not Tagged"
        secondary_dim_value = entry.get("secondary_dim_value") or "Not Tagged"

        if (
            main_dim_value in heads
            and secondary_dim_value in heads[main_dim_value]["secondary_dims"]
        ):
            # Process data for all nodes (including groups that have their own data)
            # Groups will be filtered out later if render_as_tree_view is false
            if entry.root_type == "Income":
                amount = int((entry.total_credit or 0) - (entry.total_debit or 0))
                heads[main_dim_value]["secondary_dims"][secondary_dim_value][
                    "income"
                ] += amount
                heads[main_dim_value]["secondary_dims"][secondary_dim_value][
                    "net"
                ] += amount
            elif entry.root_type in ["Expense", "Asset", "Liability"]:
                amount = int((entry.total_debit or 0) - (entry.total_credit or 0))
                heads[main_dim_value]["secondary_dims"][secondary_dim_value][
                    "expense"
                ] += amount
                heads[main_dim_value]["secondary_dims"][secondary_dim_value][
                    "net"
                ] -= amount

    # Process adjustment data if enabled
    if include_adjustment:
        # Build adjustment conditions
        adj_conditions = "ia.docstatus = 1"

        if from_date and to_date:
            adj_conditions += (
                f" AND ia.posting_date BETWEEN '{from_date}' AND '{to_date}'"
            )

        # if company:
        #     adj_conditions += f" AND ia.company = '{company}'"

        # Main dimension filter
        main_dimension_values_list = (
            list(heads.keys()) if main_dimension_values else None
        )
        main_dimension_values_filtered = []
        if main_dimension_values_list:
            main_dimension_values_filtered = [
                h for h in main_dimension_values_list if h != "Not Tagged"
            ]

        if main_dimension == "Cost Head" and not has_all_access():
            allowed_heads = get_cost_head_values()
            if allowed_heads:
                if main_dimension_values_filtered:
                    filtered_heads = [
                        h for h in main_dimension_values_filtered if h in allowed_heads
                    ]
                    if filtered_heads:
                        heads_str = "', '".join([str(h) for h in filtered_heads])
                        adj_conditions += (
                            f" AND iai.{main_dimension_fieldname} IN ('{heads_str}')"
                        )
                else:
                    allowed_str = "', '".join(allowed_heads)
                    adj_conditions += (
                        f" AND iai.{main_dimension_fieldname} IN ('{allowed_str}')"
                    )
        elif main_dimension_values_filtered:
            heads_str = "', '".join([str(h) for h in main_dimension_values_filtered])
            if heads_str:
                adj_conditions += (
                    f" AND iai.{main_dimension_fieldname} IN ('{heads_str}')"
                )

        # Secondary dimension filter (only if values provided)
        if secondary_dimension_list:
            secondary_values_filtered = [
                h for h in secondary_dimension_list if h != "Not Tagged"
            ]
            if secondary_dimension == "Cost Head" and not has_all_access():
                allowed_heads = get_cost_head_values()
                if allowed_heads:
                    if secondary_values_filtered:
                        filtered_heads = [
                            h for h in secondary_values_filtered if h in allowed_heads
                        ]
                        if filtered_heads:
                            heads_str = "', '".join([str(h) for h in filtered_heads])
                            adj_conditions += f" AND iai.{secondary_dimension_fieldname} IN ('{heads_str}')"
            elif secondary_values_filtered:
                heads_str = "', '".join([str(h) for h in secondary_values_filtered])
                if heads_str:
                    adj_conditions += (
                        f" AND iai.{secondary_dimension_fieldname} IN ('{heads_str}')"
                    )

        # Additional accounts filter
        if additional_accounts:
            all_accounts = []
            if isinstance(additional_accounts, list):
                all_accounts.extend(additional_accounts)
            else:
                all_accounts.append(additional_accounts)

            if all_accounts:
                acc_str = "', '".join(all_accounts)
                adj_conditions += f" AND iai.account IN ('{acc_str}')"

        # Additional dimensions filters
        if additional_dimensions:
            for dim_filter in additional_dimensions:
                if not dim_filter.get("dimension") or not dim_filter.get("values"):
                    continue

                add_dim = dim_filter["dimension"]
                add_values = dim_filter["values"]

                if add_dim == main_dimension or add_dim == secondary_dimension:
                    continue

                expanded_values = expand_dimension_values(add_dim, add_values)
                add_dim_field = frappe.scrub(add_dim)
                add_dim_doc = frappe.db.get_value(
                    "Accounting Dimension", {"document_type": add_dim}, "fieldname"
                )
                if add_dim_doc:
                    add_dim_field = add_dim_doc

                if add_dim == "Cost Head" and not has_all_access():
                    allowed_heads = get_cost_head_values()
                    if allowed_heads:
                        filtered_values = [
                            v
                            for v in expanded_values
                            if v != "Not Tagged" and v in allowed_heads
                        ]
                        if filtered_values:
                            values_str = "', '".join([str(v) for v in filtered_values])
                            adj_conditions += (
                                f" AND iai.{add_dim_field} IN ('{values_str}')"
                            )
                else:
                    if expanded_values:
                        values_str = "', '".join(
                            [str(v) for v in expanded_values if v != "Not Tagged"]
                        )
                        if values_str:
                            adj_conditions += (
                                f" AND iai.{add_dim_field} IN ('{values_str}')"
                            )

        # Filter by adjustment type if specified
        if internal_adjustment_type:
            if isinstance(internal_adjustment_type, list):
                adj_types_str = "', '".join(internal_adjustment_type)
                adj_conditions += f" AND ia.type IN ('{adj_types_str}')"
            else:
                adj_conditions += f" AND ia.type = '{internal_adjustment_type}'"

        # Fetch adjustment data (include adjustment_type for separate columns)
        adj_query = f"""
        SELECT 
            COALESCE(iai.{main_dimension_fieldname}, 'Not Tagged') as main_dim_value,
            COALESCE(iai.{secondary_dimension_fieldname}, 'Not Tagged') as secondary_dim_value,
            ia.type as adjustment_type,
            CAST(COALESCE(SUM(CASE WHEN ia.adjustment_for = 'Income' THEN iai.credit - iai.debit ELSE 0 END), 0) AS SIGNED) AS total_inc,
            CAST(COALESCE(SUM(CASE WHEN ia.adjustment_for = 'Expense' THEN iai.debit - iai.credit ELSE 0 END), 0) AS SIGNED) AS total_exp
        FROM `tabInternal Adjustment` ia
        JOIN `tabInternal Adjustment Detail` iai ON iai.parent = ia.name
        WHERE {adj_conditions}
        GROUP BY iai.{main_dimension_fieldname}, iai.{secondary_dimension_fieldname}, ia.type
        """

        adjustment_data = frappe.db.sql(adj_query, as_dict=True)

        # If discovering secondary dimensions, extract from adjustment data too
        if not secondary_dimension_values:
            unique_adj_secondary_dims = set()
            for adj_entry in adjustment_data:
                sec_dim_value = adj_entry.get("secondary_dim_value") or "Not Tagged"
                unique_adj_secondary_dims.add(sec_dim_value)

            if unique_adj_secondary_dims:
                expanded_adj_values = expand_dimension_values(
                    secondary_dimension, list(unique_adj_secondary_dims)
                )
                existing_set = set(secondary_dimension_list)
                for val in expanded_adj_values:
                    if val not in existing_set:
                        secondary_dimension_list.append(val)
                        existing_set.add(val)

        # Initialize any new secondary dimensions found in adjustments
        for head_name in heads.keys():
            for sec_dim_value in secondary_dimension_list:
                if sec_dim_value not in heads[head_name]["secondary_dims"]:
                    heads[head_name]["secondary_dims"][sec_dim_value] = {
                        "income": 0.0,
                        "expense": 0.0,
                        "net": 0.0,
                        "adjustments": {},
                    }

        # Check for "Not Tagged" in adjustments
        has_not_tagged_adj_secondary = any(
            (adj_entry.get("secondary_dim_value") or "Not Tagged") == "Not Tagged"
            for adj_entry in adjustment_data
        )

        if (
            has_not_tagged_adj_secondary
            and "Not Tagged" not in secondary_dimension_list
        ):
            secondary_dimension_list.append("Not Tagged")
            for head_name in heads.keys():
                heads[head_name]["secondary_dims"]["Not Tagged"] = {
                    "income": 0.0,
                    "expense": 0.0,
                    "net": 0.0,
                    "adjustments": {},
                }

        # Process adjustment data (store per adjustment type)
        for adj_entry in adjustment_data:
            main_dim_value = adj_entry.get("main_dim_value") or "Not Tagged"
            secondary_dim_value = adj_entry.get("secondary_dim_value") or "Not Tagged"
            adjustment_type = adj_entry.get("adjustment_type")

            if (
                main_dim_value in heads
                and secondary_dim_value in heads[main_dim_value]["secondary_dims"]
            ):
                # Process adjustment data for all nodes (including groups that have their own data)
                # Groups will be filtered out later if render_as_tree_view is false
                total_inc = int(adj_entry.get("total_inc", 0) or 0)
                total_exp = int(adj_entry.get("total_exp", 0) or 0)

                # Add to total income/expense
                heads[main_dim_value]["secondary_dims"][secondary_dim_value][
                    "income"
                ] += total_inc
                heads[main_dim_value]["secondary_dims"][secondary_dim_value][
                    "expense"
                ] += total_exp
                heads[main_dim_value]["secondary_dims"][secondary_dim_value]["net"] += (
                    total_inc - total_exp
                )

                # Store per adjustment type for separate columns
                if adjustment_type:
                    all_adjustment_types.add(adjustment_type)
                    if (
                        "adjustments"
                        not in heads[main_dim_value]["secondary_dims"][
                            secondary_dim_value
                        ]
                    ):
                        heads[main_dim_value]["secondary_dims"][secondary_dim_value][
                            "adjustments"
                        ] = {}

                    if (
                        adjustment_type
                        not in heads[main_dim_value]["secondary_dims"][
                            secondary_dim_value
                        ]["adjustments"]
                    ):
                        heads[main_dim_value]["secondary_dims"][secondary_dim_value][
                            "adjustments"
                        ][adjustment_type] = {"income": 0.0, "expense": 0.0}

                    heads[main_dim_value]["secondary_dims"][secondary_dim_value][
                        "adjustments"
                    ][adjustment_type]["income"] += total_inc
                    heads[main_dim_value]["secondary_dims"][secondary_dim_value][
                        "adjustments"
                    ][adjustment_type]["expense"] += total_exp

    # Accumulate parent values for tree structure (main dimension)
    if frappe.get_meta(main_dimension).is_tree and render_as_tree_view:
        parent_field = f"parent_{frappe.scrub(main_dimension)}"

        # Sort by lft descending to process children first
        sorted_heads = sorted(
            [(name, data) for name, data in heads.items() if name != "Not Tagged"],
            key=lambda x: x[1].get("lft", 0),
            reverse=True,
        )

        for head_name, head_data in sorted_heads:
            parent = head_data.get(parent_field)
            if parent and parent in heads:
                for sec_dim_value in secondary_dimension_list:
                    if sec_dim_value in heads[head_name]["secondary_dims"]:
                        # Accumulate income, expense, net
                        for key in ["income", "expense", "net"]:
                            if sec_dim_value in heads[parent]["secondary_dims"]:
                                heads[parent]["secondary_dims"][sec_dim_value][
                                    key
                                ] += heads[head_name]["secondary_dims"][sec_dim_value][
                                    key
                                ]

                        # Accumulate adjustments per type
                        if (
                            "adjustments"
                            in heads[head_name]["secondary_dims"][sec_dim_value]
                        ):
                            if (
                                "adjustments"
                                not in heads[parent]["secondary_dims"][sec_dim_value]
                            ):
                                heads[parent]["secondary_dims"][sec_dim_value][
                                    "adjustments"
                                ] = {}

                            for adj_type, adj_values in heads[head_name][
                                "secondary_dims"
                            ][sec_dim_value]["adjustments"].items():
                                if (
                                    adj_type
                                    not in heads[parent]["secondary_dims"][
                                        sec_dim_value
                                    ]["adjustments"]
                                ):
                                    heads[parent]["secondary_dims"][sec_dim_value][
                                        "adjustments"
                                    ][adj_type] = {"income": 0.0, "expense": 0.0}
                                heads[parent]["secondary_dims"][sec_dim_value][
                                    "adjustments"
                                ][adj_type]["income"] += adj_values.get("income", 0)
                                heads[parent]["secondary_dims"][sec_dim_value][
                                    "adjustments"
                                ][adj_type]["expense"] += adj_values.get("expense", 0)

    # Convert to list and flatten secondary dimensions into columns
    result = []
    for head_name, head_data in heads.items():
        row = {
            "name": head_name,
            "indent": head_data.get("indent", 0),
            "is_group": head_data.get("is_group", 0),
            "lft": head_data.get("lft", 0),
        }

        # Add secondary dimension columns (always show income, expense, and net)
        # Also add adjustment type columns per secondary dimension
        for sec_dim_value in secondary_dimension_list:
            if sec_dim_value in head_data["secondary_dims"]:
                sec_dim_data = head_data["secondary_dims"][sec_dim_value]
                # Use secondary dimension value as key (sanitize for column name)
                sec_key = (
                    frappe.scrub(sec_dim_value)
                    if sec_dim_value != "Not Tagged"
                    else "not_tagged"
                )
                row[f"{sec_key}_inc"] = sec_dim_data["income"]
                row[f"{sec_key}_exp"] = sec_dim_data["expense"]
                row[f"{sec_key}_net"] = sec_dim_data["net"]

                # Add adjustment type columns for this secondary dimension
                if "adjustments" in sec_dim_data and sec_dim_data["adjustments"]:
                    for adj_type, adj_values in sec_dim_data["adjustments"].items():
                        adj_type_scrubbed = frappe.scrub(adj_type)
                        row[f"{sec_key}_{adj_type_scrubbed}_inc"] = adj_values.get(
                            "income", 0
                        )
                        row[f"{sec_key}_{adj_type_scrubbed}_exp"] = adj_values.get(
                            "expense", 0
                        )

        result.append(row)

    # Sort by lft for tree display (always sort by lft if tree dimension)
    if frappe.get_meta(main_dimension).is_tree:
        result = sorted(result, key=lambda x: x.get("lft", 0))

        # If not rendering as tree, remove parent groups (keep only leaf nodes) and reset indents
        if not render_as_tree_view:
            # Filter out groups, but keep groups that have their own data (not just from children)
            # A group has its own data if it has non-zero values in any secondary dimension
            filtered_result = []
            for row in result:
                # Check if this is a group
                if row.get("is_group") == 1:
                    # Check if group has its own data (not just aggregated from children)
                    has_own_data = False
                    for key, value in row.items():
                        # Skip non-numeric metadata fields
                        if key in ["name", "indent", "is_group", "lft", "rgt"]:
                            continue
                        # Check if field is amount-related
                        if (
                            key.endswith("_inc")
                            or key.endswith("_exp")
                            or key.endswith("_net")
                        ):
                            if isinstance(value, (int, float)) and value != 0:
                                has_own_data = True
                                break

                    # Only include group if it has its own data
                    if not has_own_data:
                        continue

                # Reset indent for all rows when not rendering as tree
                row["indent"] = 0
                filtered_result.append(row)

            result = filtered_result

    # Note: Empty row filtering is now done in the frontend

    # Add secondary dimension metadata to response
    secondary_metadata = {
        "secondary_dimensions": [
            {
                "key": (
                    frappe.scrub(sec_dim) if sec_dim != "Not Tagged" else "not_tagged"
                ),
                "label": sec_dim,
                "value": sec_dim,
            }
            for sec_dim in secondary_dimension_list
        ],
        "has_secondary_dimensions": True,
    }

    return {"data": result, "metadata": secondary_metadata}
