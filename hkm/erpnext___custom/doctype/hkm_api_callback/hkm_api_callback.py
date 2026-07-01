# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

# import frappe
import json
import time
import uuid
import frappe
from frappe.model.document import Document


class HKMAPICALLBACK(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        api_response: DF.JSON | None
        document_payload: DF.JSON | None
        integration_doctype: DF.Link
        order_number: DF.Data
        refrence_docname: DF.DynamicLink | None
        refrence_doctype: DF.Link
    # end: auto-generated types
    
    def before_save(self):
        pass