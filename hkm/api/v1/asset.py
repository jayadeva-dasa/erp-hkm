from dataclasses import field
import json
import frappe


def is_null_or_blank(value):
    """
    Check if a value is None, empty, blank, or contains only empty/blank elements.
    Supports:
        - None
        - Blank strings
        - Empty lists
        - Empty dicts
        - Lists of dicts or nested structures

    Args:
        value: Any Python object.

    Returns:
        bool: True if value is None/empty/blank; otherwise, False.
    """

    # Case 1: None
    if value is None:
        return True

    # Case 2: String
    if isinstance(value, str):
        return value.strip() == ""

    # Case 3: Dict → True if empty OR all values inside are null/blank
    if isinstance(value, dict):
        if not value:
            return True
        return all(is_null_or_blank(v) for v in value.values())

    # Case 4: List or Tuple → True if empty OR each element is null/blank
    if isinstance(value, (list, tuple)):
        if not value:
            return True
        return all(is_null_or_blank(v) for v in value)

    # Other types (int, float, bool, object) → Count as NOT blank
    return False


@frappe.whitelist()
def search():

    roles = frappe.get_roles(frappe.session.user)

    if "Asset Reco" not in roles:
        return frappe.throw("You are not authorized to perform this action")

    request_data = frappe._dict(json.loads(frappe.request.data))
    page = int(request_data.get("page", 1))
    page_size = int(request_data.get("page_size", 10))
    limit_start = page * page_size

    custodian_department = frappe.get_all(
        "Execution Department",
        filters={"department_hod": frappe.session.user},
        pluck="name",
    )

    # Build WHERE conditions
    conditions = []
    values = {}

    # Department filter
    if "System Manager" not in roles:
        if custodian_department:
            conditions.append("asset.custodian_department IN %(custodian_department)s")
            values["custodian_department"] = custodian_department
        else:
            # No departments assigned, return empty result
            return []

    # Search field filter
    if not is_null_or_blank(request_data.get("search_field")) and not is_null_or_blank(
        request_data.get("search_text")
    ):
        search_field = request_data.get("search_field").strip()
        search_text = request_data.get("search_text").strip()
        # Sanitize field name to prevent SQL injection
        allowed_fields = [
            "name",
            "company",
            "item_name",
            "asset_name",
            "location",
            "barcode_id",
            "secondary_custodian",
            "asset_category",
        ]
        if search_field in allowed_fields:
            conditions.append(f"asset.{search_field} LIKE %(search_text)s")
            values["search_text"] = f"%{search_text}%"

    # Asset category filter
    if not is_null_or_blank(request_data.get("asset_category")):
        asset_categories = request_data.get("asset_category")
        conditions.append("asset.asset_category IN %(asset_categories)s")
        values["asset_categories"] = asset_categories

    # Specifications filter (if needed, requires JOIN)
    has_specifications = False
    if not is_null_or_blank(request_data.get("selected_specifications")):
        selected_specifications = request_data.get("selected_specifications")
        for idx, spec in enumerate(selected_specifications):
            # Handle both camelCase (from frontend) and snake_case
            spec_name = spec.get("specificationName") or spec.get("specification_name")
            spec_value = spec.get("value")

            if spec_name and spec_value:
                # Add parameterized condition for specification name and value
                param_spec_name = f"spec_name_{idx}"
                param_spec_value = f"spec_value_{idx}"
                conditions.append(
                    f"(sp.specification_name = %({param_spec_name})s AND sp.value = %({param_spec_value})s)"
                )
                values[param_spec_name] = spec_name
                values[param_spec_value] = spec_value
        has_specifications = True

    # Company filter
    if not is_null_or_blank(request_data.get("company")):
        companies = request_data.get("company")
        conditions.append("asset.company IN %(companies)s")
        values["companies"] = companies

    # Purchase date from filter
    if not is_null_or_blank(request_data.get("purchase_date_from")):
        conditions.append("asset.purchase_date >= %(purchase_date_from)s")
        values["purchase_date_from"] = request_data.get("purchase_date_from")

    # Purchase date to filter
    if not is_null_or_blank(request_data.get("purchase_date_to")):
        conditions.append("asset.purchase_date <= %(purchase_date_to)s")
        values["purchase_date_to"] = request_data.get("purchase_date_to")

    # Gross purchase amount from filter
    if not is_null_or_blank(request_data.get("gross_purchase_amount_from")):
        conditions.append(
            "asset.gross_purchase_amount >= %(gross_purchase_amount_from)s"
        )
        values["gross_purchase_amount_from"] = request_data.get(
            "gross_purchase_amount_from"
        )

    # Gross purchase amount to filter
    if not is_null_or_blank(request_data.get("gross_purchase_amount_to")):
        conditions.append("asset.gross_purchase_amount <= %(gross_purchase_amount_to)s")
        values["gross_purchase_amount_to"] = request_data.get(
            "gross_purchase_amount_to"
        )

    conditions.append("asset.docstatus != 2")
    # Build FROM and JOIN clauses
    from_clause = "FROM `tabAsset` asset"
    if has_specifications:
        # Adjust this JOIN based on your actual specifications table structure
        from_clause += " LEFT JOIN `tabHKM Asset Specification Value` sp ON sp.parent = asset.name AND sp.parenttype = 'Asset'"

    # Build WHERE clause
    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    # Sort field validation
    sort_field = request_data.get("sort_field", "creation")
    allowed_sort_fields = [
        "name",
        "company",
        "item_name",
        "asset_name",
        "location",
        "barcode_id",
        "secondary_custodian",
        "purchase_date",
        "gross_purchase_amount",
        "creation",
        "modified",
    ]
    if sort_field not in allowed_sort_fields:
        sort_field = "creation"

    # Sort order validation
    sort_order = request_data.get("sort_order", "desc").upper()
    if sort_order not in ["ASC", "DESC"]:
        sort_order = "DESC"

    # Build query parts
    query_parts = [
        "SELECT",
        "    asset.name,",
        "    asset.company,",
        "    asset.asset_category,",
        "    asset.item_name,",
        "    asset.asset_name,",
        "    asset.docstatus,",
        "    asset.location,",
        "    asset.barcode_id,",
        "    asset.secondary_custodian,",
        "    asset.purchase_date,",
        "    asset.gross_purchase_amount",
        from_clause,
    ]

    if where_clause:
        query_parts.append(where_clause)

    query_parts.extend(
        [
            "GROUP BY asset.name",
            f"ORDER BY asset.{sort_field} {sort_order}",
            "LIMIT %(limit_start)s, %(page_size)s",
        ]
    )

    query = "\n".join(query_parts)

    values["limit_start"] = limit_start
    values["page_size"] = page_size

    # log_sql_query(query, values)

    result = frappe.db.sql(query, values, as_dict=True)
    return result


from frappe.utils import cstr


def log_sql_query(query, params):
    formatted = query
    for k, v in params.items():
        formatted = formatted.replace(f"%({k})s", f"'{cstr(v)}'")
    frappe.log_error(formatted, "Final SQL Query")


@frappe.whitelist()
def search_asset(request_data):
    if is_null_or_blank(request_data):
        return []

    return frappe.db.sql(
    """
    SELECT name, asset_name, purchase_date, gross_purchase_amount
    FROM `tabAsset`
    WHERE docstatus = 1
    AND (name LIKE %(request_data)s OR asset_name LIKE %(request_data)s)
    LIMIT 10
    """,
    {"request_data": f"%{request_data}%"},
    as_dict=True,
)

