# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe


def dummy():
    filters = frappe._dict({
        "company": "Hare Krishna Movement Jaipur",
        "from_fiscal_year": "2023-2024",
        "to_fiscal_year": "2024-2025",
    })
    AssetLifewise(filters)

def execute(filters=None):
    columns, data = [], []
    AssetLifewise(filters)
    return columns, data


class AssetLifewise:
    def __init__(self,filters):
        self.filters = filters
        self.validate_filters()
        self.assets_map = {}
        self.category_life_map = {}
        self.get_assets()
        self.get_categorywise_data()
        print(self.assets_map)
        print(self.category_life_map)
    
    def validate_filters(self):
        self.start_fy_dates = self.get_period_dates(self.filters.from_fiscal_year)
        self.end_fy_dates = self.get_period_dates(self.filters.to_fiscal_year)
  
        if self.start_fy_dates[1] > self.end_fy_dates[0]:
            frappe.throw("From Fiscal Year cannot be greater than To Fiscal Year")

    def get_assets(self):
        assets = frappe.get_all(
            "Asset",
            pluck="name",
            filters={
                "docstatus": 1,
                "company": self.filters.company,
                "available_for_use_date": ("<", self.end_fy_dates[1])
            }
        )
        
        for asset in assets:
            asset_doc = frappe.get_doc("Asset", asset)
            a_info = {
                "asset_id": asset_doc.name,
                "category": asset_doc.asset_category,
                "use_date": asset_doc.available_for_use_date,
                "purchase_amount": asset_doc.gross_purchase_amount
            }
            if asset_doc.calculate_depreciation:
                dep_schedules = asset_doc.finance_books
                total_number_of_depreciations = dep_schedules[0].total_number_of_depreciations
                frequency_of_depreciation = dep_schedules[0].frequency_of_depreciation
                life = int((total_number_of_depreciations*frequency_of_depreciation)/12)
                a_info["calculate_depreciation"] = True
                a_info["life"] = life
            else:
                a_info["calculate_depreciation"] = False
                a_info["life"] = "NA"
            
            total_dep
            
            self.assets_map.setdefault(asset_doc.name, a_info)
  
    def get_period_dates(self,fy):
        fy = frappe.db.get_value(
            "Fiscal Year", fy, ["year_start_date", "year_end_date"], as_dict=True
        )
        return fy.year_start_date, fy.year_end_date

    def get_categorywise_data(self):
        for asset in self.assets_map:
            category_life_str =  f"{self.assets_map[asset]['category']}-{self.assets_map[asset]['life']}"
            if category_life_str not in self.category_life_map:
                self.category_life_map.setdefault(category_life_str, frappe._dict({
                    "category": self.assets_map[asset]['category'],
                    "life": self.assets_map[asset]['life'],
                    "gross_block": 0,
                    "total_depreciation": 0
                }))
            
            self.category_life_map[category_life_str].gross_block += self.assets_map[asset]['purchase_amount']
        