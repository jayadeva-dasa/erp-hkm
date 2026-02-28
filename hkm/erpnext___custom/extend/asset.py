import frappe
from frappe import _
from frappe.model.document import Document


def on_submit(doc, method=None):
    if doc.get("secondary_custodian"):
        frappe.get_doc(
            {
                "doctype": "HKM Asset Movement",
                "asset": doc.name,
                "department": doc.custodian_department,
                "from_sub_custodian": doc.secondary_custodian,
                "to_sub_custodian": doc.secondary_custodian,
                "movement_date": doc.purchase_date,
            }
        ).insert().submit()
    return


def validate(doc, method=None):
    if doc.get("specifications"):
        validate_specifications(doc)
    return


def validate_specifications(doc):
    """Validate asset specifications"""
    for spec in doc.specifications:
        spec_doc = frappe.get_doc("HKM Asset Specification", spec.specification)

        if spec_doc.asset_category != doc.asset_category:
            frappe.throw(
                _("Specification {0} not valid for category {1}").format(
                    spec.specification, doc.asset_category
                )
            )

        if spec_doc.is_mandatory and not spec.value:
            frappe.throw(
                _("Specification {0} is mandatory").format(spec.specification_name)
            )
