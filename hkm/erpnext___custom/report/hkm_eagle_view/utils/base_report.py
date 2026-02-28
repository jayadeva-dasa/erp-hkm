# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe
from hkm.erpnext___custom.report.hkm_eagle_view.utils.date_utils import validate_filters
from hkm.erpnext___custom.report.hkm_eagle_view.utils.query_optimizer import (
    PermissionCache,
)
from hkm.erpnext___custom.report.hkm_eagle_view.utils.report_formatters import (
    ReportFormatter,
)
from hkm.erpnext___custom.report.hkm_eagle_view.utils.constants import (
    FROM_DATE,
    TO_DATE,
    TIME_PERIOD,
    REPORT_TYPE,
    INCLUDE_ADJUSTMENT,
    INTERNAL_ADJUSTMENT_TYPE,
    INCLUDE_STOCK_ASSET,
    ONLY_INCOME,
    ONLY_EXPENSE,
    NET_PROFIT,
    Add_Income_Expense_total,
    Add_Income_total,
    Add_Expense_total,
    Add_Net_Profit_total,
    DIMENSION,
    ACCOUNT,
    DIMENSION_VALUE,
    TIME_PERIOD,
    INCLUDE_DISABLED_DIMENSION,
    HIDE_NOT_TAGGED_ENTRIES,
    EXCLUDE_PERIOD_CLOSING_ENTRIES,
    RENDER_AS_TREE_VIEW,
)
from hkm.erpnext___custom.report.hkm_eagle_view.utils.dimension_utils import (
    get_heads,
    get_proper_heads,
)


class BaseReport:
    def __init__(self, filters):
        self.filters = filters
        # Initialize permission cache (single query for entire report)
        self.permission_cache = PermissionCache()
        self._initialize_data()
        validate_filters(self.from_date, self.to_date, self.time_period)

    def _initialize_data(self):
        """Initialize report data and settings"""
        self._set_date_range()
        self._set_report_settings()
        self._set_dimension_settings()
        self._set_total_type()
        self._initialize_keys()

    def _set_date_range(self):
        """Set date range from filters"""
        self.from_date = self.filters.get(FROM_DATE)
        self.to_date = self.filters.get(TO_DATE)
        self.time_period = self.filters.get(TIME_PERIOD)

    def _set_report_settings(self):
        """Set report type and adjustment settings"""
        self.report_type = self.filters.get(REPORT_TYPE)
        self.include_adjustment = self._get_boolean_value(INCLUDE_ADJUSTMENT)
        self.internal_adjustment_type = self.filters.get(INTERNAL_ADJUSTMENT_TYPE)
        self.include_stock_asset = self._get_boolean_value(INCLUDE_STOCK_ASSET)
        self.exclude_period_closing_entries = self._get_boolean_value(
            EXCLUDE_PERIOD_CLOSING_ENTRIES
        )
        self.company = self.filters.get("company")

    def _set_dimension_settings(self):
        """Set dimension and account settings"""
        self.account = self.filters.get(ACCOUNT)
        self.dimension_meta = frappe.get_meta(self.filters.get(DIMENSION))

        self.dimension_meta.is_tree = (
            self.dimension_meta.is_tree
            if self.dimension_meta.is_tree and self.filters.get(RENDER_AS_TREE_VIEW)
            else 0
        )

        # Get the correct fieldname from Accounting Dimension doctype
        self.dimension = frappe.db.get_value(
            "Accounting Dimension",
            {"document_type": self.dimension_meta.name},
            "fieldname",
        )
        if not self.dimension:
            # Fallback to scrubbed name if not found in Accounting Dimension
            self.dimension = frappe.scrub(self.dimension_meta.name)
        self.selected_dimension_value = self.filters.get(DIMENSION_VALUE)
        self.include_disabled_dimension = self._get_boolean_value(
            INCLUDE_DISABLED_DIMENSION
        )

        self.accounting_dimension = frappe.get_all(
            "Accounting Dimension",
            filters={"document_type": ["!=", self.dimension_meta.name]},
            pluck="fieldname",
        )
        self.hide_not_tagged_entries = self._get_boolean_value(HIDE_NOT_TAGGED_ENTRIES)
        self.selected_dimension_value = get_proper_heads(
            self.dimension_meta, self.selected_dimension_value
        )
        self.tree = (
            0
            if self.dimension_meta.is_tree == 0
            and self.filters.get(RENDER_AS_TREE_VIEW)
            else 1
        )
        self.heads = get_heads(
            dimension_meta=self.dimension_meta,
            selected_head=self.selected_dimension_value,
            detailed=True,
            include_disabled_dimension=self.include_disabled_dimension,
        )

        self.heads["Not Tagged"] = {
            "name": "Not Tagged",
            "parent_cost_head": None,
            "lft": 3,
            "rgt": 4,
            "is_group": 0,
            "indent": 0,
        }

        # Normalize parent fields immediately after fetch (Issue 3.1 fix)
        ReportFormatter.normalize_heads_parent_fields(self.heads, self.dimension_meta)

    def _set_total_type(self):
        """Set total type based on report type"""
        total_type_map = {
            ONLY_INCOME: Add_Income_total,
            ONLY_EXPENSE: Add_Expense_total,
            NET_PROFIT: Add_Net_Profit_total,
        }
        self.total_type = total_type_map.get(self.report_type, Add_Income_Expense_total)

    def _initialize_keys(self):
        """Initialize key lists for tracking"""
        self.inc_keys = []
        self.exp_keys = []
        self.net_keys = []
        self.adj_inc_keys = []
        self.adj_exp_keys = []

    def _get_boolean_value(self, key):
        """Convert checkbox value to boolean"""
        value = self.filters.get(key)
        return bool(value) if value is not None else False

    def has_children(self, head_name):
        """Check if a head has children"""
        # Parent fields use scrubbed doctype name, not fieldname
        parent_key = "parent_" + frappe.scrub(self.dimension_meta.name)
        for head, data in self.heads.items():
            parent = data.get(parent_key)
            # Parent fields are already normalized to None in _set_dimension_settings
            if parent == head_name:
                return True
        return False
