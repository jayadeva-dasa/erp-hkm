# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

# import frappe
from asyncio import Condition
import frappe
from frappe.model.document import Document


from frappe import _
import re


class ApprovalMatrix(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF
        from hkm.erpnext___custom.doctype.approval_matrix_detail.approval_matrix_detail import ApprovalMatrixDetail

        dimension: DF.Link
        fields_applicable: DF.Data | None
        target_doctype: DF.Link
        transitions: DF.Table[ApprovalMatrixDetail]
    # end: auto-generated types

    def validate(self):
        self.validate_applicable_fields()

    def validate_applicable_fields(self):
        # Build list of applicable fields (excluding dimension field since it's handled separately)
        applicable_fields = [
            f.strip() for f in (self.fields_applicable or "").split(",") if f.strip()
        ]

        # Add dimension field to allowed fields for validation purposes
        # (even though it's not in fields_applicable, it's valid via dimension_value)
        dimension_fieldname = frappe.scrub(self.dimension) if self.dimension else None
        allowed_fields = applicable_fields.copy()
        if dimension_fieldname:
            allowed_fields.append(dimension_fieldname)

        print(f"Applicable fields: {applicable_fields}")
        print(f"Allowed fields (including dimension): {allowed_fields}")

        for transition in self.transitions:
            authorities = list(
                {
                    auth.strip()
                    for auth in (transition.approving_authority or "").strip().split("\n")
                    if auth.strip()
                }
            )

            for authority in authorities:
                if not frappe.db.exists("User", {"email": authority}):
                    frappe.throw(_("User '{0}' does not exist").format(authority))

            if transition.condition:

                print(f"Validating condition: {transition.condition}")
                # extract identifiers (words with letters, numbers, underscores, or dots)
                words = re.findall(
                    r"\b[a-zA-Z_][a-zA-Z0-9_]*\b(?=\s*(?:==|!=|<=|>=|<|>| in | not in | is ))",
                    transition.condition,
                )

                for word in words:
                    # reject dotted fields explicitly
                    if "." in word:
                        frappe.throw(
                            _("Dotted field '{0}' is not allowed in conditions").format(
                                word
                            )
                        )

                    # Check against allowed_fields (which includes dimension field)
                    if word not in allowed_fields:
                        if not allowed_fields:
                            frappe.throw(
                                _(
                                    "Field '{0}' is not applicable. No fields are configured in 'Fields Applicable'. "
                                    "Please add '{0}' to 'Fields Applicable' or remove it from the condition."
                                ).format(word)
                            )
                        else:
                            frappe.throw(
                                _(
                                    "Field '{0}' is not applicable. Allowed fields: {1}"
                                ).format(word, ", ".join(allowed_fields))
                            )
