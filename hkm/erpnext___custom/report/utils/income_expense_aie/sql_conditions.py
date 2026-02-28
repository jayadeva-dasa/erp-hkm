# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe

from .dimension_utils import get_heads


def get_common_condition(
    account=None,
    heads=None,
    from_date=None,
    to_date=None,
    prefix="gl",
    dimension_meta=None,
):
    """Get common SQL conditions for filtering"""
    heads_condition = ""
    account_condition = ""

    head_sql_fields = frappe.scrub(dimension_meta.name)

    if heads:
        if isinstance(heads, list):
            if len(heads) > 1:
                heads = ", ".join(f"'{s}'" for s in heads)
                heads_condition = f" AND {prefix}.{head_sql_fields} IN ({heads})"
            else:
                heads_condition = f" AND {prefix}.{head_sql_fields} = '{heads[0]}'"
        else:
            heads_condition = f" AND {prefix}.{head_sql_fields} = '{heads}'"

    if account:
        if isinstance(account, list):
            if len(account) > 1:
                account = ", ".join(f"'{s}'" for s in account)
                account_condition = f" AND {prefix}.account IN ({account})"
            else:
                account_condition = f" AND {prefix}.account = '{account[0]}'"
        else:
            account_condition = f" AND {prefix}.account = '{account}'"
    else:
        account_condition = ""

    conditions = ""
    if prefix == "gl":
        if from_date:
            conditions += f" AND {prefix}.posting_date >= %(from_date)s"
        if to_date:
            conditions += f" AND {prefix}.posting_date <= %(to_date)s"

    return heads_condition + account_condition + conditions


def get_ie_gl_sql_conditions(
    account=None,
    from_date=None,
    to_date=None,
    include_stock_asset=None,
    dimension_value=None,
    dimension_meta=None,
):

    heads = get_heads(dimension_meta, dimension_value, detailed=False)
    """Get GL SQL conditions for Income/Expense entries"""
    conditions = """
    WHERE gl.is_cancelled = 0
        AND tac.report_type = 'Profit and Loss'
        AND tac.root_type IN ('Income', 'Expense')
    """

    if include_stock_asset:
        conditions += """
        AND NOT (
                (tac.root_type = 'Expense' AND gl.against LIKE '%%Stock In Hand%%')
                OR
                (tac.root_type = 'Expense' AND tac.account_type = 'Depreciation' AND tac.name LIKE '%%Depreciation%%')
            )
        """

    return conditions + get_common_condition(
        account=account,
        heads=heads,
        from_date=from_date,
        to_date=to_date,
        dimension_meta=dimension_meta,
    )


def get_al_gl_sql_conditions(
    account=None,
    from_date=None,
    to_date=None,
    include_stock_asset=None,
    dimension_value=None,
    dimension_meta=None,
):
    """Get GL asset liability common condition"""
    heads = get_heads(dimension_meta, dimension_value, detailed=False)
    conditions = """
    WHERE gl.is_cancelled = 0
        AND tac.report_type = 'Balance Sheet'
        AND gl.voucher_type = 'Purchase Invoice'
        AND (
                gl.against LIKE '%%Asset Received But Not Billed%%'
                OR
                gl.account LIKE '%%Stock Received But Not Billed%%'
            )
    """
    
    # if include_stock_asset:
    #     conditions += """
    #     AND NOT (
    #             (tac.root_type = 'Expense' AND gl.against LIKE '%%Stock In Hand%%')
    #             OR
    #             (tac.root_type = 'Expense' AND tac.account_type = 'Depreciation' AND tac.name LIKE '%%Depreciation%%')
    #         )
    #     """

    return conditions + get_common_condition(
        account=account,
        heads=heads,
        from_date=from_date,
        to_date=to_date,
        dimension_meta=dimension_meta,
    )


def get_ie_adjustment_sql_conditions(
    account=None,
    from_date=None,
    to_date=None,
    dimension_value=None,
    dimension_meta=None,
    adjustment_type=None,
):
    def get_adjustment_type(adjustment_type):
        if isinstance(adjustment_type, list):
            if len(adjustment_type) > 1:
                adjustment_type = ", ".join(f"'{s}'" for s in adjustment_type)
                return f" AND ia.type IN ({adjustment_type})"
            else:
                return f" AND ia.type = '{adjustment_type[0]}'"
        else:
            return f" AND ia.type = '{adjustment_type}'"
    
    """Get adjustment SQL conditions"""
    heads = get_heads(dimension_meta, dimension_value, detailed=False)

    conditions = "WHERE ia.docstatus = 1"

    if from_date:
        conditions += " AND ia.posting_date >= %(from_date)s"
    if to_date:
        conditions += " AND ia.posting_date <= %(to_date)s"
        
    if adjustment_type:
        adj_type = get_adjustment_type(adjustment_type)
        conditions += adj_type

    return conditions + get_common_condition(
        account=account, heads=heads, prefix="iai", dimension_meta=dimension_meta
    )


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
