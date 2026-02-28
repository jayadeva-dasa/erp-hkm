# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from .constants import SUMMARY, ONLY_INCOME, ONLY_EXPENSE, NET_PROFIT


class ColumnBuilder:
    """Class to build report columns with common logic"""
    
    @staticmethod
    def build_summary_columns(doc):
        columns = [
            {
                "fieldname": doc.dimension,
                "label": _(doc.dimension_meta.name),
                "fieldtype": "Link",
                "options": doc.dimension_meta.name,
                "width": 300,
            },
            {
                "fieldname": "total_inc",
                "label": _("<center>Total (Income)</center>"),
                "fieldtype": "Currency",
                "width": 150,
            },
            {
                "fieldname": "total_exp",
                "label": _("<center>Total (Expense)</center>"),
                "fieldtype": "Currency",
                "width": 150,
            },
        ]
        return columns
    
    @staticmethod
    def build_detailed_columns(doc):
        columns = [
            {
                "fieldname": "posting_date",
                "label": _("Date"),
                "fieldtype": "Date",
                "width": 150,
            },
            {
                "fieldname": "company",
                "label": _("Company"),
                "fieldtype": "Data",
                "width": 150,
            },
            {
                "fieldname": "voucher_type",
                "label": _("Voucher Type"),
                "fieldtype": "Data",
                "width": 150,
            },
            {
                "fieldname": "voucher_no",
                "label": _("Voucher No"),
                "fieldtype": "HTML",
                "width": 150,
            },
            {
                "fieldname": doc.dimension,
                "label": _(doc.dimension_meta.name),
                "fieldtype": "Link",
                "options": doc.dimension_meta.name,
                "width": 80,
            },
            {
                "fieldname": "account_head",
                "label": _("Account Head"),
                "fieldtype": "Link",
                "options": "Account",
                "width": 180,
            },
            {
                "fieldname": "amount",
                "label": _("Amount"),
                "fieldtype": "Currency",
                "width": 130,
            },
            {
                "fieldname": "remarks",
                "label": _("Remarks"),
                "fieldtype": "Data",
                "width": 150,
            },
            {
                "fieldname": "files_html",
                "label": _("Attachments"),
                "fieldtype": "HTML",
                "width": 300,
            },
        ]
        return columns
    
    
    
    
    
    
    
    
    
    
    
    

    @staticmethod
    def build_base_columns(name_field="name", name_label="Name"):
        """Build base columns for reports"""
        return [
            {
                "fieldname": name_field,
                "label": _(name_label),
                "fieldtype": "Data",
                "width": 300,
            },
        ]

    @staticmethod
    def add_total_columns(columns, report_type):
        """Add total columns based on report type"""
        if report_type == SUMMARY:
            columns.extend(
                [
                    {
                        "fieldname": "horizontal_total_inc",
                        "label": "<center>Total (Income)</center>",
                        "fieldtype": "Currency",
                        "options": "Currency",
                        "precision": 0,
                        "width": 150,
                    },
                    {
                        "fieldname": "horizontal_total_exp",
                        "label": "<center>Total (Expense)</center>",
                        "fieldtype": "Currency",
                        "options": "Currency",
                        "precision": 0,
                        "width": 150,
                    },
                ]
            )

        else:

            if report_type == ONLY_EXPENSE:
                key = "horizontal_total_exp"
            elif report_type == NET_PROFIT:
                key = "horizontal_total_net"
            else:
                key = "horizontal_total_inc"

            columns.extend(
                [
                    {
                        "fieldname": key,
                        "label": "<center>Total</center>",
                        "fieldtype": "Currency",
                        "options": "Currency",
                        "precision": 0,
                        "width": 150,
                    }
                ]
            )

        return columns

    @staticmethod
    def add_month_columns(columns, months, report_type, include_adjustment = None , internal_adjustment_type = None):
        """Add month columns based on report type"""
        for month in months:
            if report_type == SUMMARY:
                columns.extend(
                    [
                        {
                            "fieldname": month.key + "_inc",
                            "label": month.label + " (Income)",
                            "fieldtype": "Currency",
                            "options": "Currency",
                            "precision": 0,
                            "width": 150,
                        },
                        {
                            "fieldname": month.key + "_exp",
                            "label": month.label + " (Expense)",
                            "fieldtype": "Currency",
                            "options": "Currency",
                            "precision": 0,
                            "width": 150,
                        },
                    ]
                )
            elif report_type == ONLY_INCOME:
                label = " (Main)" if include_adjustment else ""
                columns.extend(
                    [
                        {
                            "fieldname": month.key + "_inc",
                            "label": month.label + label,
                            "fieldtype": "Currency",
                            "options": "Currency",
                            "precision": 0,
                            "width": 150,
                        },
                    ]
                )
                if include_adjustment:
                    if not internal_adjustment_type:
                        adj_type = frappe.get_all("Internal Adjustment Type" , pluck="name")
                        adj_type.append("Unknown")
                        for i in adj_type:
                            columns.extend(
                                [
                                    {
                                        "fieldname": month.key + "_" + frappe.scrub(i) + "_inc_adj",
                                        "label": month.label + " (" + i + ")",
                                        "fieldtype": "Currency",
                                        "options": "Currency",
                                        "precision": 0,
                                        "width": 150,
                                    },
                                ]
                            )
                    else:
                        for i in internal_adjustment_type:
                            columns.extend(
                                [
                                    {
                                        "fieldname": month.key + "_" + frappe.scrub(i) + "_inc_adj",
                                        "label": month.label + " (" + i + ")",
                                        "fieldtype": "Currency",
                                        "options": "Currency",
                                        "precision": 0,
                                        "width": 150,
                                    },
                                ]
                            )

            elif report_type == ONLY_EXPENSE:
                label = " (Main)" if include_adjustment else ""
                columns.extend(
                    [
                        {
                            "fieldname": month.key + "_exp",
                            "label": month.label + label,
                            "fieldtype": "Currency",
                            "options": "Currency",
                            "precision": 0,
                            "width": 150,
                        },
                    ]
                )
                if include_adjustment:
                    if not internal_adjustment_type:
                        adj_type = frappe.get_all("Internal Adjustment Type" , pluck="name")
                        adj_type.append("Unknown")
                        for i in adj_type:
                            columns.extend(
                                [
                                    {
                                        "fieldname": month.key + "_" + frappe.scrub(i) + "_exp_adj",
                                        "label": month.label + " (" + i + ")",
                                        "fieldtype": "Currency",
                                        "options": "Currency",
                                        "precision": 0,
                                        "width": 150,
                                    },
                                ]
                            )
                    else:
                        for i in internal_adjustment_type:
                            columns.extend(
                                [
                                    {
                                        "fieldname": month.key + "_" + frappe.scrub(i) + "_exp_adj",
                                        "label": month.label + " (" + i + ")",
                                        "fieldtype": "Currency",
                                        "options": "Currency",
                                        "precision": 0,
                                        "width": 150,
                                    },
                                ]
                            )
                
                
            elif report_type == NET_PROFIT:
                columns.extend(
                    [
                        {
                            "fieldname": month.key + "_net",
                            "label": month.label,
                            "fieldtype": "Currency",
                            "options": "Currency",
                            "precision": 0,
                            "width": 150,
                        }
                    ]
                )
        return columns
