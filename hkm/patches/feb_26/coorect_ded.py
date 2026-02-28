
_TEAM_SUFFIX = "-team"
import frappe
from .target_recurrence.query import get_query
from frappe.utils import now_datetime
from frappe.utils.nestedset import rebuild_tree
from datetime import datetime


def _is_script_created_wrapper(initial):
    """
    Return True if this node was created by correct_tree_structure.

    Script-created wrappers end with _TEAM_SUFFIX (e.g. 'BKSD-team').
    Nodes that already had a double-hyphen suffix (e.g. '--team') are not
    touched — that pattern never arises in normal usage.
    """
    if not initial:
        return False
    lower = initial.lower()
    return lower.endswith(_TEAM_SUFFIX) and not lower.endswith("-" + _TEAM_SUFFIX)


def correct_tree_structure():
    """
    Idempotent restructure of DED Devotee tree.

    For every original group node A (not already a script-created wrapper):
        1. Create A-team (group, same parent as A)
        2. Move A's children under A-team
        3. Move child-wrappers (created during recursion) under A-team
        4. Move A itself under A-team and set is_group = 0

    Before:
        A (group)
            ├── B (group)
            │   └── C
            └── D

    After:
        A-team (group)
            ├── A  (non-group)
            ├── B-team (group)
            │   ├── B (non-group)
            │   └── C
            └── D

    Safe to run multiple times — already-structured nodes are skipped.
    """
    if not frappe.db.exists("DocType", "DED Devotee"):
        return
    frappe.db.begin()
    try:
        roots = frappe.get_all(
            "DED Devotee",
            filters={"parent_ded_devotee": ["in", ["", None]]},
            pluck="name",
            order_by="lft",
        )
        for root in roots:
            _traverse_and_restructure(root)

        rebuild_tree("DED Devotee")
        frappe.db.commit()

    except Exception:
        frappe.db.rollback()
        raise


def _traverse_and_restructure(name):
    """Depth-first traversal; wraps group nodes that are not yet wrapped."""
    doc = frappe.get_doc("DED Devotee", name)

    # Snapshot of children BEFORE recursion so we know the original set
    original_children = frappe.get_all(
        "DED Devotee",
        filters={"parent_ded_devotee": name},
        pluck="name",
        order_by="lft",
    )

    # Recurse depth-first — child wrappers are created here
    for child_name in original_children:
        _traverse_and_restructure(child_name)

    # Only group nodes need wrapping
    if not doc.is_group:
        return

    # ── IDEMPOTENCY GUARD 1 ──
    # Nodes created as wrappers by this script end with _TEAM_SUFFIX.
    # Skip them to prevent double-wrapping on a repeat run.
    if _is_script_created_wrapper(doc.initial):
        return

    wrapper_initial = (doc.initial or "") + _TEAM_SUFFIX

    # ── IDEMPOTENCY GUARD 2 ──
    # If wrapper already exists, this node has already been processed.
    if frappe.db.exists("DED Devotee", wrapper_initial):
        return

    # ── Build and insert wrapper document ──
    data = doc.as_dict()
    for field in ("name", "lft", "rgt", "old_parent"):
        data.pop(field, None)
    for row in data.get("periodic_allowances_deductions") or []:
        row.pop("name", None)
        row.pop("owner", None)

    data["initial"] = wrapper_initial
    data["full_name"] = (doc.full_name or "") + " Team"
    data["parent_ded_devotee"] = doc.parent_ded_devotee
    data["is_group"] = 1

    wrapper_doc = frappe.get_doc(data)
    wrapper_doc.insert(ignore_permissions=True)

    # ── Move original children that are STILL directly under this node ──
    # (some may have already been re-parented to their own wrapper during
    # recursion — those should NOT be moved again)
    for child_name in original_children:
        current_parent = frappe.db.get_value(
            "DED Devotee", child_name, "parent_ded_devotee"
        )
        if current_parent == name:
            frappe.db.set_value(
                "DED Devotee",
                child_name,
                "parent_ded_devotee",
                wrapper_doc.name,
                update_modified=False,
            )

    # ── Move child-wrappers created during recursion ──
    # Recursion creates wrapper nodes (e.g. B-team) parented to 'name'.
    # They were NOT in original_children and must be moved to the new wrapper.
    child_wrappers = frappe.get_all(
        "DED Devotee",
        filters={"parent_ded_devotee": name, "is_group": 1},
        pluck="name",
    )
    for cw in child_wrappers:
        if cw == wrapper_doc.name:
            continue  # skip the wrapper we just created
        frappe.db.set_value(
            "DED Devotee",
            cw,
            "parent_ded_devotee",
            wrapper_doc.name,
            update_modified=False,
        )

    # ── Demote the original node under its new wrapper ──
    frappe.db.set_value(
        "DED Devotee",
        doc.name,
        {"parent_ded_devotee": wrapper_doc.name, "is_group": 0},
        update_modified=False,
    )


# ── Preview helper ────────────────────────────────────────────────────────────

def preview_correct_tree():
    """
    Dry-run: print what correct_tree_structure() WOULD do without touching DB.

    Shows:
      [CREATE]  <wrapper_initial>  (group, parent=<parent>)
      [SKIP]    <initial>  — already wrapped / already a wrapper
    """
    rows = frappe.db.sql(
        "SELECT name, initial, full_name, is_group, parent_ded_devotee, lft "
        "FROM `tabDED Devotee` ORDER BY lft",
        as_dict=True,
    )
    nodes = {r.name: r for r in rows}

    def _would_wrap(initial):
        if not initial:
            return False
        lower = initial.lower()
        return lower.endswith(_TEAM_SUFFIX) and not lower.endswith("-" + _TEAM_SUFFIX)

    print(f"\n{'lft':>4}  {'is_group':8}  {'parent':30}  action / name")
    print("-" * 80)
    for r in rows:
        if not r.is_group:
            print(f"{r.lft:>4}  {'leaf':8}  {(r.parent_ded_devotee or '(root)')!r:30}  {r.name!r}")
            continue

        if _would_wrap(r.initial):
            print(f"{r.lft:>4}  {'group':8}  {(r.parent_ded_devotee or '(root)')!r:30}  [SKIP — already a wrapper]  {r.name!r}")
            continue

        wrapper_initial = (r.initial or "") + _TEAM_SUFFIX
        if frappe.db.exists("DED Devotee", wrapper_initial):
            print(f"{r.lft:>4}  {'group':8}  {(r.parent_ded_devotee or '(root)')!r:30}  [SKIP — wrapper exists]  {r.name!r}")
            continue

        print(
            f"{r.lft:>4}  {'group':8}  {(r.parent_ded_devotee or '(root)')!r:30}  "
            f"[CREATE {wrapper_initial!r}]  wraps {r.name!r}"
        )

