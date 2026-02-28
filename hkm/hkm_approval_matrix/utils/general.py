"""
Authority management utilities for HKM Approval Matrix.
This module handles all operations related to approving authorities,
including setting, getting, and validating authorities.
"""

import frappe
from .constants import CHILD_TABLE_FIELD, SAFE_GLOBALS
import re


def condition_to_dict(condition_str):
    # Regex to capture key, operator, and value (supports ' ' or " ")
    pattern = r"(\w+)\s*(==|!=|<=|>=|<|>)\s*(?:'([^']*)'|\"([^\"]*)\"|(\d+))"
    matches = re.findall(pattern, condition_str)

    condition_dict = {}
    for match in matches:
        key, op = match[0], match[1]
        value = match[2] or match[3] or match[4]  # pick non-empty capture

        if value.isdigit():
            value = int(value)

        condition_dict[key] = value

    # frappe.errprint(condition_dict)  # debug log
    return condition_dict


def is_transition_condition_satisfied(condition, doc, matrix_dimension, dimension_value) -> bool:
    """Check if a transition condition is satisfied for a document."""
    locals_dict = doc.as_dict()
    dimension_fieldname = frappe.scrub(matrix_dimension) if matrix_dimension else None

    dimension_value = dimension_value or None

    if matrix_dimension and dimension_value:
        dimension_meta = frappe.get_meta(matrix_dimension)

        # Check if dimension value matches
        doc_dimension_value = locals_dict.get(dimension_fieldname)

        # Handle tree-based dimensions (hierarchical check)
        if dimension_meta.is_tree or matrix_dimension == "Cost Head":
            descendants = frappe.db.get_descendants(matrix_dimension, dimension_value)
            if doc_dimension_value not in descendants and doc_dimension_value != dimension_value:
                return False
            # Set the dimension value to the parent for condition evaluation
            locals_dict[dimension_fieldname] = dimension_value
        else:
            # For non-tree dimensions, exact match required
            if doc_dimension_value != dimension_value:
                return False

    # If no additional condition, dimension match is sufficient
    if not condition or not condition.strip():
        return True

    # Evaluate additional conditions
    return frappe.safe_eval(condition, SAFE_GLOBALS, locals_dict)


def get_approving_authority(doctype, docname):
    """Get the approving authorities for a document based on approval matrix conditions."""
    doc = frappe.get_doc(doctype, docname)
    approval_authority = []

    approval_matrices = frappe.get_all(
        "Approval Matrix",
        filters={"target_doctype": doctype},
        fields=["name", "dimension"],
    )

    frappe.errprint(f"approval_matrices {approval_matrices}")
    if not approval_matrices:
        frappe.throw("No approval matrix found for this doctype")

    if len(approval_matrices) > 1:
        frappe.errprint("Multiple approval matrices found for this doctype")
        for matrix in approval_matrices:
            transitions = frappe.get_all(
                "Approval Matrix Detail",
                filters={"parent": matrix.name, "disabled": 0},
                fields=["condition", "approving_authority", "dimension_value"],
                order_by="idx asc",
            )

            for transition in transitions:
                condition = transition.condition
                dimension_value = transition.dimension_value

                if is_transition_condition_satisfied(condition, doc, matrix.dimension, dimension_value):

                    authorities = list(
                        {
                            auth.strip()
                            for auth in transition.approving_authority.strip().split(
                                "\n"
                            )
                            if auth.strip()
                        }
                    )

                    approval_authority.extend(authorities)
                    break

    else:
        transitions = frappe.get_all(
            "Approval Matrix Detail",
            filters={"parent": approval_matrices[0].name, "disabled": 0},
            fields=["condition", "approving_authority", "dimension_value"],
            order_by="idx asc",
        )

        for transition in transitions:
            condition = transition.condition
            dimension_value = transition.dimension_value
            if is_transition_condition_satisfied(
                condition, doc, approval_matrices[0].dimension, dimension_value
            ):
                seen = set()
                authorities_dict = {}
                for idx, auth in enumerate(
                    transition.approving_authority.strip().split("\n"), start=1
                ):
                    auth = auth.strip()
                    if auth and auth not in seen:
                        authorities_dict[idx] = auth
                        seen.add(auth)

                approval_authority = authorities_dict
                break

    if not approval_authority:
        frappe.throw("No transition condition satisfied for approval matrix")

    if isinstance(approval_authority, dict):
        return approval_authority

    return list(set(approval_authority))


def get_current_approving_authority(doctype, docname):
    """Get the current or next pending approving authority for a document."""
    doc = frappe.get_doc(doctype, docname)

    sorted_rows = sorted(
        doc.approving_authorities,
        key=lambda x: (x.idx),
    )

    pending = [row.authority for row in sorted_rows if not row.status]

    if not pending:
        return None

    return pending[0]


def set_approving_authority(doctype, docname):
    """Set approving authorities for a document based on approval matrix rules."""
    doc = frappe.get_doc(doctype, docname)
    approving_authority = get_approving_authority(doctype, docname)
    doc.approving_authorities = []

    authorities = approving_authority
    if isinstance(approving_authority, dict):
        authorities = []
        for idx, auth in approving_authority.items():
            authorities.append(auth)

    users_data = frappe.get_all(
        "User",
        filters={"name": ["in", authorities]},
        fields=["name", "approval_scale"],
    )

    if isinstance(approving_authority, dict):

        user_dict = {user.name: user.approval_scale for user in users_data}
        for idx, auth in approving_authority.items():
            doc.append(
                "approving_authorities",
                {
                    "authority": auth,
                    "approval_scale": user_dict.get(auth, 0),
                    "idx": idx,
                },
            )

    else:

        users_data.sort(key=lambda x: (x.approval_scale or 0, x.name))
        for i, user in enumerate(users_data, start=1):
            doc.append(
                "approving_authorities",
                {
                    "authority": user.name,
                    "approval_scale": user.approval_scale or 0,
                    "idx": i,
                },
            )

    doc.flags.ignore_frozen_transaction = True
    doc.save()
    doc.reload()


def is_doctype_in_approval_matrix(doctype):
    """Check if doctype is configured for approval matrix."""
    return doctype in frappe.get_hooks(
        "approval_matrix_doctypes",
        app_name="hkm",
    )
