# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

# import frappe
import json
from frappe.model.document import Document

import re
import frappe

from frappe import _


class HKMAssetsReco(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF
        from hkm.erpnext___custom.doctype.hkm_asset_specification_value.hkm_asset_specification_value import (
            HKMAssetSpecificationValue,
        )

        amended_from: DF.Link | None
        asset_category: DF.Link
        asset_id: DF.Link | None
        asset_name: DF.Data | None
        availability_status: DF.Literal["New", "Available"]
        company: DF.Link
        custodian_department: DF.Link | None
        location: DF.Data | None
        purchased_amount: DF.Currency
        purchased_date: DF.Date | None
        remarks: DF.Data | None
        secondary_custodian: DF.Link | None
        specification: DF.Table[HKMAssetSpecificationValue]
    # end: auto-generated types
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    # end: auto-generated types
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    def abbreviate(self, text):
        # Replace &, and, AND, And... with a space
        text = re.sub(r"\b(and|&)\b", " ", text, flags=re.IGNORECASE)

        # Split and take first letters
        words = text.split()
        return "".join(word[0].upper() for word in words)

    # def autoname(self):
    #     """
    #     Custom autoname method.
    #     IMPORTANT: If name is already set (e.g., from QR barcode printing),
    #     respect it and DO NOT override.
    #     """
    #     # Check if name is already set (from QR printing or explicit assignment)
    #     if self.name and self.name != "new-hkm-assets-reco":
    #         frappe.logger().info(f"autoname() - Name already set to: {self.name}, skipping autoname")
    #         return

    #     # Check if flags indicate name is pre-set
    #     if self.flags.get("name_set"):
    #         frappe.logger().info(f"autoname() - name_set flag is True, skipping autoname")
    #         return

    #     # Generate automatic name only if not already set
    #     prefix = "0001"

    #     while True:
    #         new_name = (
    #             f"{self.abbreviate(self.company)}"
    #             f"{self.abbreviate(self.asset_category)}"
    #             f"{prefix}"
    #         )

    #         if not frappe.db.exists("HKM Assets Reco", new_name):
    #             break

    #         prefix = f"{int(prefix) + 1:04d}"

    #     self.name = new_name
    #     frappe.logger().info(f"autoname() - Generated automatic name: {new_name}")

    def validate_specification(self):
        entered_specs = [d.specification for d in self.specification if d.specification]
        if entered_specs:
            specs_data = frappe.get_all(
                "HKM Asset Specification",
                filters={"name": ["in", entered_specs]},
                fields=["name", "asset_category", "specification_name"],
            )
            specs_map = {d.name: d for d in specs_data}

            for row in self.specification:
                if not row.specification:
                    continue

                spec_def = specs_map.get(row.specification)
                if spec_def and spec_def.asset_category != self.asset_category:
                    frappe.throw(
                        _(
                            "Specification {0} is not valid for category {1} (belongs to {2})"
                        ).format(
                            spec_def.specification_name,
                            self.asset_category,
                            spec_def.asset_category,
                        )
                    )

        mandatory_specs = frappe.get_all(
            "HKM Asset Specification",
            filters={"asset_category": self.asset_category, "is_mandatory": 1},
            fields=["name", "specification_name"],
        )

        provided_values = {
            d.specification: d.value for d in self.specification if d.specification
        }

        for m_spec in mandatory_specs:
            val = provided_values.get(m_spec.name)
            if not val:
                frappe.throw(
                    _("Specification {0} is mandatory").format(
                        m_spec.specification_name
                    )
                )

    def validate(self):

        old_doc = self.get_doc_before_save()
        if old_doc:
            if self.availability_status == "Available" and not self.asset_id:
                frappe.throw(
                    "Asset ID is required when availability status is Available"
                )

            if self.asset_id and frappe.get_all(
                "HKM Assets Reco",
                filters={
                    "asset_id": self.asset_id,
                    "docstatus": ["!=", 2],
                    "name": ["!=", self.name],
                },
            ):
                frappe.throw("Asset ID already linked to another asset reco")

            if not self.purchased_date:
                frappe.throw("Purchased Date is required")
            if not self.purchased_amount:
                frappe.throw("Purchased Amount is required")
            if not self.location:
                frappe.throw("Location is required")
            if not self.asset_name:
                frappe.throw("Asset Name is required")

            self.validate_specification()

            if old_doc.secondary_custodian != self.secondary_custodian:
                hod = frappe.db.get_value(
                    "Execution Department", self.custodian_department, "department_hod"
                )
                if (
                    frappe.session.user != hod
                    and frappe.session.user != "Administrator"
                ):
                    frappe.throw(
                        "You are not authorized to change the secondary custodian"
                    )

    def before_submit(self):
        hod = frappe.db.get_value(
            "Execution Department", self.custodian_department, "department_hod"
        )
        if frappe.session.user != hod and frappe.session.user != "Administrator":
            frappe.throw("You are not authorized to submit this asset reco")


@frappe.whitelist()
def get_assets_reco_id(company, asset_category):
    prefix = "0001"

    while True:
        new_name = f"{abbreviate(company)}" f"{abbreviate(asset_category)}" f"{prefix}"

        if not frappe.db.exists("HKM Assets Reco", new_name):
            break

        prefix = f"{int(prefix) + 1:04d}"

    return new_name


@frappe.whitelist()
def get_next_sequence_number(company, asset_category, abbreviation):
    """
    Get the next sequence number for the given abbreviation prefix.
    User provides abbreviation, system finds the next available number.
    Returns the next available sequence number only (not the full ID).
    """
    # Clean and validate abbreviation
    abbreviation = str(abbreviation).strip().upper()

    if not abbreviation:
        frappe.throw(_("Abbreviation prefix is required"))

    # Log the request for debugging
    frappe.logger().info(
        f"Getting next sequence for abbreviation: {abbreviation}, company: {company}, category: {asset_category}"
    )

    # Find the highest existing number with this prefix
    existing_assets = frappe.get_all(
        "HKM Assets Reco",
        filters={"name": ["like", f"{abbreviation}%"]},
        fields=["name"],
        order_by="name desc",
        limit=1,
    )

    if existing_assets:
        # Extract number from the last asset
        last_asset = existing_assets[0].name
        try:
            # Remove the abbreviation prefix to get the number
            number_part = last_asset.replace(abbreviation, "")
            last_number = int(number_part)
            next_number = last_number + 1
            frappe.logger().info(
                f"Last asset: {last_asset}, Next number: {next_number}"
            )
        except (ValueError, AttributeError):
            # If extraction fails, start from 1
            next_number = 1
            frappe.logger().warning(
                f"Could not extract number from {last_asset}, starting from 1"
            )
    else:
        next_number = 1
        frappe.logger().info(
            f"No existing assets found with prefix {abbreviation}, starting from 1"
        )

    # Double-check that the next ID doesn't exist (safety check)
    while frappe.db.exists("HKM Assets Reco", f"{abbreviation}{next_number:04d}"):
        next_number += 1

    return next_number


@frappe.whitelist()
def create_assets_reco(company, asset_category, qr_ids):
    """
    Create HKM Assets Reco records for printed QR codes.
    This function is called AFTER printing is successful.
    """
    if isinstance(qr_ids, str):
        qr_ids = json.loads(qr_ids)

    if not qr_ids:
        frappe.throw(_("No QR IDs provided"))

    # Log the creation request
    frappe.logger().info(
        f"Creating {len(qr_ids)} assets for company: {company}, category: {asset_category}"
    )
    frappe.logger().info(f"QR IDs: {qr_ids}")

    created_assets = []
    skipped_assets = []
    failed_assets = []

    for qr_id in qr_ids:
        try:
            # Validate QR ID format
            qr_id = str(qr_id).strip()
            if not qr_id:
                continue

            # Check if already exists
            if frappe.db.exists("HKM Assets Reco", qr_id):
                skipped_assets.append(qr_id)
                frappe.logger().info(f"Asset {qr_id} already exists, skipping")
                continue

            # Create new asset with explicit name
            # Set name BEFORE creating doc, and use flag to tell autoname() to skip
            doc = frappe.get_doc(
                {
                    "doctype": "HKM Assets Reco",
                    "name": qr_id,  # Set the QR ID as name
                    "company": company,
                    "asset_category": asset_category,
                    "availability_status": "New",  # Default status
                }
            )

            # CRITICAL: Set flag to tell autoname() not to override

            # Use normal insert() - this runs full lifecycle (validations, hooks, etc.)
            # but autoname() will check the flag and skip naming
            # frappe.logger().info(f"Creating asset with name: {qr_id}, name_set flag: True")
            doc.insert(ignore_permissions=True, set_name=qr_id)

            # Verify the name is correct
            if doc.name != qr_id:
                frappe.logger().error(
                    f"Name mismatch after insert! Expected: {qr_id}, Got: {doc.name}"
                )
                frappe.throw(
                    _(
                        f"Failed to create asset with correct name. Expected {qr_id}, got {doc.name}"
                    )
                )

            created_assets.append(doc.name)
            frappe.logger().info(
                f"Successfully created asset: {doc.name} (full lifecycle executed)"
            )

        except Exception as e:
            error_msg = str(e)
            failed_assets.append({"qr_id": qr_id, "error": error_msg})
            frappe.logger().error(f"Error creating asset {qr_id}: {error_msg}")
            frappe.log_error(
                f"Error creating asset {qr_id}: {error_msg}", "Asset Creation Error"
            )

    frappe.db.commit()  # v16: REVIEW - check if needed

    # Prepare response message
    message_parts = []
    if created_assets:
        message_parts.append(f"Successfully created {len(created_assets)} assets")
    if skipped_assets:
        message_parts.append(f"Skipped {len(skipped_assets)} existing assets")
    if failed_assets:
        message_parts.append(
            f"Failed to create {len(failed_assets)} assets (check error log)"
        )

    return {
        "success": len(created_assets) > 0,
        "created_count": len(created_assets),
        "created_assets": created_assets,
        "skipped_count": len(skipped_assets),
        "skipped_assets": skipped_assets,
        "failed_count": len(failed_assets),
        "failed_assets": failed_assets,
        "message": ", ".join(message_parts),
    }


def abbreviate(text):
    # Replace &, and, AND, And... with a space
    text = re.sub(r"\b(and|&)\b", " ", text, flags=re.IGNORECASE)

    # Split and take first letters
    words = text.split()
    return "".join(word[0].upper() for word in words)


@frappe.whitelist()
def get_existing_assets_count(company, asset_category):
    """Get count of existing assets and their ID range"""
    # Generate the prefix pattern for this company + category
    prefix = f"{abbreviate(company)}{abbreviate(asset_category)}"

    # Get all existing assets matching this prefix
    assets = frappe.get_all(
        "HKM Assets Reco",
        filters={"company": company, "asset_category": asset_category},
        fields=["name"],
        order_by="name asc",
    )

    if not assets:
        return {"total_count": 0, "first_id": None, "last_id": None}

    return {
        "total_count": len(assets),
        "first_id": assets[0].name,
        "last_id": assets[-1].name,
    }


@frappe.whitelist()
def get_assets_in_range(company, asset_category, abbreviation, from_number, to_number):
    """Get asset IDs in the specified range for the given abbreviation prefix"""
    # Clean and validate abbreviation
    abbreviation = str(abbreviation).strip().upper()
    
    if not abbreviation:
        frappe.throw(_("Abbreviation prefix is required"))
    
    # Validate company and asset_category match
    if not frappe.db.exists("Company", company):
        frappe.throw(_("Company {0} does not exist").format(company))
    
    if not frappe.db.exists("Asset Category", asset_category):
        frappe.throw(_("Asset Category {0} does not exist").format(asset_category))

    # Generate all possible IDs in the range using the provided abbreviation
    from_number = int(from_number)
    to_number = int(to_number)
    
    if from_number > to_number:
        frappe.throw(_("From number must be less than or equal to To number"))

    asset_ids = []
    for num in range(from_number, to_number + 1):
        asset_id = f"{abbreviation}{num:04d}"
        # Check if this asset exists and matches company and category
        if frappe.db.exists("HKM Assets Reco", asset_id):
            # Verify the asset belongs to the specified company and category
            asset_company, asset_category_val = frappe.db.get_value(
                "HKM Assets Reco", asset_id, ["company", "asset_category"]
            )
            if asset_company == company and asset_category_val == asset_category:
                asset_ids.append(asset_id)

    return asset_ids


def rename_assets_reco():

    for i in frappe.get_all(
        "HKM Assets Reco", filters={"asset_category": "Vehicles"}, pluck="name"
    ):
        result = i.replace("J", "", 1)

        frappe.rename_doc("HKM Assets Reco", i, result)
    frappe.db.commit()  # v16: REVIEW - check if needed
    return "done"
