import frappe


def get_all_assets():
    assets = frappe.get_all(
        "Asset",
        filters={
            "docstatus": 1,
            "calculate_depreciation": 1,
            "company": "Hare Krishna Movement Jaipur",
            "available_for_use_date":["<", "2025-04-01"]
        },
        fields=["name"],
    )

    for i, a in enumerate(assets):
        asset_doc = frappe.get_doc("Asset", a.name)
        dep_schedules = asset_doc.finance_books
        if not dep_schedules:
            frappe.throw(
                _("Asset {0} does not have any depreciation schedule").format(a.name)
            )
        total_number_of_depreciations = dep_schedules[0].total_number_of_depreciations
        frequency_of_depreciation = dep_schedules[0].frequency_of_depreciation
        life = (total_number_of_depreciations*frequency_of_depreciation)/12
        print(a.name,total_number_of_depreciations, frequency_of_depreciation, life)
        
        
