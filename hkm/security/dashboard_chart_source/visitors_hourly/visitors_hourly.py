import frappe
from frappe import _
from frappe.utils.dashboard import cache_source


@frappe.whitelist()
@cache_source
def get(
    chart_name=None,
    chart=None,
    no_cache=None,
    filters=None,
    from_date=None,
    to_date=None,
    timespan=None,
    time_interval=None,
    heatmap_year=None,
):
    labels, datapoints = [], []
    filters = frappe.parse_json(filters)

    if filters:
        filters.update(
            {
                "from_date": filters.get("date_range") and filters.get("date_range")[0],
                "to_date": filters.get("date_range") and filters.get("date_range")[1],
            }
        )

    visitors_filters = ""
    if filters:
        visitors_filters += f"""
                         AND DATE(date) >= "{filters.get('from_date')}"
                         AND DATE(date) <= "{filters.get('to_date')}"
                         """

    hourly_visitors = frappe.db.sql(
        f"""
                    select DATE_FORMAT(time, '%H') AS hour, sum(count) as total
                    from `tabTemple Visitor Ping`
                    where 1
                    {visitors_filters}
                    group by hour
                    """,
        as_dict=1,
    )

    # AND DATE_FORMAT(creation, '%H') BETWEEN 7 AND 11
    for h in hourly_visitors:
        labels.append(_(h.get("hour")))
        datapoints.append(h.get("total"))

    return {
        "labels": labels,
        "datasets": [{"name": _("Visitors"), "values": datapoints}],
        "type": "bar",
    }
