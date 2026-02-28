import frappe

from hkm.erpnext___custom.report.hkm_eagle_view.utils.constants import ALL_ACCESS_ROLE
from hkm.erpnext___custom.report.hkm_eagle_view.utils.query_optimizer import DimensionQueryOptimizer


def get_proper_heads(dimension_meta, selected_head):
    if not selected_head or not any(selected_head):
        return []

    if len(selected_head) == 1:
        return selected_head

    if dimension_meta.is_tree:
        # Build a set of all descendants of selected heads
        all_descendants = set()
        for head in selected_head:
            descendants = frappe.db.get_descendants(dimension_meta.name, head) or []
            all_descendants.update(descendants)

        # Filter out heads that are descendants of any other head in the list
        proper_heads = [h for h in selected_head if h not in all_descendants]

        return proper_heads

    else:
        return selected_head


def get_formatted_sql_heads(heads):
    if isinstance(heads, list):
        if len(heads) > 1:
            heads = ", ".join(f"'{s}'" for s in heads)
            return f" AND name IN ({heads})"
        else:
            return f" AND name = '{heads[0]}'"
    else:
        return f" AND name = '{heads}'"


def get_child_nodes(dimension_meta, selected_head, include_disabled_dimension=False):
    condition = ""
    disabled_filter = {}

    if not include_disabled_dimension:
        if dimension_meta.has_field("disabled"):
            disabled_filter = {"disabled": 0}
            condition = "WHERE disabled = 0"
        elif dimension_meta.has_field("enabled"):
            disabled_filter = {"enabled": 1}
            condition = "WHERE enabled = 1"
        else:
            disabled_filter = {}
            condition = ""

    if not selected_head or not any(selected_head):
        if not dimension_meta.is_tree:
            return frappe.db.get_list(
                dimension_meta.name, filters=disabled_filter, pluck="name"
            )
        else:
            return frappe.db.sql_list(
                f"""
                    SELECT name 
                     FROM `tab{dimension_meta.name}`
                     {condition}
                     AND rgt = lft + 1
                    """
            )
    else:
        if dimension_meta.is_tree:
            children = []
            for d in selected_head:
                children.extend(
                    get_descendants_of(
                        dimension_meta.name,
                        d,
                        additional_filters=disabled_filter,
                    )
                )
            disabled_filter.update({"name": ["in", selected_head]})
            children.extend(
                frappe.get_all(
                    dimension_meta.name, filters=disabled_filter, pluck="name"
                )
            )
            condition += get_formatted_sql_heads(selected_head)
            return frappe.db.sql_list(
                f"""
                    SELECT name 
                     FROM `tab{dimension_meta.name}`
                     {condition}
                     AND rgt = lft + 1
                    """
            )
        else:
            return [selected_head]


def get_descendants_of(
    doctype,
    name,
    order_by="lft desc",
    limit=None,
    ignore_permissions=False,
    additional_filters=None,
    pluck=True,
    pluck_field="name",
):

    if not frappe.db.exists(doctype, name):
        return []
    lft, rgt = frappe.db.get_value(doctype, name, ["lft", "rgt"])

    if rgt - lft <= 1:
        return []

    filters = {"lft": [">", lft], "rgt": ["<", rgt]}
    if additional_filters:
        filters.update(additional_filters)

    if pluck:
        return frappe.get_list(
            doctype,
            filters=filters,
            order_by=order_by,
            limit_page_length=limit,
            ignore_permissions=ignore_permissions,
            pluck=pluck_field,
        )
    else:
        return frappe.get_list(
            doctype,
            filters=filters,
            order_by=order_by,
            fields=pluck_field if isinstance(pluck_field, list) else [pluck_field],
            limit_page_length=limit,
            ignore_permissions=ignore_permissions,
        )


def get_heads(
    dimension_meta, selected_head, detailed=True, include_disabled_dimension=False
):
    from hkm.erpnext___custom.report.hkm_eagle_view.utils.sql_conditions import (
        get_cost_head_values,
    )

    heads = {}
    actual_heads = []
    disabled_filter = {}

    detailed_fields = [
        "name",
        "parent_" + frappe.scrub(dimension_meta.name),
        "lft",
        "rgt",
        "is_group",
    ]

    # Ensure selected_head is a list
    if isinstance(selected_head, str):
        selected_head = [selected_head]
    elif selected_head is None:
        selected_head = []

    if not include_disabled_dimension:
        if dimension_meta.has_field("disabled"):
            disabled_filter = {"disabled": 0}
        elif dimension_meta.has_field("enabled"):
            disabled_filter = {"enabled": 1}
        else:
            disabled_filter = {}

    if not selected_head or not any(selected_head):

        if detailed:

            if dimension_meta.is_tree:
           
                actual_heads = frappe.get_all(
                    dimension_meta.name,
                    filters=disabled_filter,
                    fields=detailed_fields,
                )
                
                actual_heads = sorted(actual_heads, key=lambda d: d["lft"])

                user_roles = frappe.get_roles(frappe.session.user)
                have_role = any(role in ALL_ACCESS_ROLE for role in user_roles)

                if not have_role and dimension_meta.name == "Cost Head":
                    allowed_heads = get_cost_head_values()
                    actual_heads = [
                        head for head in actual_heads if head.name in allowed_heads
                    ]
                
                # frappe.errprint(attach_indent_to_heads(dimension_meta, actual_heads))
                return attach_indent_to_heads(dimension_meta, actual_heads)
            else:
                return {
                    d: {"name": d}
                    for d in frappe.db.get_list(
                        dimension_meta.name, filters=disabled_filter, pluck="name"
                    )
                }
        else:
            return frappe.db.get_list(
                dimension_meta.name, filters=disabled_filter, pluck="name"
            )

    if detailed:
        if dimension_meta.is_tree:
            # OPTIMIZATION: Use batch query instead of N+1 queries (Issue 1.1 fix)
            all_nodes = DimensionQueryOptimizer.get_all_descendants_batch(
                dimension_meta,
                selected_head,
                detailed_fields,
                include_disabled_dimension
            )
            return attach_indent_to_heads(dimension_meta, all_nodes, selected_head)
        else:
            return {d: {"name": d} for d in selected_head}
    else:
        if dimension_meta.is_tree:
            children = []
            for d in selected_head:
                children.extend(
                    get_descendants_of(
                        dimension_meta.name,
                        d,
                        additional_filters=disabled_filter,
                    )
                )
            disabled_filter.update({"name": ["in", selected_head]})
            children.extend(
                frappe.get_all(
                    dimension_meta.name,
                    filters=disabled_filter,
                    pluck="name",
                )
            )
            return children
        else:
            return selected_head


def attach_indent_to_heads(dimension_meta, actual_heads, selected_head=None, depth=20):
    """Attach indentation to heads for tree display"""

 


    # Parent fields use scrubbed doctype name, not fieldname
    parent_field = "parent_" + frappe.scrub(dimension_meta.name)
    parent_children_map = {}
    heads_by_name = {}

   
    

    for d in actual_heads:
        heads_by_name[d.name] = d
        parent = d.get(parent_field)
        
        # Normalize empty string to None (root node) - Issue 3.1 fix
        if parent == '':
            parent = None
            d[parent_field] = None  # Normalize in the data itself
            
        parent_children_map.setdefault(parent, []).append(d)

    refactored_heads = []

  

    def add_to_list(parent, level):
        if level >= depth:
            return
        children = parent_children_map.get(parent, [])
        children = sorted(children, key=lambda x: x.get("lft", 0))

        for child in children:
            child["indent"] = level
            refactored_heads.append(child)
            add_to_list(child["name"], level + 1)


    
    if not selected_head:
        add_to_list(None, 0)
    else:
        for head in selected_head:
            if head in heads_by_name:
                heads_by_name[head]["indent"] = 0
                refactored_heads.append(heads_by_name[head])
                add_to_list(head, 1)

    user_roles = frappe.get_roles(frappe.session.user)
    have_role = any(role in ALL_ACCESS_ROLE for role in user_roles)
    if dimension_meta.name == "Cost Head" and not have_role and not selected_head:

        parent_heads = get_proper_heads(dimension_meta, [h.name for h in actual_heads])

        for head in parent_heads:
            if head in heads_by_name:
                heads_by_name[head]["indent"] = 0
                refactored_heads.append(heads_by_name[head])
                add_to_list(head, 1)

    return {r["name"]: r for r in refactored_heads}
