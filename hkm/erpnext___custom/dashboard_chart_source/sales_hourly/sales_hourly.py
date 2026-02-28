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

    filters.update({"from_date": filters.get("date_range") and filters.get("date_range")[0], "to_date": filters.get("date_range") and filters.get("date_range")[1]})

    pos_filters = ""
    if filters and filters.get("pos_profile"):
        pos_filters += f'''
                         AND DATE(posting_date) >= "{filters.get('from_date')}"
                         AND DATE(posting_date) <= "{filters.get('to_date')}"
                         AND pos_profile = "{filters.get("pos_profile")}"
                         '''
    
    hourly_invoices = frappe.db.sql(f"""
                    select DATE_FORMAT(posting_time, '%H') AS hour, sum(grand_total) as total
                    from `tabPOS Invoice`
                    where docstatus = 1
                    {pos_filters}
                    group by hour
                    """, as_dict = 1)

     # AND DATE_FORMAT(creation, '%H') BETWEEN 7 AND 11
    for h in hourly_invoices:
        labels.append(_(h.get("hour")))
        datapoints.append(h.get("total"))

    return {
        "labels": labels,
        "datasets": [{"name": _("Sales"), "values": datapoints}],
        "type": "bar",
    }