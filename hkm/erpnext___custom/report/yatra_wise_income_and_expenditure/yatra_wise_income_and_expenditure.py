# Copyright (c) 2026, HKM and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt

NO_YATRA = "(No Yatra)"
NO_BATCH = "(No Batch)"
SHOW_ENTRIES = "Yatra, Batch, Account and Entries"
SHOW_BATCH = ("Yatra and Batch", "Yatra, Batch and Account", SHOW_ENTRIES)
SHOW_ACCOUNT = ("Yatra, Batch and Account", SHOW_ENTRIES)
# validated categorical pair (light and dark surfaces); green/red stay reserved for status
INCOME_COLOR, EXPENDITURE_COLOR = "#2a78d6", "#d95926"


def execute(filters=None):
    filters = frappe._dict(filters or {})
    if filters.from_date > filters.to_date:
        frappe.throw(_("From Date must be before To Date"))

    currency = frappe.get_cached_value("Company", filters.company, "default_currency")
    data, total = get_data(filters, currency)
    return (
        get_columns(filters),
        data,
        None,
        get_chart(data, currency),
        get_report_summary(total, currency),
    )


def get_columns(filters):
    show_entries = filters.show == SHOW_ENTRIES
    columns = [
        {
            "fieldname": "label",
            "label": _("Yatra / Batch / Account / Voucher") if show_entries else _("Yatra / Batch / Account"),
            "fieldtype": "Data",
            "width": 420,
        },
    ]
    if show_entries:
        columns += [
            {
                "fieldname": "posting_date",
                "label": _("Posting Date"),
                "fieldtype": "Date",
                "width": 110,
            },
            {
                "fieldname": "voucher_type",
                "label": _("Voucher Type"),
                "fieldtype": "Data",
                "width": 140,
            },
        ]
    columns += [
        {
            "fieldname": "income",
            "label": _("Income"),
            "fieldtype": "Currency",
            "options": "currency",
            "width": 160,
        },
        {
            "fieldname": "expenditure",
            "label": _("Expenditure"),
            "fieldtype": "Currency",
            "options": "currency",
            "width": 160,
        },
        {
            "fieldname": "surplus",
            "label": _("Surplus / (Deficit)"),
            "fieldtype": "Currency",
            "options": "currency",
            "width": 170,
        },
        {
            "fieldname": "margin",
            "label": _("Margin %"),
            "fieldtype": "Percent",
            "width": 100,
        },
        {
            "fieldname": "currency",
            "label": _("Currency"),
            "fieldtype": "Link",
            "options": "Currency",
            "hidden": 1,
        },
    ]
    if show_entries:
        columns += [
            {
                "fieldname": "party_type",
                "label": _("Party Type"),
                "fieldtype": "Data",
                "hidden": 1,
            },
            {
                "fieldname": "party",
                "label": _("Party"),
                "fieldtype": "Dynamic Link",
                "options": "party_type",
                "width": 180,
            },
            {
                "fieldname": "against",
                "label": _("Against Account"),
                "fieldtype": "Data",
                "width": 180,
            },
            {
                "fieldname": "remarks",
                "label": _("Remarks"),
                "fieldtype": "Data",
                "width": 300,
            },
        ]
    return columns


def get_gl_amounts(filters, entries=False):
    """Income and expense per Yatra, Batch and account, or each GL entry when `entries`.
    Year closing entries are left out, so a closed year still shows its income and expenditure."""
    conditions = []
    values = {
        "company": filters.company,
        "from_date": filters.from_date,
        "to_date": filters.to_date,
        "no_yatra": NO_YATRA,
        "no_batch": NO_BATCH,
    }
    if filters.pk_yatra:
        conditions.append("gle.pk_yatra in %(pk_yatra)s")
        values["pk_yatra"] = tuple(filters.pk_yatra)
    if filters.pk_yatra_batch:
        conditions.append("gle.pk_yatra_batch in %(pk_yatra_batch)s")
        values["pk_yatra_batch"] = tuple(filters.pk_yatra_batch)
    if not filters.include_untagged:
        conditions.append("ifnull(gle.pk_yatra, '') != ''")

    if entries:
        amounts = """gle.name, gle.posting_date, gle.voucher_type, gle.voucher_no,
            gle.party_type, gle.party, gle.against, gle.remarks,
            gle.debit, gle.credit"""
        group_by = ""
    else:
        amounts = "sum(gle.debit) as debit, sum(gle.credit) as credit"
        group_by = "group by yatra, batch, gle.account, acc.root_type"

    return frappe.db.sql(
        """
        select
            ifnull(nullif(gle.pk_yatra, ''), %(no_yatra)s) as yatra,
            ifnull(nullif(gle.pk_yatra_batch, ''), %(no_batch)s) as batch,
            gle.account,
            acc.root_type,
            {amounts}
        from `tabGL Entry` gle
        join `tabAccount` acc on acc.name = gle.account
        where gle.company = %(company)s
            and gle.is_cancelled = 0
            and gle.voucher_type != 'Period Closing Voucher'
            and gle.posting_date between %(from_date)s and %(to_date)s
            and acc.root_type in ('Income', 'Expense')
            {conditions}
        {group_by}
        """.format(
            amounts=amounts,
            conditions="".join(f" and {c}" for c in conditions),
            group_by=group_by,
        ),
        values,
        as_dict=True,
    )


def get_data(filters, currency):
    """Tree rows: Yatra, then Batch, then account, then each entry, as the "Show" filter asks.
    Untagged entries go last, under (No Yatra) / (No Batch)."""
    show_batch = filters.show in SHOW_BATCH
    show_account = filters.show in SHOW_ACCOUNT
    show_entries = filters.show == SHOW_ENTRIES
    rows, by_name = [], {}

    def node(name, parent, label, indent, **extra):
        if name not in by_name:
            by_name[name] = frappe._dict(
                name=name,
                parent=parent,
                label=label,
                indent=indent,
                income=0.0,
                expenditure=0.0,
                currency=currency,
                **extra,
            )
            rows.append(by_name[name])
        return by_name[name]

    total = frappe._dict(income=0.0, expenditure=0.0)
    amounts = sorted(
        get_gl_amounts(filters, show_entries),
        key=lambda d: (
            d.yatra == NO_YATRA,
            d.yatra,
            d.batch == NO_BATCH,
            d.batch,
            d.account,
            d.posting_date or "",
            d.voucher_no or "",
        ),
    )
    for d in amounts:
        income = flt(d.credit - d.debit) if d.root_type == "Income" else 0.0
        expenditure = flt(d.debit - d.credit) if d.root_type == "Expense" else 0.0

        path = [node(d.yatra, None, d.yatra, 0)]
        if show_batch:
            batch_name = f"{d.yatra}::{d.batch}"
            path.append(node(batch_name, d.yatra, d.batch, 1))
            if show_account:
                account_name = f"{batch_name}::{d.account}"
                path.append(
                    node(
                        account_name,
                        batch_name,
                        d.account,
                        2,
                        account=d.account,
                        yatra=d.yatra,
                        batch=d.batch,
                        # the General Ledger can't filter on "no Yatra / no Batch"
                        drill_down=int(d.yatra != NO_YATRA and d.batch != NO_BATCH),
                    )
                )
                if show_entries:
                    path.append(
                        node(
                            d.name,
                            account_name,
                            d.voucher_no,
                            3,
                            root_type=d.root_type,
                            posting_date=d.posting_date,
                            voucher_type=d.voucher_type,
                            voucher_no=d.voucher_no,
                            party_type=d.party_type,
                            party=d.party,
                            against=d.against,
                            remarks=d.remarks,
                        )
                    )
        for row in path + [total]:
            row.income += income
            row.expenditure += expenditure

    total.update(name="Total", parent=None, label=_("Total"), indent=0, currency=currency)
    for row in rows + [total]:
        row.income, row.expenditure = flt(row.income, 2), flt(row.expenditure, 2)
        if row.voucher_no:
            # an entry shows only its own amount, in its account's column
            row["expenditure" if row.root_type == "Income" else "income"] = None
            continue
        row.surplus = flt(row.income - row.expenditure, 2)
        row.margin = flt(row.surplus / row.income * 100, 2) if row.income else None
    return (rows + [total] if rows else []), total


def get_chart(data, currency):
    yatras = [d for d in data if d.indent == 0 and d.name != "Total"]
    if not yatras:
        return None
    return {
        "data": {
            "labels": [d.label for d in yatras],
            "datasets": [
                {"name": _("Income"), "values": [d.income for d in yatras]},
                {"name": _("Expenditure"), "values": [d.expenditure for d in yatras]},
            ],
        },
        "type": "bar",
        "colors": [INCOME_COLOR, EXPENDITURE_COLOR],
        "fieldtype": "Currency",
        "options": "currency",
        "currency": currency,
    }


def get_report_summary(total, currency):
    return [
        {
            "value": total.income,
            "label": _("Total Income"),
            "datatype": "Currency",
            "currency": currency,
        },
        {"type": "separator", "value": "-"},
        {
            "value": total.expenditure,
            "label": _("Total Expenditure"),
            "datatype": "Currency",
            "currency": currency,
        },
        {"type": "separator", "value": "=", "color": "blue"},
        {
            "value": total.surplus,
            "label": _("Surplus") if total.surplus >= 0 else _("Deficit"),
            "indicator": "Green" if total.surplus >= 0 else "Red",
            "datatype": "Currency",
            "currency": currency,
        },
    ]
