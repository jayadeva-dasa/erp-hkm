"""Guarded replacements for the whitelisted save / submit / cancel / workflow endpoints.

Registered through `override_whitelisted_methods` in hooks.py. Each wrapper calls the
original Frappe method unchanged and only intervenes when it raises, so successful saves
behave exactly as before.
"""

import frappe

from .core import handle_exception


def _run(fn, doc_ref=None, doctype_ref=None, **kwargs):
    try:
        return fn(**kwargs)
    except Exception as exc:
        handle_exception(exc, doc=doc_ref, doctype=doctype_ref)
        raise


@frappe.whitelist(methods=["POST", "PUT"])
def savedocs(doc, action):
    from frappe.desk.form.save import savedocs as original

    return _run(original, doc, doc=doc, action=action)


@frappe.whitelist(methods=["POST", "PUT"])
def cancel(doctype=None, name=None, workflow_state_fieldname=None, workflow_state=None):
    from frappe.desk.form.save import cancel as original

    return _run(
        original,
        doctype_ref=doctype,
        doctype=doctype,
        name=name,
        workflow_state_fieldname=workflow_state_fieldname,
        workflow_state=workflow_state,
    )


@frappe.whitelist(methods=["POST", "PUT"])
def client_insert(doc=None):
    from frappe.client import insert as original

    return _run(original, doc, doc=doc)


@frappe.whitelist(methods=["POST", "PUT"])
def client_save(doc):
    from frappe.client import save as original

    return _run(original, doc, doc=doc)


@frappe.whitelist(methods=["POST", "PUT"])
def client_submit(doc):
    from frappe.client import submit as original

    return _run(original, doc, doc=doc)


@frappe.whitelist(methods=["POST", "PUT"])
def client_cancel(doctype, name):
    from frappe.client import cancel as original

    return _run(original, doctype_ref=doctype, doctype=doctype, name=name)


@frappe.whitelist(methods=["POST", "PUT"])
def client_set_value(doctype, name, fieldname, value=None):
    from frappe.client import set_value as original

    return _run(original, doctype_ref=doctype, doctype=doctype, name=name, fieldname=fieldname, value=value)


@frappe.whitelist()
def apply_workflow(doc, action):
    from frappe.model.workflow import apply_workflow as original

    return _run(original, doc, doc=doc, action=action)


@frappe.whitelist()
def make_mapped_doc(method, source_name, selected_children=None, args=None):
    from frappe.model.mapper import make_mapped_doc as original

    return _run(
        original,
        method=method,
        source_name=source_name,
        selected_children=selected_children,
        args=args,
    )
