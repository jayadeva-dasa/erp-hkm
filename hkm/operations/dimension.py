from dataclasses import field
from math import exp
import frappe

import frappe
import re


def clean_and_replace_company_text(
    value, old_company, new_company, old_suffix, new_suffix
):
    """
    Helper function to clean and replace company-related text in any field value
    Handles ALL variations of company suffixes including -Z-, -C- patterns
    """
    if not value or not isinstance(value, str):
        return value

    original_value = value
    cleaned = value

    # Replace full old company name first
    cleaned = cleaned.replace(old_company, new_company)

    # Replace old suffix with new suffix (most specific pattern first)
    cleaned = cleaned.replace(old_suffix, new_suffix)

    # Handle all variations of company suffix patterns (case insensitive)
    # Patterns for -Z-HKMJ, -z-HKMJ, - Z - HKMJ, etc.
    # Patterns for -C-HKMJ, -c-HKMJ, - C - HKMJ, etc.
    patterns_to_replace = [
        # Z patterns
        (r"\s*-\s*[Zz]\s*-\s*HKMJ", " - HKMJ"),  # - z - HKMJ or - Z - HKMJ
        (r"\s*-\s*[Zz]-HKMJ", " - HKMJ"),  # - Z-HKMJ or -Z-HKMJ
        (r"-[Zz]-HKMJ", " - HKMJ"),  # -Z-HKMJ or -z-HKMJ
        # C patterns
        (r"\s*-\s*[Cc]\s*-\s*HKMJ", " - HKMJ"),  # - c - HKMJ or - C - HKMJ
        (r"\s*-\s*[Cc]-HKMJ", " - HKMJ"),  # - C-HKMJ or -C-HKMJ
        (r"-[Cc]-HKMJ", " - HKMJ"),  # -C-HKMJ or -c-HKMJ
        # Generic Z patterns (without HKMJ)
        (r"\s*-\s*[Zz]\s*-\s*", " - "),  # Generic - z - pattern
        (r"\s*-\s*[Zz]-", " - "),  # Generic - Z- pattern
        (r"-[Zz]-", " - "),  # Generic -Z- pattern
        # Generic C patterns (without HKMJ)
        (r"\s*-\s*[Cc]\s*-\s*", " - "),  # Generic - c - pattern
        (r"\s*-\s*[Cc]-", " - "),  # Generic - C- pattern
        (r"-[Cc]-", " - "),  # Generic -C- pattern
    ]

    for pattern, replacement in patterns_to_replace:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)

    # Clean up any double spaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Clean up any double dashes (including with spaces: "- -" or "- - ")
    cleaned = re.sub(r"\s*-\s*-\s*", " - ", cleaned)

    # Clean up triple or more dashes
    cleaned = re.sub(r"-{2,}", "-", cleaned)

    # Final trim
    cleaned = cleaned.strip()

    return cleaned if cleaned != original_value else value


def should_process_field(value, old_company):
    """
    Check if a field value needs to be processed for company migration
    Detects all variations of company references including -Z- and -C- patterns
    """
    if not value or not isinstance(value, str):
        return False

    # Check for various patterns
    patterns_to_check = [
        old_company,  # Full old company name
        # C patterns
        "- c -",  # Cost center pattern variations
        "-c-",
        "- C-",
        "-C-",
        " c ",
        "C-HKMJ",  # Old suffix variations
        "c-HKMJ",
        # Z patterns
        "- z -",
        "-z-",
        "- Z-",
        "-Z-",
        " z ",
        "Z-HKMJ",
        "z-HKMJ",
    ]

    value_lower = value.lower()
    for pattern in patterns_to_check:
        if pattern.lower() in value_lower:
            return True

    return False


def validate_new_value(doctype, field_name, new_value, new_company):
    """
    Validate that the new value exists in the database
    ONLY validates critical fields: Account, Cost Center, Company
    Returns: (is_valid: bool, error_message: str)
    """
    if not new_value or not isinstance(new_value, str):
        return True, None

    try:
        # Get the actual field metadata from doctype
        meta = frappe.get_meta(doctype)
        field_def = meta.get_field(field_name)

        if not field_def:
            # Field doesn't exist in meta (might be dynamic), skip validation
            return True, None

        # Only validate Link fields
        if field_def.fieldtype != "Link":
            return True, None

        link_doctype = field_def.options

        # ONLY validate critical accounting fields
        if link_doctype == "Account":
            # Try with exact match first
            if frappe.db.exists("Account", new_value):
                return True, None

            # Try with trimmed/cleaned value
            cleaned_value = new_value.strip()
            if frappe.db.exists("Account", cleaned_value):
                return True, None

            return False, f"❌ Account '{new_value}' does not exist"

        elif link_doctype == "Cost Center":
            if frappe.db.exists("Cost Center", new_value):
                return True, None

            cleaned_value = new_value.strip()
            if frappe.db.exists("Cost Center", cleaned_value):
                return True, None

            return False, f"❌ Cost Center '{new_value}' does not exist"

        elif link_doctype == "Company":
            if frappe.db.exists("Company", new_value):
                return True, None
            return False, f"❌ Company '{new_value}' does not exist"

        else:
            # For all other link fields (Bank Account, Customer, Supplier, etc.)
            # Skip validation - let user decide during approval
            return True, None

    except Exception as e:
        # If validation fails, log but don't block
        print(f"   ⚠️  Validation warning for {doctype}.{field_name}: {str(e)}")
        return True, None


def get_user_approval(doctype, docname, field, old_value, new_value, auto_approve_all):
    """
    Interactive approval for each change
    Returns: (approved: bool, auto_approve_all: bool)
    """
    if auto_approve_all:
        return True, True

    print("\n" + "─" * 70)
    print(f"📄 DocType: {doctype}")
    print(f"📌 Document: {docname}")
    print(f"🔧 Field: {field}")
    print(f"❌ Old Value: {old_value}")
    print(f"✅ New Value: {new_value}")
    print("─" * 70)

    while True:
        response = (
            input("👉 Approve? [y=yes / n=no / a=approve all remaining / q=quit]: ")
            .strip()
            .lower()
        )

        if response in ["y", "yes"]:
            return True, False
        elif response in ["n", "no"]:
            return False, False
        elif response in ["a", "all"]:
            print("\n✅ Auto-approving all remaining changes...")
            return True, True
        elif response in ["q", "quit"]:
            print("\n🛑 Migration cancelled by user.")
            frappe.db.rollback()
            return False, False
        else:
            print("Invalid input. Please enter y/n/a/q")


def migrate_company_dimension():
    """
    Dynamically migrate all Sales Invoices and related data from
    'Z - Hare Krishna Movement Jaipur' to 'Hare Krishna Movement Jaipur'
    Uses doc.as_dict() to catch ALL fields automatically
    WITH INTERACTIVE APPROVAL for each change
    """
    old_company = "Z - Hare Krishna Movement Jaipur"
    new_company = "Hare Krishna Movement Jaipur"
    old_suffix = " - c - Z - Hare Krishna Movement Jaipur"
    new_suffix = " - HKMJ"

    print("=" * 70)
    print("🔄 Starting Dynamic Sales Invoice Company Migration (APPROVAL MODE)")
    print("=" * 70)

    # Get all Sales Invoices to migrate
    invoices = frappe.db.sql_list(
        """
        SELECT DISTINCT name 
        FROM `tabSales Invoice`
        WHERE company = %(old_company)s
        ORDER BY name
        """,
        {"old_company": old_company},
    )

    total_invoices = len(invoices)
    print(f"\n📊 Found {total_invoices} Sales Invoices to migrate")

    if not total_invoices:
        print("✅ No invoices to migrate. Exiting.")
        return

    # Collect all changes first before applying
    print("\n🔍 Phase 1: Collecting all changes...")
    all_changes = []

    # Track stats
    stats = {
        "total_changes": 0,
        "approved_changes": 0,
        "skipped_changes": 0,
        "invoice_fields": set(),
        "child_table_fields": set(),
        "gl_fields": set(),
    }

    # Process each invoice to collect changes
    for idx, invoice_name in enumerate(invoices, start=1):
        try:
            doc = frappe.get_doc("Sales Invoice", invoice_name)
            doc_dict = doc.as_dict()

            # Collect parent field changes
            for field, value in doc_dict.items():
                if field.startswith("_") or value is None or isinstance(value, list):
                    continue

                if should_process_field(value, old_company):
                    new_value = clean_and_replace_company_text(
                        value, old_company, new_company, old_suffix, new_suffix
                    )
                    if new_value != value:
                        all_changes.append(
                            {
                                "type": "parent",
                                "doctype": "Sales Invoice",
                                "docname": invoice_name,
                                "field": field,
                                "old_value": value,
                                "new_value": new_value,
                            }
                        )
                        stats["invoice_fields"].add(field)

            # Always update company field
            if doc.company == old_company:
                all_changes.append(
                    {
                        "type": "parent",
                        "doctype": "Sales Invoice",
                        "docname": invoice_name,
                        "field": "company",
                        "old_value": old_company,
                        "new_value": new_company,
                    }
                )
                stats["invoice_fields"].add("company")

            # Collect child table changes
            meta = frappe.get_meta("Sales Invoice")
            for df in meta.fields:
                if df.fieldtype == "Table" and df.options:
                    child_doctype = df.options
                    child_records = doc.get(df.fieldname) or []

                    for child in child_records:
                        child_dict = child.as_dict()
                        for child_field, child_value in child_dict.items():
                            if child_field.startswith("_") or child_value is None:
                                continue

                            if should_process_field(child_value, old_company):
                                new_value = clean_and_replace_company_text(
                                    child_value,
                                    old_company,
                                    new_company,
                                    old_suffix,
                                    new_suffix,
                                )
                                if new_value != child_value:
                                    all_changes.append(
                                        {
                                            "type": "child",
                                            "doctype": child_doctype,
                                            "docname": child.name,
                                            "field": child_field,
                                            "old_value": child_value,
                                            "new_value": new_value,
                                            "parent": invoice_name,
                                        }
                                    )
                                    stats["child_table_fields"].add(
                                        f"{child_doctype}.{child_field}"
                                    )

            print(f"   ✓ Scanned {idx}/{total_invoices} invoices", end="\r", flush=True)

        except Exception as e:
            print(f"\n   ❌ Error scanning {invoice_name}: {str(e)}")
            continue

    # Collect GL Entry changes
    print("\n\n🔍 Phase 2: Collecting GL Entry changes...")

    gl_entries = frappe.db.sql_list(
        """
        SELECT name
        FROM `tabGL Entry`
        WHERE company = %(old_company)s
        AND voucher_type = 'Sales Invoice'
        """,
        {"old_company": old_company},
    )

    total_gl = len(gl_entries)

    for idx, gl_name in enumerate(gl_entries, start=1):
        try:
            gl_doc = frappe.get_doc("GL Entry", gl_name)
            gl_dict = gl_doc.as_dict()

            for field, value in gl_dict.items():
                if field.startswith("_") or value is None or isinstance(value, list):
                    continue

                if should_process_field(value, old_company):
                    new_value = clean_and_replace_company_text(
                        value, old_company, new_company, old_suffix, new_suffix
                    )
                    if new_value != value:
                        all_changes.append(
                            {
                                "type": "gl",
                                "doctype": "GL Entry",
                                "docname": gl_name,
                                "field": field,
                                "old_value": value,
                                "new_value": new_value,
                            }
                        )
                        stats["gl_fields"].add(field)

            # Always update company
            if gl_doc.company == old_company:
                all_changes.append(
                    {
                        "type": "gl",
                        "doctype": "GL Entry",
                        "docname": gl_name,
                        "field": "company",
                        "old_value": old_company,
                        "new_value": new_company,
                    }
                )
                stats["gl_fields"].add("company")

            print(f"   ✓ Scanned {idx}/{total_gl} GL Entries", end="\r", flush=True)

        except Exception as e:
            print(f"\n   ❌ Error scanning GL Entry {gl_name}: {str(e)}")
            continue

    stats["total_changes"] = len(all_changes)

    print(f"\n\n" + "=" * 70)
    print(f"📊 SUMMARY: Found {stats['total_changes']} total changes")
    print("=" * 70)
    print(
        f"  • Sales Invoice changes: {sum(1 for c in all_changes if c['type'] == 'parent')}"
    )
    print(
        f"  • Child Table changes: {sum(1 for c in all_changes if c['type'] == 'child')}"
    )
    print(f"  • GL Entry changes: {sum(1 for c in all_changes if c['type'] == 'gl')}")
    print("=" * 70)

    if not all_changes:
        print("\n✅ No changes needed. Exiting.")
        return

    # Validate all changes
    print("\n🔍 Phase 3: Validating new values in database...")
    print("=" * 70)

    valid_changes = []
    invalid_changes = []

    for idx, change in enumerate(all_changes, start=1):
        is_valid, error_msg = validate_new_value(
            change["doctype"], change["field"], change["new_value"], new_company
        )

        if is_valid:
            valid_changes.append(change)
        else:
            change["validation_error"] = error_msg
            invalid_changes.append(change)

        if idx % 50 == 0 or idx == len(all_changes):
            print(
                f"   ✓ Validated {idx}/{len(all_changes)} changes", end="\r", flush=True
            )

    print(f"\n\n✅ Validation Complete:")
    print(f"   • Valid changes: {len(valid_changes)}")
    print(f"   • Invalid changes: {len(invalid_changes)}")

    if invalid_changes:
        print(f"\n⚠️  WARNING: {len(invalid_changes)} changes have validation errors:\n")
        for change in invalid_changes[:10]:  # Show first 10
            print(f"   ❌ {change['doctype']}.{change['field']}: {change['new_value']}")
            print(f"      {change['validation_error']}")

        if len(invalid_changes) > 10:
            print(f"\n   ... and {len(invalid_changes) - 10} more invalid changes")

        print("\n   These changes will be SKIPPED automatically.")

    if not valid_changes:
        print("\n❌ No valid changes to apply. Exiting.")
        return

    # Now ask for approval (only for valid changes)
    print("\n" + "=" * 70)
    print(f"🔍 Phase 4: Reviewing and approving {len(valid_changes)} valid changes...")
    print("=" * 70)
    print("\n💡 Options: y=yes, n=no, a=approve all remaining, q=quit\n")

    auto_approve_all = False
    approved_changes = []

    for idx, change in enumerate(valid_changes, start=1):
        print(f"\n[Change {idx}/{len(valid_changes)}]")

        parent_info = f" (Parent: {change['parent']})" if change.get("parent") else ""

        approved, auto_approve_all = get_user_approval(
            doctype=change["doctype"],
            docname=change["docname"] + parent_info,
            field=change["field"],
            old_value=change["old_value"],
            new_value=change["new_value"],
            auto_approve_all=auto_approve_all,
        )

        if approved:
            approved_changes.append(change)
            stats["approved_changes"] += 1
        else:
            stats["skipped_changes"] += 1
            if not auto_approve_all:  # User pressed 'q'
                print("\n🛑 Migration cancelled. No changes have been applied.")
                return

    # Apply approved changes
    print("\n\n" + "=" * 70)
    print(f"✅ Applying {len(approved_changes)} approved changes...")
    print("=" * 70)

    for idx, change in enumerate(approved_changes, start=1):
        try:
            frappe.db.set_value(
                change["doctype"],
                change["docname"],
                change["field"],
                change["new_value"],
                update_modified=False,
            )

            if idx % 10 == 0 or idx == len(approved_changes):
                print(
                    f"   ✓ Applied {idx}/{len(approved_changes)} changes",
                    end="\r",
                    flush=True,
                )

        except Exception as e:
            print(
                f"\n   ❌ Error applying change to {change['docname']}.{change['field']}: {str(e)}"
            )
            continue

    # Commit all changes
    frappe.db.commit()  # v16: OK - operations script

    print(f"\n\n" + "=" * 70)
    print("✅ MIGRATION COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print(f"\nStatistics:")
    print(f"  • Total changes found: {stats['total_changes']}")
    print(f"  • Valid changes: {len(valid_changes)}")
    print(f"  • Invalid changes (skipped): {len(invalid_changes)}")
    print(f"  • Approved & applied: {stats['approved_changes']}")
    print(f"  • User skipped: {stats['skipped_changes']}")
    print(f"\nFields Updated in Sales Invoice:")
    for field in sorted(stats["invoice_fields"]):
        print(f"    - {field}")
    print(f"\nChild Table Fields Updated:")
    for field in sorted(stats["child_table_fields"]):
        print(f"    - {field}")
    print(f"\nGL Entry Fields Updated:")
    for field in sorted(stats["gl_fields"]):
        print(f"    - {field}")

    if invalid_changes:
        print(f"\n⚠️  Invalid Changes (Not Applied):")
        for change in invalid_changes[:5]:
            print(f"    - {change['doctype']}.{change['field']}: {change['new_value']}")
        if len(invalid_changes) > 5:
            print(f"    ... and {len(invalid_changes) - 5} more")

    print("\n" + "=" * 70)


def migrate_cost_head():
    # cost_heads = frappe.db.get_descendants("Cost Head", "Volunteers") + ["Volunteers"]
    # print(cost_heads)

    # # Find all voucher types with invalid cost_head-volunteer pairs
    # voucher_types = frappe.db.sql_list(
    #     """
    #     SELECT DISTINCT gl.voucher_type
    #     FROM `tabGL Entry` gl
    #     WHERE gl.volunteer IS NOT NULL
    #     AND gl.cost_head IS NOT NULL
    #     AND TRIM(gl.cost_head) != ''
    #     AND TRIM(gl.cost_head) != 'None'
    #     AND TRIM(gl.volunteer) != ''
    #     AND gl.cost_head NOT IN %(cost_heads)s
    #     """,
    #     {"cost_heads": cost_heads},
    # )

    # voucher_types = ["GL Entry"] + voucher_types
    # print(f"Found {len(voucher_types)} voucher types to process\n")

    # child_docs = set()

    # # Process each doctype
    # for doctype in voucher_types:
    #     print(f"🔍 Processing {doctype}...")

    #     # Ensure fields exist
    #     if frappe.db.has_column(doctype, "volunteer") and frappe.db.has_column(
    #         doctype, "cost_head"
    #     ):

    #         # Fetch all records to clean
    #         parent_records = frappe.db.sql(
    #             f"""
    #             SELECT name
    #             FROM `tab{doctype}`
    #             WHERE volunteer IS NOT NULL
    #             AND cost_head IS NOT NULL
    #             AND TRIM(cost_head) != ''
    #             AND TRIM(cost_head) != 'None'
    #             AND TRIM(volunteer) != ''
    #             AND cost_head NOT IN %(cost_heads)s
    #             """,
    #             {"cost_heads": cost_heads},
    #             as_dict=True,
    #         )

    #         total = len(parent_records)
    #         print(parent_records[0])
    #         if not total:
    #             print("   No records to update.")
    #         else:
    #             for idx, rec in enumerate(parent_records, start=1):
    #                 frappe.db.set_value(doctype, rec.name, "volunteer", None)
    #                 if idx % 10 == 0 or idx == total:
    #                     print(
    #                         f"   ↻ Updated {idx}/{total} parent rows",
    #                         end="\r",
    #                         flush=True,
    #                     )

    #             print(f"\n   ✅ Updated {total} parent records in {doctype}")

    #     # Find child tables for further updates
    #     meta = frappe.get_meta(doctype)
    #     for f in meta.fields:
    #         if (
    #             f.fieldtype == "Table"
    #             and frappe.db.has_column(f.options, "volunteer")
    #             and frappe.db.has_column(f.options, "cost_head")
    #         ):
    #             child_docs.add(f.options)

    # print(child_docs)
    # # Process child doctypes
    # for child_doc in child_docs:
    #     print(f"↳ Updating {child_doc}...")

    #     if not (
    #         frappe.db.has_column(child_doc, "volunteer")
    #         and frappe.db.has_column(child_doc, "cost_head")
    #     ):
    #         print(f"   ⚠️ Skipped child {child_doc} (missing volunteer or cost_head)")
    #         continue

    #     child_records = frappe.db.sql(
    #         f"""
    #         SELECT name
    #         FROM `tab{child_doc}`
    #         WHERE volunteer IS NOT NULL
    #           AND cost_head IS NOT NULL
    #           AND TRIM(cost_head) != ''
    #           AND TRIM(cost_head) != 'None'
    #           AND TRIM(volunteer) != ''
    #           AND cost_head NOT IN %(cost_heads)s
    #         """,
    #         {"cost_heads": cost_heads},
    #         as_dict=True,
    #     )

    #     total = len(child_records)
    #     if not total:
    #         print("   No child rows to update.")
    #         continue

    #     for idx, rec in enumerate(child_records, start=1):
    #         frappe.db.set_value(child_doc, rec.name, "volunteer", None)
    #         if idx % 10 == 0 or idx == total:
    #             print(f"   ↻ Updated {idx}/{total} child rows", end="\r", flush=True)

    #     print(f"\n   ✅ Updated {total} child rows in {child_doc}")

    # frappe.db.commit()
    # print("\n✅ Done migrating cost heads (parent + child tables)")

    mapping = {
        "Family Support": "Basic Support",
    }

    voucher_types = frappe.db.sql_list(
        """
    SELECT DISTINCT gl.voucher_type
    FROM `tabGL Entry` gl
    JOIN `tabDED Component Head` c ON c.name = gl.volunteer_head
    WHERE c.name = 'Family Support'
    AND gl.volunteer_head IS NOT NULL
"""
    )

    voucher_types = ["GL Entry"] + voucher_types

    child_docs = set()
    print(f"Found {len(voucher_types)} voucher types to process\n")

    for doctype in voucher_types:
        print(f"🔍 Processing {doctype}...")

        # ✅ Check if cost_head exists in the main doctype
        if not frappe.db.has_column(doctype, "volunteer"):
            print(f"   ⚠️ Skipped — no 'volunteer' field in {doctype}")
            continue

        meta = frappe.get_meta(doctype)
        parent_fields = meta.fields

        if frappe.db.has_column(doctype, "volunteer"):

            parent_records = frappe.get_all(
                doctype,
                filters={"volunteer": ["in", list(mapping.keys())]},
                fields=["name", "volunteer"],
            )

            total = len(parent_records)
            for idx, i in enumerate(parent_records, start=1):
                frappe.db.set_value(doctype, i.name, "volunteer", mapping[i.volunteer])
                if idx % 10 == 0 or idx == total:
                    print(
                        f"   ↻ Updated {idx}/{total} parent rows", end="\r", flush=True
                    )

            if total:
                print(f"   ✅ Updated {total} parent records")

            # find child doctypes
            for f in parent_fields:
                if f.fieldtype == "Table":
                    child_doctype = f.options
                    if frappe.db.has_column(child_doctype, "volunteer"):
                        child_docs.add(child_doctype)

    # update child doctypes
    for child_doc in child_docs:
        if not frappe.db.has_column(child_doc, "volunteer"):
            print(f"   ⚠️ Skipped child {child_doc} (no cost_head column)")
            continue

        child_records = frappe.get_all(
            child_doc,
            filters={"volunteer": ["in", list(mapping.keys())]},
            fields=["name", "volunteer"],
        )

        total = len(child_records)
        if not total:
            continue

        print(f"↳ Updating {child_doc}...")
        for idx, i in enumerate(child_records, start=1):
            frappe.db.set_value(child_doc, i.name, "volunteer", mapping[i.volunteer])
            if idx % 10 == 0 or idx == total:
                print(f"   ↻ Updated {idx}/{total} child rows", end="\r", flush=True)

        print(f"   ✅ Updated {total} child rows in {child_doc}")

    frappe.db.commit()  # v16: OK - operations script
    print("\n✅ Done migrating cost heads (parent + child tables)")


def create_ded_devotee():
    doc_devotee = frappe.get_all("DED Devotee", pluck="name")
    devotees = frappe.get_all(
        "Devotee",
        filters={
            "name": [
                "not in",
                doc_devotee,
            ]
        },
        pluck="name",
    )
    for i in devotees:
        frappe.get_doc(
            {"doctype": "DED Devotee", "full_name": i, "initial": i, "enabled": 0}
        ).insert()
    frappe.db.commit()  # v16: OK - operations script
    print("✅ Done creating DED Devotee")


def set_status_indicator():
    pos = frappe.get_all("Purchase Order", pluck="name")
    total = len(pos)
    done = 0

    for i in pos:
        doc = frappe.get_doc("Purchase Order", i)

        # default
        indicator = "Check Pending"
        if doc.docstatus == 1:
            indicator = "Approved"
        elif doc.docstatus == 2:
            indicator = "Cancelled"
        elif doc.approval_status == "Rejected":
            indicator = "Rejected"
        elif doc.docstatus == 0 and doc.locked == 1:
            authorities = frappe.get_all(
                "Approval Matrix Authority",
                filters={"parent": i},
                fields=["status"],
            )
            approved_count = sum(1 for a in authorities if a.status == "Approved")
            total_auth = len(authorities)
            if approved_count == 1:
                indicator = "Approval Started"
            elif (approved_count + 1) == total_auth and total_auth > 1:
                indicator = "Final Approval Pending"
            elif approved_count == total_auth:
                indicator = "Approved"
            else:
                indicator = "Checked"

        frappe.db.set_value("Purchase Order", i, "status_indicator", indicator)
        done += 1

        # overwrite same line
        print(
            f"\rProgress: {done}/{total} (Last: {i} -> {indicator})", end="", flush=True
        )

    frappe.db.commit()  # v16: OK - operations script
    print("\n✅ Done updating all Purchase Orders")


import frappe

import frappe


def find_dangling_assignments(doctype):
    # Get all docs where assigned_to is not null
    docs_with_assignment = frappe.get_all(
        doctype, filters={"_assign": ["is", "set"]}, pluck="name"
    )

    dangling = []
    for docname in docs_with_assignment:
        todo_exists = frappe.get_all(
            "ToDo",
            filters={
                "reference_type": doctype,
                "reference_name": docname,
                "status": ("!=", "Cancelled"),
            },
            limit=1,
        )
        if not todo_exists:
            dangling.append(docname)
    return dangling


def clean_dangling_assignments():
    doctype = "Purchase Order"
    dangling_docs = find_dangling_assignments(doctype)
    total = len(dangling_docs)
    print(f"Found {total} dangling assignments in {doctype}\n")

    for idx, docname in enumerate(dangling_docs, start=1):
        frappe.db.set_value(doctype, docname, "_assign", None)
        print(f"\rCleared assignment for {idx}/{total}", end="", flush=True)

    frappe.db.commit()  # v16: OK - operations script
    print("\n✅ All dangling assignments cleaned up!")

    # todos = frappe.get_all(
    #     "ToDo",
    #     filters={
    #         "reference_type": "Purchase Order",
    #         "reference_name": ["in", purchase_orders],
    #     },
    #     pluck="name",
    #     limit=2000,
    # )

    # total_todos = len(todos)
    # print(f"Found {total_todos} ToDo records to delete...\n")

    # for idx, j in enumerate(todos, start=1):
    #     frappe.delete_doc("ToDo", j, ignore_permissions=True)

    #     print(f"\rDeleting ToDo {idx}/{total_todos}", end="", flush=True)

    frappe.db.commit()  # v16: OK - operations script
    print("\n✅ All ToDo assignments cleared successfully!")


def replace_dimension():
    if not frappe.db.exists("Accounting Dimension", "Volunteer"):
        frappe.get_doc(
            {
                "doctype": "Accounting Dimension",
                "document_type": "DED Devotee",
                "label": "Volunteer",
            }
        ).insert()

    for d in frappe.get_hooks("accounting_dimension_doctypes"):

        try:
            docs = frappe.db.sql(
                f"SELECT name, devotee FROM `tab{d}` WHERE devotee IS NOT NULL AND TRIM(devotee) != '' AND devotee != 'None' AND volunteer IS NULL",
                as_dict=True,
            )

            total = len(docs)
            try:
                for idx, doc in enumerate(docs, start=1):
                    # Set volunteer field
                    frappe.db.set_value(d, doc.name, "volunteer", doc.devotee)

                    # Show progress in single line
                    print(
                        f"Updating {d}: {idx}/{total} → {doc.name} = {doc.devotee}",
                        end="\r",
                    )
            except Exception as e:
                frappe.log_error(f"Error updating {d}: {e}")
        except Exception as e:
            frappe.log_error(f"Error getting docs for {d}: {e}")

        print()

    frappe.db.commit()  # v16: OK - operations script


def set_volunteer_head():
    expenses_mapping = {
        "Audio Expenses - HKMJ": "Other",
        "Bank Expenses - HKMJ": "Office & Admin",
        "Book & Gifts Expenses - HKMJ": "Publicity & Promotion",
        "Cultural Program Expenses - HKMJ": "Programs & Events",
        "Disposable Expenses - HKMJ": "Food",
        "Donor Development Expenses - HKMJ": "Programs & Events",
        "Electricity Expenses - HKMJ": "Housing & Utilities",
        "Electronics Insurance Expenses - HKMJ": "Other",
        "Flowers/Decoration Expenses - HKMJ": "Programs & Events",
        "Food Distribution Expenses - HKMJ": "Food",
        "Freight and Forwarding Expenses - HKMJ": "Transport",
        "Fuel Expenses - HKMJ": "Transport",
        "Gaushala Expenses - HKMJ": "Other",
        "Grihasta Allowance-ALKD - HKMJ": "Salaries & Allowances",
        "Grihasta Allowance-NMCD - HKMJ": "Salaries & Allowances",
        "Grihasta Allowance-SMND - HKMJ": "Salaries & Allowances",
        "Grihasta Medical Allowance-AJKD - HKMJ": "Medical",
        "Grihasta Medical Allowance-NMCD - HKMJ": "Medical",
        "Honorarium Expenses - HKMJ": "Salaries & Allowances",
        "House Setup Allowance - HKMJ": "Housing & Utilities",
        "Housekeeping Expenses - HKMJ": "Housing & Utilities",
        "IT & Software Expenses - HKMJ": "IT & Communication",
        "Kitchen Expenses - HKMJ": "Food",
        "Labour Expenses - HKMJ": "Other",
        "Laundry Expenses - HKMJ": "Other",
        "Legal Expenses - HKMJ": "Office & Admin",
        "Medical Expenses - HKMJ": "Medical",
        "Medical Expenses - RKM": "Medical",
        "Medical Insurance Expenses - HKMJ": "Medical",
        "Miscellaneous Expenses - General - HKMJ": "Office & Admin",
        "Postage & Courier Expenses - HKMJ": "Office & Admin",
        "Printing and Stationary Expenses - HKMJ": "Office & Admin",
        "Publicity & Promotion Expenses - HKMJ": "Publicity & Promotion",
        "Rent payable for Jagatpura B-100 Mahal Scheme NMCD - HKMJ": "Housing & Utilities",
        "Rent payable for Jagatpura F209 Balaji Tower (ALKD Prabhu) - HKMJ": "Housing & Utilities",
        "Rental Expenses (House) - HKMJ": "Housing & Utilities",
        "Repair & Maintainance (Civil) - HKMJ": "Repairs & Maintenance",
        "Repair & Maintainance (Other Equipments) - HKMJ": "Repairs & Maintenance",
        "Repair & Maintainance (Vehicle) - HKMJ": "Repairs & Maintenance",
        "Repair & Maintenance (IT) - HKMJ": "IT & Communication",
        "Repairs & Maintenance (General) - HKMJ": "Repairs & Maintenance",
        "Repairs & Maintenance(Furniture & Fixtures) - HKMJ": "Repairs & Maintenance",
        "Rounded Off - HKMJ": "Other",
        "Routine Utilities Allowance - HKMJ": "Salaries & Allowances",
        "Staff Welfare Expenses - HKMJ": "Other",
        "Telecommunication Expenses - HKMJ": "IT & Communication",
        "Training Expenses - HKMJ": "Other",
        "Travel Expenses - HKMJ": "Transport",
        "Vehicle Hiring Expenses - HKMJ": "Transport",
        "Volunteer Expenses - HKMJ": "Other",
        "Water Expenses - HKMJ": "Housing & Utilities",
        "Worship & Rituals Expenses - HKMJ": "Programs & Events",
        "Yatra Allowance - HKMJ": "Other",
        "Youth Programs Expenses - HKMJ": "Programs & Events",
    }

    cost_head = ["Brahmachari Ashram - General", "Grihastha Ashram"]

    keys = list(expenses_mapping.keys())
    rows = frappe.db.sql(
        """
            SELECT name, account
            FROM `tabGL Entry`
            WHERE volunteer IS NOT NULL
            AND account in %(accounts)s
            AND volunteer IS NOT NULL
            AND TRIM(volunteer) != ''
            AND volunteer != 'None'
            AND volunteer_head IS NULL
            AND cost_head IN %(cost_head)s
            """,
        {"accounts": keys, "cost_head": cost_head},
        as_dict=True,
    )

    total = len(rows)
    print(f"Total rows to update: {total}")

    for idx, i in enumerate(rows, start=1):
        frappe.db.set_value(
            "GL Entry", i.name, "volunteer_head", expenses_mapping[i.account]
        )

        print(f"Progress: {idx}/{total}", end="\r")

    frappe.db.commit()  # v16: OK - operations script
    print(f"\n✅ Completed all {total} updates.")

    expense_account = frappe.db.sql_list(
        """
                    SELECT DISTINCT parent
                    FROM `tabPurchase Invoice Item`
                    WHERE volunteer IS NOT NULL
                    AND expense_account in %(accounts)s
                    AND volunteer IS NOT NULL
                    AND TRIM(volunteer) != ''
                    AND volunteer_head IS NULL
                    AND volunteer != 'None'
                    AND cost_head IN %(cost_head)s
                    """,
        {"accounts": keys, "cost_head": cost_head},
        # as_dict=True,
    )
    print(expense_account)

    expense_account = frappe.db.sql(
        """
                    SELECT name, expense_account
                    FROM `tabPurchase Invoice Item`
                    WHERE volunteer IS NOT NULL
                    AND expense_account in %(accounts)s
                    AND volunteer IS NOT NULL
                    AND TRIM(volunteer) != ''
                    AND volunteer_head IS NULL
                    AND volunteer != 'None'
                    AND cost_head IN %(cost_head)s
                    """,
        {"accounts": keys, "cost_head": cost_head},
        as_dict=True,
    )
    total = len(expense_account)
    print(f"Total rows to update: {total}")

    for idx, i in enumerate(expense_account, start=1):
        frappe.db.set_value(
            "Purchase Invoice Item",
            i.name,
            "volunteer_head",
            expenses_mapping[i.expense_account],
        )

        print(f"Progress: {idx}/{total}", end="\r")

    frappe.db.commit()  # v16: OK - operations script
    print(f"\n✅ Completed all {total} updates.")
