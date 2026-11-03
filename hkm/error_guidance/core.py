"""Turn terse / crashing save errors into messages that say what is wrong and how to fix it.

Entry point is `handle_exception(exc, doc, doctype)`, called from the guarded API wrappers
in `hkm.error_guidance.api`. It either returns None (caller re-raises the original
exception, with its message log already improved) or raises a new, explicit ValidationError.
"""

import json
import re
import traceback

import frappe
from frappe import _
from frappe.utils import cstr, strip_html

from .rules import (
    DEFAULT_FIELD_HINT,
    EXCEPTION_HINTS,
    FIELD_TYPE_HINTS,
    HINT_RULES,
    LINK_DOCTYPE_HINTS,
)

HINT_MARKER = "How to fix"

_MISSING_TABLE = re.compile(r"Data missing in table (?P<label>.+)$")
_MISSING_ROW = re.compile(
    r"(?:<b>|<strong>)(?P<dt>.+?)(?:</b>|</strong>) Row #(?P<idx>\d+): Value missing for: (?P<label>.+)$"
)
_MISSING_FIELD = re.compile(r"Value missing for (?P<dt>[^:]+): (?P<label>.+)$")

# frappe frames that are never the interesting part of a traceback
_BORING_FRAMES = ("/frappe/frappe/model/", "/frappe/frappe/handler", "/frappe/frappe/__init__", "error_guidance")


# ---------------------------------------------------------------------------------------
# public entry point
# ---------------------------------------------------------------------------------------
def handle_exception(exc, doc=None, doctype=None):
    doc = _load_doc(doc)
    doctype = doctype or (doc.doctype if doc else None)

    if isinstance(exc, frappe.DoesNotExistError):
        if frappe.local.message_log or cstr(exc).strip():
            _improve_validation_error(exc, doctype)
            return
        _log(exc, doctype, doc)
        _throw(
            _("A record this document depends on no longer exists (it may have been deleted or renamed)."),
            _("Reload the form, re-select the linked values (Supplier, Item, Address, ...) and save again."),
            title=_("Linked record not found"),
        )

    if isinstance(exc, frappe.ValidationError):
        _improve_validation_error(exc, doctype)
        return

    if isinstance(exc, frappe.PermissionError):
        if not frappe.local.message_log:
            _throw(
                _("You don't have permission to do this on {0}.").format(doctype or _("this document")),
                _(
                    "Ask your System Manager to give your role the required permission "
                    "(Role Permission Manager) or to do it for you."
                ),
                title=_("Permission denied"),
            )
        return

    if isinstance(exc, frappe.DuplicateEntryError):
        _log(exc, doctype, doc)
        dt, name = (list(exc.args) + [None, None])[:2]
        _throw(
            _("A {0} named '{1}' already exists.").format(dt or doctype, name),
            _("Open the existing record instead of creating a new one, or use a different name."),
            title=_("Duplicate entry"),
        )

    if isinstance(exc, frappe.QueryDeadlockError) or _db_error_code(exc) in (1205, 1213):
        _throw(
            _("The system was busy with another update, so nothing was saved."),
            _("Wait a few seconds and click Save again."),
            title=_("Please retry"),
        )

    if _is_framework_exception(exc):
        return

    _handle_crash(exc, doc, doctype)


# ---------------------------------------------------------------------------------------
# validation errors that already carry a message
# ---------------------------------------------------------------------------------------
def _improve_validation_error(exc, doctype):
    log = frappe.local.message_log
    if not log:
        # raise frappe.ValidationError with no text at all
        text = cstr(exc).strip()
        if text:
            _append_hint_to_new_message(text)
        else:
            _log(exc, doctype, None)
            _throw(
                _("A validation rule blocked this action but did not say why."),
                _(
                    "Check that the document is in the right workflow/approval state and that "
                    "all required details are filled. If it still fails, contact IT and quote the time of this error."
                ),
                title=_("Cannot complete action"),
            )
        return

    if isinstance(exc, frappe.MandatoryError):
        _consolidate_mandatory(doctype)

    for m in frappe.local.message_log:
        if isinstance(m, dict) and m.get("message") and HINT_MARKER not in m["message"]:
            hint = _find_hint(m["message"])
            if hint:
                m["message"] = f"{m['message']}<br><br><b>{_(HINT_MARKER)}:</b> {hint}"


def _append_hint_to_new_message(text):
    hint = _find_hint(text)
    msg = text if not hint else f"{text}<br><br><b>{_(HINT_MARKER)}:</b> {hint}"
    frappe.local.message_log.append({"message": msg, "title": _("Error"), "indicator": "red"})


def _find_hint(message):
    plain = strip_html(cstr(message)).replace("&amp;", "&")
    for pattern, fix in HINT_RULES:
        match = re.search(pattern, plain, re.IGNORECASE | re.DOTALL)
        if match:
            groups = [g or "" for g in match.groups()]
            try:
                return fix.format(*([""] + [g.strip() for g in groups]))
            except (IndexError, KeyError):
                return fix
    return None


# ---------------------------------------------------------------------------------------
# missing mandatory fields -> one clear checklist
# ---------------------------------------------------------------------------------------
def _consolidate_mandatory(doctype):
    items, others = [], []
    for m in frappe.local.message_log:
        text = cstr(m.get("message") if isinstance(m, dict) else m).strip()
        parsed = _parse_missing(text)
        if parsed:
            items.append(parsed)
        else:
            others.append(m)

    if not items:
        return

    lines = [_missing_line(doctype, *item) for item in items]
    html = (
        "<p>{}</p><ol>{}</ol><p>{}</p>".format(
            _("{0} cannot be saved because required information is missing:").format(
                frappe.bold(_(doctype)) if doctype else _("This document")
            ),
            "".join(f"<li>{line}</li>" for line in lines),
            _("Fill in the items above (they are highlighted in red on the form) and save again."),
        )
    )
    frappe.local.message_log = [
        {"message": html, "title": _("Missing required information"), "indicator": "red"},
        *others,
    ]


def _parse_missing(text):
    text = re.sub(r"^Error:\s*", "", text)
    if m := _MISSING_TABLE.search(text):
        return ("table", None, m["label"].strip(), None)
    if m := _MISSING_ROW.search(text):
        return ("row", m["dt"].strip(), m["label"].strip(), int(m["idx"]))
    if m := _MISSING_FIELD.search(strip_html(text)):
        return ("field", m["dt"].strip(), m["label"].strip(), None)
    return None


def _missing_line(parent_doctype, kind, dt, label, idx):
    if kind == "table":
        df = _find_field(parent_doctype, label)
        return "<b>{}</b> &mdash; {}".format(label, FIELD_TYPE_HINTS["Table"])

    df = _find_field(dt, label)
    how = _how_to_fill(df)

    if kind == "row":
        table = _table_label_for_child(parent_doctype, dt) or dt
        return "{} <b>{}</b>, {} {}: <b>{}</b> &mdash; {}".format(
            _("Table"), table, _("Row"), idx, label, how
        )

    return f"<b>{label}</b> &mdash; {how}"


def _how_to_fill(df):
    if not df:
        return DEFAULT_FIELD_HINT
    if df.fieldtype == "Link" and df.options in LINK_DOCTYPE_HINTS:
        return LINK_DOCTYPE_HINTS[df.options]
    template = FIELD_TYPE_HINTS.get(df.fieldtype, DEFAULT_FIELD_HINT)
    return template.format(options=df.options) if "{options}" in template else template


def _find_field(doctype, label):
    if not doctype:
        return None
    try:
        for df in frappe.get_meta(doctype).fields:
            if label in (df.label, _(df.label)):
                return df
    except Exception:
        pass
    return None


def _table_label_for_child(parent_doctype, child_doctype):
    if not parent_doctype:
        return None
    try:
        for df in frappe.get_meta(parent_doctype).get_table_fields():
            if df.options == child_doctype:
                return df.label
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------------------
# unexpected crashes (TypeError, AttributeError, DB errors, ...)
# ---------------------------------------------------------------------------------------
def _handle_crash(exc, doc, doctype):
    _log(exc, doctype, doc)

    db_code = _db_error_code(exc)
    if db_code:
        what, fix = _explain_db_error(exc, db_code, doc, doctype)
        _throw(what, fix, title=_("Could not save"))

    missing = _missing_mandatory(doc, doctype)
    suspects = _suspect_fields(exc, doc)
    what, fix = EXCEPTION_HINTS.get(
        type(exc).__name__,
        (
            _("The system hit an unexpected problem while processing this document."),
            _("Check that all required details are filled correctly and try again."),
        ),
    )

    body = [f"<p>{what}</p>"]
    if missing:
        body.append(
            "<p><b>{}</b></p><ol>{}</ol>".format(
                _("These required fields are empty:"), "".join(f"<li>{line}</li>" for line in missing)
            )
        )
    elif suspects:
        body.append(
            "<p><b>{}</b> {}</p>".format(
                _("Most likely cause &mdash; these fields are empty:"), ", ".join(f"<b>{s}</b>" for s in suspects)
            )
        )
    if missing:
        fix = _("Fill in the fields listed above and save again.")
    body.append(f"<p><b>{_(HINT_MARKER)}:</b> {fix}</p>")
    body.append(
        "<p class='text-muted small'>{}: {}: {}</p>".format(
            _("Technical detail for IT"), type(exc).__name__, frappe.utils.escape_html(cstr(exc))[:200]
        )
    )
    _throw_html("".join(body), title=_("Could not save {0}").format(_(doctype)) if doctype else _("Could not save"))


def _missing_mandatory(doc, doctype):
    if not doc:
        return []
    out = []
    try:
        entries = list(doc._get_missing_mandatory_fields())
        for child in doc.get_all_children():
            entries.extend(child._get_missing_mandatory_fields())
        for _fieldname, msg in entries:
            parsed = _parse_missing(msg)
            if parsed:
                out.append(_missing_line(doctype, *parsed))
    except Exception:
        pass
    return out


def _suspect_fields(exc, doc):
    """Fields mentioned on the source line that crashed which are empty on the document."""
    if not doc:
        return []
    try:
        frames = [
            f
            for f in traceback.extract_tb(exc.__traceback__)
            if "/apps/" in f.filename and not any(b in f.filename for b in _BORING_FRAMES)
        ]
        if not frames:
            return []
        line = frames[-1].line or ""
        names = re.findall(r"\b(?:self|doc|d|row|item|args)\.(\w+)", line)
        names += re.findall(r"get\(\s*[\"'](\w+)[\"']", line)
        names += re.findall(r"\[\s*[\"'](\w+)[\"']\s*\]", line)
        if isinstance(exc, KeyError) and exc.args:
            names.append(cstr(exc.args[0]))

        labels = []
        for name in dict.fromkeys(names):
            label = _empty_field_label(doc, name)
            if label and label not in labels:
                labels.append(label)
        return labels[:5]
    except Exception:
        return []


def _empty_field_label(doc, fieldname):
    df = doc.meta.get_field(fieldname)
    if df and df.fieldtype not in ("Table", "Check") and not doc.get(fieldname):
        return _(df.label)
    for table in doc.meta.get_table_fields():
        child_meta = frappe.get_meta(table.options)
        df = child_meta.get_field(fieldname)
        rows = doc.get(table.fieldname) or []
        if df and rows and any(not r.get(fieldname) for r in rows):
            return f"{_(table.label)} &rarr; {_(df.label)}"
    return None


def _db_error_code(exc):
    try:
        import pymysql

        if isinstance(exc, pymysql.Error) and exc.args and isinstance(exc.args[0], int):
            return exc.args[0]
    except Exception:
        pass
    return None


def _explain_db_error(exc, code, doc, doctype):
    text = cstr(exc)
    column = (re.search(r"column '(\w+)'", text) or [None, None])[1]
    label = _label_for(doc, doctype, column) if column else None
    field = f"<b>{label}</b>" if label else (f"<b>{column}</b>" if column else _("one of the fields"))

    if code == 1406:
        return (
            _("The text entered in {0} is too long.").format(field),
            _("Shorten the text (for long notes use a Text field or the Remarks box) and save again."),
        )
    if code == 1264:
        return (
            _("The number entered in {0} is too large.").format(field),
            _("Check for an extra zero or a misplaced decimal point and enter a smaller value."),
        )
    if code in (1366, 1292):
        return (
            _("{0} contains a value in the wrong format.").format(field),
            _("Use plain digits for numbers and a valid date for date fields."),
        )
    if code == 1048:
        return (
            _("{0} cannot be empty.").format(field),
            _("Fill in {0} and save again.").format(field),
        )
    if code == 1062:
        return (
            _("A record with the same name or unique value already exists."),
            _("Open the existing record, or change the name/unique value you entered."),
        )
    return (
        _("The database rejected this save."),
        _("Reload the form and try again. If it keeps failing, contact IT with the time of this error."),
    )


def _label_for(doc, doctype, fieldname):
    try:
        meta = frappe.get_meta(doctype or doc.doctype)
        if df := meta.get_field(fieldname):
            return _(df.label)
        for table in meta.get_table_fields():
            if df := frappe.get_meta(table.options).get_field(fieldname):
                return f"{_(table.label)} &rarr; {_(df.label)}"
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------------------
def _is_framework_exception(exc):
    """frappe's own control-flow / auth exceptions - leave them alone."""
    return type(exc).__module__.startswith("frappe.") and not isinstance(exc, KeyError)


def _load_doc(doc):
    try:
        if isinstance(doc, str):
            doc = json.loads(doc)
        if isinstance(doc, dict) and doc.get("doctype"):
            return frappe.get_doc(doc)
    except Exception:
        pass
    return doc if hasattr(doc, "meta") else None


def _log(exc, doctype, doc):
    try:
        frappe.log_error(
            title=f"Save failed: {doctype or ''} {type(exc).__name__}: {cstr(exc)[:80]}",
            reference_doctype=doctype,
            reference_name=getattr(doc, "name", None),
            defer_insert=True,
        )
    except Exception:
        pass


def _throw(what, fix, title=None):
    _throw_html(f"<p>{what}</p><p><b>{_(HINT_MARKER)}:</b> {fix}</p>", title=title)


def _throw_html(html, title=None):
    frappe.local.message_log = []
    frappe.throw(html, title=title or _("Error"))
