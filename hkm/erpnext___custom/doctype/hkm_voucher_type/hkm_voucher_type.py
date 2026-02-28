# Copyright (c) 2024, Narahari Dasa and contributors
# For license information, please see license.txt

# import frappe
from hkm.utils import validate_child_single_field_duplicacy
from frappe.model.document import Document


class HKMVoucherType(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF
        from hkm.erpnext___custom.doctype.hkm_voucher_type_account.hkm_voucher_type_account import (
            HKMVoucherTypeAccount,
        )

        defaults: DF.Table[HKMVoucherTypeAccount]
        voucher_type: DF.Data
    # end: auto-generated types

    def validate(self):
        validate_child_single_field_duplicacy(self, "defaults", "company")
        return
