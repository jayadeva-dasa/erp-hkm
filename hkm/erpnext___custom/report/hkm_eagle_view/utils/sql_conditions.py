# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe
from typing import Tuple, Dict, List, Optional

from .dimension_utils import get_heads
from .query_optimizer import QueryParameterBuilder
from hkm.erpnext___custom.report.hkm_eagle_view.utils.constants import ALL_ACCESS_ROLE


def get_cost_head_values():
    # user = "rgvd@hkmjaipur.org"
    user = frappe.session.user
    # Get all Cost Heads linked to user
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
        child_nodes = get_heads(dimension_meta, c, detailed=False)
        if child_nodes:
            all_heads.extend(child_nodes)

    return all_heads


def get_common_condition(
    account=None,
    heads=None,
    from_date=None,
    to_date=None,
    prefix="gl",
    dimension_meta=None,
    permission_cache=None,  # NEW: Accept permission cache to avoid repeated checks
) -> Tuple[str, Dict]:
    """
    Get common SQL conditions for filtering (with parameterized queries).
    
    Returns:
        Tuple of (condition_string, parameters_dict)
    
    SECURITY: Uses parameterized queries to prevent SQL injection (Issue 4.1 fix)
    PERFORMANCE: Uses permission cache to avoid repeated role checks (Issue 1.2 fix)
    """
    conditions = []
    params = {}

    # Get the correct fieldname from Accounting Dimension doctype
    head_sql_fields = frappe.db.get_value(
        "Accounting Dimension", 
        {"document_type": dimension_meta.name}, 
        "fieldname"
    )
    if not head_sql_fields:
        head_sql_fields = frappe.scrub(dimension_meta.name)

    # Handle heads with parameterized query
    if heads:
        if isinstance(heads, str):
            heads = [heads]
        
        if heads:
            heads_condition, heads_params = QueryParameterBuilder.build_in_condition(
                f"{prefix}.{head_sql_fields}", heads, "head"
            )
            conditions.append(heads_condition)
            params.update(heads_params)

    # Handle account with parameterized query
    if account:
        if isinstance(account, str):
            account = [account]
        
        if account:
            account_condition, account_params = QueryParameterBuilder.build_in_condition(
                f"{prefix}.account", account, "account"
            )
            conditions.append(account_condition)
            params.update(account_params)

    # Handle date range
    if from_date and to_date and prefix != "iai":
        date_condition, date_params = QueryParameterBuilder.build_date_range_condition(
            f"{prefix}.posting_date", from_date, to_date
        )
        conditions.append(date_condition)
        params.update(date_params)

    # OPTIMIZATION: Use permission cache if provided (Issue 1.2 fix)
    if permission_cache:
        have_role = permission_cache.has_all_access
        if not have_role and dimension_meta.name == "Cost Head":
            allowed_heads = permission_cache.allowed_cost_heads
        else:
            allowed_heads = None
    else:
        # Fallback to direct check if no cache provided
        user_roles = frappe.get_roles(frappe.session.user)
        have_role = any(role in ALL_ACCESS_ROLE for role in user_roles)
        allowed_heads = get_cost_head_values() if not have_role and dimension_meta.name == "Cost Head" else None

    # Handle permission-based filtering
    if not have_role and dimension_meta.name == "Cost Head":
        if not allowed_heads:
            frappe.throw(
                "You are not authorized to view any Cost Head. Please set value in Cost Head Concerned Person."
            )
        
        if not heads:
            # User didn't specify heads, use allowed heads
            perm_condition, perm_params = QueryParameterBuilder.build_in_condition(
                f"{prefix}.{head_sql_fields}", allowed_heads, "perm_head"
            )
            conditions.append(perm_condition)
            params.update(perm_params)
        else:
            # Verify user is authorized for requested heads
            if any(head not in allowed_heads for head in (heads if isinstance(heads, list) else [heads])):
                frappe.throw("You are not authorized to view the selected Cost Head(s)")

    # Combine all conditions
    condition_str = " AND " + " AND ".join(conditions) if conditions else ""
    return condition_str, params


def get_ie_gl_sql_conditions(
    account=None,
    from_date=None,
    to_date=None,
    include_stock_asset=None,
    dimension_value=None,
    dimension_meta=None,
    include_disabled_dimension=False,
    exclude_period_closing_entries=False,
    company=None,
    permission_cache=None,
) -> Tuple[str, Dict]:
    """Get GL SQL conditions for Income/Expense entries with parameterized queries"""
    heads = None
    if dimension_value:
        heads = get_heads(
            dimension_meta,
            dimension_value,
            detailed=False,
            include_disabled_dimension=include_disabled_dimension,
        )
    
    conditions = """
    WHERE gl.is_cancelled = 0
        AND tac.report_type = 'Profit and Loss'
        AND tac.root_type IN ('Income', 'Expense')
    """
    params = {}

    if company:
        conditions += " AND gl.company = %(company)s"
        params["company"] = company

    if include_stock_asset:
        conditions += """
         AND NOT (
            (
                tac.root_type = 'Expense'
                AND gl.against LIKE '%%Stock In Hand%%'
            )
            OR
            (
                tac.root_type = 'Expense'
                AND tac.account_type = 'Depreciation'
                AND tac.name LIKE '%%Depreciation%%'
            )
        )
        AND NOT (
            tac.root_type = 'Expense'
            AND gl.voucher_type = 'Stock Entry'
            )

        """

    if exclude_period_closing_entries:
        conditions += """
        AND gl.voucher_type != 'Period Closing Voucher'
        """

    common_cond, common_params = get_common_condition(
        account=account,
        heads=heads,
        from_date=from_date,
        to_date=to_date,
        dimension_meta=dimension_meta,
        permission_cache=permission_cache,
    )
    
    params.update(common_params)
    return conditions + common_cond, params


def get_al_gl_sql_conditions(
    account=None,
    from_date=None,
    to_date=None,
    include_stock_asset=None,
    dimension_value=None,
    dimension_meta=None,
    include_disabled_dimension=False,
    exclude_period_closing_entries=False,
    company=None,
    permission_cache=None,
) -> Tuple[str, Dict]:
    """Get GL asset liability conditions with parameterized queries"""
    heads = None
    if dimension_value:
        heads = get_heads(
            dimension_meta,
            dimension_value,
            detailed=False,
            include_disabled_dimension=include_disabled_dimension,
        )
    
    conditions = """
    WHERE gl.is_cancelled = 0
        AND tac.report_type = 'Balance Sheet'
        AND gl.voucher_type = 'Purchase Invoice'
        AND (
                gl.account LIKE '%%Asset Received But Not Billed%%'
                OR
                gl.account LIKE '%%Stock Received But Not Billed%%'
            )
    """
    params = {}

    if company:
        conditions += " AND gl.company = %(company)s"
        params["company"] = company

    if exclude_period_closing_entries:
        conditions += """
        AND gl.voucher_type != 'Period Closing Voucher'
        """

    common_cond, common_params = get_common_condition(
        account=account,
        heads=heads,
        from_date=from_date,
        to_date=to_date,
        dimension_meta=dimension_meta,
        permission_cache=permission_cache,
    )
    
    params.update(common_params)
    return conditions + common_cond, params


def get_ie_adjustment_sql_conditions(
    account=None,
    from_date=None,
    to_date=None,
    dimension_value=None,
    dimension_meta=None,
    adjustment_type=None,
    include_disabled_dimension=False,
    permission_cache=None,
) -> Tuple[str, Dict]:
    """Get adjustment SQL conditions with parameterized queries"""
    heads = None
    if dimension_value:
        heads = get_heads(
            dimension_meta,
            dimension_value,
            detailed=False,
            include_disabled_dimension=include_disabled_dimension,
        )
    
    conditions = "WHERE ia.docstatus = 1"
    params = {}

    if from_date and to_date:
        conditions += " AND ia.posting_date BETWEEN %(from_date)s AND %(to_date)s"
        params["from_date"] = from_date
        params["to_date"] = to_date

    if adjustment_type:
        if isinstance(adjustment_type, str):
            adjustment_type = [adjustment_type]
        
        if adjustment_type:
            adj_condition, adj_params = QueryParameterBuilder.build_in_condition(
                "ia.type", adjustment_type, "adj_type"
            )
            conditions += " AND " + adj_condition
            params.update(adj_params)

    common_cond, common_params = get_common_condition(
        account=account, 
        heads=heads, 
        prefix="iai", 
        dimension_meta=dimension_meta,
        permission_cache=permission_cache,
    )
    
    params.update(common_params)
    return conditions + common_cond, params


def get_cost_head_condition(cost_head):
    """Get SQL conditions for cost head filtering"""
    if not cost_head:
        return ""

    all_heads = set()
    for head in cost_head:
        all_heads.add(head)
        all_heads.update(frappe.db.get_descendants("Cost Head", head) or [])

    cost_head_str = ", ".join(f"'{c}'" for c in all_heads if c)
    return f"AND cost_head IN ({cost_head_str})" if cost_head_str else ""


def get_root_type_condition(report_type, adjustment=False):
    """Get adjustment root type condition"""
    from .constants import ONLY_INCOME, ONLY_EXPENSE

    prefix = "ia.adjustment_for" if adjustment else "root_type"

    if report_type == ONLY_INCOME:
        return f"AND {prefix} = 'Income'"
    elif report_type == ONLY_EXPENSE:
        return f"AND {prefix} = 'Expense'"
    else:
        return f"AND ({prefix} = 'Income' OR {prefix} = 'Expense')"
