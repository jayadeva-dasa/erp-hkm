# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

"""
Report Formatting Utilities for Eagle View Report

Centralizes common report formatting operations like adding empty rows,
total rows, and data normalization.
"""

from typing import List, Dict, Any, Optional


class ReportFormatter:
    """
    Utility class for common report formatting operations.
    
    Eliminates duplicate code for adding empty rows and totals across
    different report types.
    """
    
    @staticmethod
    def add_empty_rows(
        data: List[Dict],
        count: int = 2,
        template_dict: Optional[Dict] = None
    ) -> None:
        """
        Add empty rows to report data (modifies list in place).
        
        Args:
            data: List of data dictionaries
            count: Number of empty rows to add
            template_dict: Template for empty row. If None, auto-detects from first row
            
        Example:
            >>> data = [{"account": "Sales", "amount": 1000}]
            >>> ReportFormatter.add_empty_rows(data, count=2)
            >>> # data now has 2 empty rows appended
        """
        if not data:
            return
        
        if template_dict is None:
            # Auto-detect template from first row
            template_dict = {}
            for key, value in data[0].items():
                if isinstance(value, (int, float)):
                    template_dict[key] = None
                else:
                    template_dict[key] = ""
        
        for _ in range(count):
            data.append(template_dict.copy())
    
    @staticmethod
    def add_grand_total_row(
        data: List[Dict],
        label_field: Optional[str] = None,
        exclude_fields: Optional[List[str]] = None,
        exclude_values: Optional[List[Any]] = None
    ) -> None:
        """
        Add grand total row to report data (modifies list in place).
        
        Args:
            data: List of data dictionaries
            label_field: Field name for total label (defaults to first field)
            exclude_fields: Fields to exclude from totaling
            exclude_values: Values in label field to exclude from sum
            
        Example:
            >>> data = [
            ...     {"account": "Sales", "income": 1000, "expense": 500},
            ...     {"account": "Purchase", "income": 0, "expense": 800}
            ... ]
            >>> ReportFormatter.add_grand_total_row(data, label_field="account")
            >>> # Adds: {"account": "Grand Total", "income": 1000, "expense": 1300}
        """
        if not data:
            return
        
        exclude_fields = exclude_fields or []
        exclude_values = exclude_values or ["Grand Total", ""]
        
        # Determine label field (first field if not specified)
        if label_field is None:
            label_field = list(data[0].keys())[0]
        
        # Identify numeric fields
        numeric_fields = []
        for field, value in data[0].items():
            if field not in exclude_fields and isinstance(value, (int, float)):
                numeric_fields.append(field)
        
        # Calculate totals
        total_row = {}
        for field in data[0].keys():
            if field == label_field:
                total_row[field] = "Grand Total"
            elif field in numeric_fields:
                total_row[field] = sum(
                    row.get(field, 0) or 0
                    for row in data
                    if row.get(field) is not None
                    and row.get(label_field) not in exclude_values
                )
            else:
                total_row[field] = ""
        
        data.append(total_row)
    
    @staticmethod
    def add_subtotal_row(
        data: List[Dict],
        label: str,
        label_field: Optional[str] = None,
        exclude_fields: Optional[List[str]] = None
    ) -> None:
        """
        Add subtotal row with custom label.
        
        Args:
            data: List of data dictionaries
            label: Label for the subtotal row
            label_field: Field name for subtotal label
            exclude_fields: Fields to exclude from totaling
        """
        if not data:
            return
        
        exclude_fields = exclude_fields or []
        
        if label_field is None:
            label_field = list(data[0].keys())[0]
        
        numeric_fields = [
            field for field, value in data[0].items()
            if field not in exclude_fields and isinstance(value, (int, float))
        ]
        
        subtotal_row = {}
        for field in data[0].keys():
            if field == label_field:
                subtotal_row[field] = label
            elif field in numeric_fields:
                subtotal_row[field] = sum(row.get(field, 0) or 0 for row in data)
            else:
                subtotal_row[field] = ""
        
        data.append(subtotal_row)
    
    @staticmethod
    def normalize_parent_fields(data: List[Dict], parent_field: str) -> None:
        """
        Normalize parent field values (empty string to None).
        
        This ensures consistent handling of parent fields across the codebase.
        
        Args:
            data: List of data dictionaries
            parent_field: Name of the parent field to normalize
            
        Example:
            >>> data = [{"name": "Child", "parent_cost_head": ""}]
            >>> ReportFormatter.normalize_parent_fields(data, "parent_cost_head")
            >>> # data[0]["parent_cost_head"] is now None
        """
        for row in data:
            if row.get(parent_field) == "":
                row[parent_field] = None
    
    @staticmethod
    def normalize_heads_parent_fields(heads: Dict[str, Dict], dimension_meta) -> None:
        """
        Normalize parent fields in heads dictionary.
        
        Args:
            heads: Dictionary of dimension heads
            dimension_meta: Meta information of dimension
        """
        parent_field = "parent_" + frappe.scrub(dimension_meta.name)
        
        for head_name, head_data in heads.items():
            if head_data.get(parent_field) == "":
                head_data[parent_field] = None
    
    @staticmethod
    def format_currency_fields(
        data: List[Dict],
        currency_fields: Optional[List[str]] = None,
        precision: int = 0
    ) -> None:
        """
        Format currency fields to specified precision.
        
        Args:
            data: List of data dictionaries
            currency_fields: List of field names to format. If None, formats all numeric fields
            precision: Decimal precision (default 0 for integer)
        """
        if not data:
            return
        
        if currency_fields is None:
            # Auto-detect numeric fields
            currency_fields = [
                field for field, value in data[0].items()
                if isinstance(value, (int, float))
            ]
        
        for row in data:
            for field in currency_fields:
                if field in row and row[field] is not None:
                    row[field] = round(row[field], precision)
    
    @staticmethod
    def create_empty_row_template(sample_row: Dict) -> Dict:
        """
        Create empty row template from sample row.
        
        Args:
            sample_row: Sample data row to base template on
            
        Returns:
            Empty row template dictionary
        """
        template = {}
        for key, value in sample_row.items():
            if isinstance(value, (int, float)):
                template[key] = None
            else:
                template[key] = ""
        return template


# Import frappe at module level for normalize functions
import frappe
