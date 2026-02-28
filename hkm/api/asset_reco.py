import json
import frappe
from mimetypes import guess_type
import re
from frappe.utils.image import optimize_image


# Sub-category not used in HKM Assets Reco - keeping for API compatibility
@frappe.whitelist()
def get_sub_category(category):
    """Sub-category field does not exist in HKM Assets Reco"""
    return []


@frappe.whitelist()
def get_all_sub_categories():
    """Sub-category field does not exist in HKM Assets Reco"""
    return []


def get_category():
    """
    Get Asset Categories (standard ERPNext) that the user has access to.
    Checks if user has role or is HOD of Execution Department.
    """
    # Check if user has admin or special role access
    if frappe.session.user == "Administrator" or "System Manager" in frappe.get_roles(frappe.session.user):
        # Return all standard ERPNext Asset Categories
        return frappe.get_all("Asset Category", pluck="name", order_by="name")
    
    # For other users, check if they are HOD of any Execution Department
    # and return categories linked to their departments
    exec_depts = frappe.get_all(
        "Execution Department",
        filters={"department_hod": frappe.session.user},
        pluck="name"
    )
    
    if not exec_depts:
        frappe.throw("You are not authorized to access asset reco. You must be HOD of an Execution Department.")
    
    # Get asset categories linked to these departments
    categories = frappe.get_all(
        "Asset Category",
        filters={"execution_department": ["in", exec_depts]},
        pluck="name",
        order_by="name"
    )
    
    if not categories:
        # If no specific categories, return all
        categories = frappe.get_all("Asset Category", pluck="name", order_by="name")
    
    return categories


@frappe.whitelist()
def get_companies():
    """Get all companies for the company filter dropdown"""
    companies = frappe.get_all(
        "Company",
        fields=["name"],
        order_by="name",
    )
    return [company.name for company in companies]


@frappe.whitelist()
def get_asset_reco_list(company=None, asset_category=None, purchased_date_from=None, purchased_date_to=None, custodian=None, secondary_custodian=None):
    """
    Get list of HKM Assets Reco with filters.
    Returns only records user has access to based on their asset categories.
    """
    # Build filters
    filters = {}
    
    # Only apply category filtering for non-admin users
    if frappe.session.user != "Administrator":
        category = get_category()
        filters["asset_category"] = ("in", category)
        
        # Add asset_category filter (must be within allowed categories)
        if asset_category and asset_category in category:
            filters["asset_category"] = asset_category
    else:
        # Administrator sees all, but can still filter by category if provided
        if asset_category:
            filters["asset_category"] = asset_category
    
    # Add company filter
    if company:
        filters["company"] = company
    
    # Add purchased date range filter
    if purchased_date_from and purchased_date_to:
        filters["purchased_date"] = ["between", [purchased_date_from, purchased_date_to]]
    elif purchased_date_from:
        filters["purchased_date"] = [">=", purchased_date_from]
    elif purchased_date_to:
        filters["purchased_date"] = ["<=", purchased_date_to]
    
    # Add custodian filter (custodian_department field)
    if custodian:
        filters["custodian_department"] = custodian
    
    # Add secondary_custodian filter
    if secondary_custodian:
        filters["secondary_custodian"] = secondary_custodian
    
    data = frappe.get_all(
        "HKM Assets Reco",
        fields=[
            "name",
            "asset_category",
            "docstatus",
            "company",
            "location",
            "custodian_department",
            "purchased_date",
            "purchased_amount",
            "secondary_custodian",
            "remarks",
            "asset_id",
            "asset_name",
            "availability_status",
        ],
        filters=filters,
        order_by="modified desc"
    )
    
    # Add image URLs to each record
    for i in data:
        i["image_urls"] = [
            f"https://{frappe.local.site}{url}"
            for url in frappe.get_all(
                "File",
                filters={
                    "attached_to_name": i.name,
                    "attached_to_doctype": "HKM Assets Reco",
                },
                pluck="file_url",
            )
        ]
        # Rename custodian_department to custodian for frontend compatibility
        i["custodian"] = i.get("custodian_department")

    return data


@frappe.whitelist()
def edit_asset_reco(dict_data):
    """
    Edit HKM Assets Reco fields.
    Only allows editing specific fields in draft (docstatus=0) documents.
    """
    import json

    # Handle both dict and JSON string input
    if isinstance(dict_data, str):
        dict_data = json.loads(dict_data)

    # Group updates by document name
    updates_by_doc = {}
    for item in dict_data:
        doc_name = item.get("name") if isinstance(item, dict) else item.name
        fieldname = item.get("fieldname") if isinstance(item, dict) else item.fieldname
        value = item.get("value") if isinstance(item, dict) else item.value

        if doc_name not in updates_by_doc:
            updates_by_doc[doc_name] = {}
        updates_by_doc[doc_name][fieldname] = value

    # Update each document
    for doc_name, fields in updates_by_doc.items():
        if not frappe.db.exists("HKM Assets Reco", doc_name):
            frappe.throw(f"Asset reco {doc_name} not found")

        doc = frappe.get_doc("HKM Assets Reco", doc_name)

        # Only allow editing if document is in draft status
        if doc.docstatus != 0:
            frappe.throw(f"Cannot edit submitted or cancelled document: {doc_name}")

        # Update allowed fields
        for fieldname, value in fields.items():
            # Validate field is editable
            if fieldname not in [
                "location",
                "purchased_date",
                "purchased_amount",
                "secondary_custodian",
                "remarks",
            ]:
                frappe.throw(f"Field {fieldname} is not editable")
            doc.set(fieldname, value)

        doc.save()

    frappe.db.commit()  # v16: REVIEW - check if needed
    return "Asset reco updated successfully"


@frappe.whitelist()
def submit_asset_reco(name):
    """Submit HKM Assets Reco document"""
    if not frappe.db.exists("HKM Assets Reco", name):
        frappe.throw("Asset reco not found")
    doc = frappe.get_doc("HKM Assets Reco", name)
    doc.submit()
    frappe.db.commit()  # v16: REVIEW - API endpoint


@frappe.whitelist()
def get_users(search_term=None):
    """Get users for secondary custodian dropdown"""
    filters = {"enabled": 1, "name": ("!=", "Administrator")}
    
    if search_term:
        users = frappe.db.sql(
            """
            SELECT name as email, full_name
            FROM `tabUser`
            WHERE enabled = 1
            AND name != 'Administrator'
            AND (
                name LIKE %(search)s 
                OR full_name LIKE %(search)s
            )
            ORDER BY full_name
            LIMIT 50
            """,
            {"search": f"%{search_term}%"},
            as_dict=True,
        )
    else:
        users = frappe.get_all(
            "User",
            filters=filters,
            fields=["name as email", "full_name"],
            order_by="full_name",
            limit=30,
        )
    
    return users


@frappe.whitelist()
def get_custodians():
    """Get all custodian departments (Execution Departments) from HKM Assets Reco"""
    custodians = frappe.db.sql(
        """
        SELECT DISTINCT custodian_department
        FROM `tabHKM Assets Reco`
        WHERE custodian_department IS NOT NULL AND custodian_department != ''
        ORDER BY custodian_department
        """,
        as_dict=True,
    )
    return [c.custodian_department for c in custodians if c.custodian_department]


def sanitize_filename(value):
    return re.sub(r"[^\w\-]", "_", value)


def get_file_name(file):
    if "." in file.filename:
        name_part, ext = file.filename.rsplit(".", 1)
        ext = "." + ext
    else:
        name_part = file.filename
        ext = ""
    return name_part, ext


def _save_file_doc(content, filename, doctype, docname, file_type):
    """Helper function to save file document"""
    frappe.local.uploaded_file = content
    frappe.local.uploaded_filename = filename

    return frappe.get_doc(
        {
            "doctype": "File",
            "file_type": file_type,
            "attached_to_doctype": doctype,
            "attached_to_name": docname,
            "folder": "Home/Attachments",
            "file_name": filename,
            "is_private": 0,
            "content": content,
        }
    ).save(ignore_permissions=1)


@frappe.whitelist()
def upload_image_attachments_assets_reco():
    """Upload images to HKM Assets Reco"""
    assets_reco_id = frappe.form_dict.get("name")
    files = frappe.request.files.getlist("image")

    for index, file in enumerate(files):
        content = file.stream.read()
        original_filename = file.filename or "image.jpg"
        content_type = guess_type(original_filename)[0] or "image/jpeg"

        if content_type.startswith("image/"):
            content = optimize_image(content=content, content_type=content_type)

        file_name = sanitize_filename(get_file_name(file)[0])
        ext = get_file_name(file)[1]

        filename = f"Images_{assets_reco_id}_{index}_{file_name}{ext}"
        
        if  frappe.get_all("File", filters={"attached_to_name": assets_reco_id, "attached_to_doctype": "HKM Assets Reco", "file_name": ["like", f"%{file_name}%"]}):
            continue

        _save_file_doc(content, filename, "HKM Assets Reco", assets_reco_id, "Image")


@frappe.whitelist()
def get_asset_reco(id):
    """Get single HKM Assets Reco document by ID with specifications"""
    if not frappe.db.exists("HKM Assets Reco", id):
        frappe.throw("Asset reco not found")
    
    doc = frappe.get_doc("HKM Assets Reco", id).as_dict()
    
    # Get specifications
    specifications = frappe.get_all(
        "HKM Asset Specification Value",
        filters={"parent": id, "parenttype": "HKM Assets Reco"},
        fields=["name", "specification", "specification_name", "value", "data_type", "idx"],
        order_by="idx"
    )
    doc["specifications"] = specifications
    
    # Get image URLs
    doc["image_urls"] = [
        f"https://{frappe.local.site}{url}"
        for url in frappe.get_all(
            "File",
            filters={
                "attached_to_name": id,
                "attached_to_doctype": "HKM Assets Reco",
            },
            pluck="file_url",
        )
    ]
    
    return doc


@frappe.whitelist()
def get_asset_categories():
    """
    Get asset categories that the user has access to.
    Administrator sees all categories.
    """
    if frappe.session.user == "Administrator":
        # Administrator sees all categories
        return frappe.get_all("Asset Category", pluck="name", order_by="name")
    else:
        # Non-admin users see only their allowed categories
        return get_category()


@frappe.whitelist()
def get_asset_specifications(main_category):
    """
    Get specifications for a given asset category (standard ERPNext Asset Category).
    Returns both mandatory and optional specifications.
    """
    if not main_category:
        return []
    
    specifications = frappe.get_all(
        "HKM Asset Specification",
        filters={"asset_category": main_category},
        fields=["name", "specification_name", "data_type", "options", "is_mandatory"],
        order_by="specification_name"
    )
    
    return specifications


@frappe.whitelist()
def get_available_custom_specs(main_category):
    """
    Get available custom (non-mandatory) specifications for a category.
    Used when adding custom specs to an asset.
    """
    if not main_category:
        return []
    
    specifications = frappe.get_all(
        "HKM Asset Specification",
        filters={
            "asset_category": main_category,
            "is_mandatory": 0
        },
        fields=["name", "specification_name", "data_type", "options"],
        order_by="specification_name"
    )
    
    return specifications


@frappe.whitelist()
def search_available_assets(asset_id=None, asset_name=None):
    """
    Search for available assets from ERPNext Asset master.
    Used for autocomplete when selecting existing assets.
    """
    filters = {
        "docstatus": 1,  # Only submitted assets
    }
    
    if asset_id:
        filters["name"] = ["like", f"%{asset_id}%"]
    elif asset_name:
        filters["asset_name"] = ["like", f"%{asset_name}%"]
    
    # Search in ERPNext Asset doctype
    assets = frappe.get_all(
        "Asset",
        filters=filters,
        fields=[
            "name as asset_id",
            "asset_name",
            "purchase_date as purchased_date",
            "gross_purchase_amount as purchased_amount",
            "asset_category"
        ],
        limit=20,
        order_by="modified desc"
    )
    
    return assets


@frappe.whitelist()
def save_asset_reco_with_specs(
    name,
    asset_category=None,
    purchased_date=None,
    purchased_amount=None,
    location=None,
    remarks=None,
    secondary_custodian=None,
    availability_status="New",
    asset_id=None,
    asset_name=None,
    specifications=None
):
    """
    Save HKM Assets Reco document with specifications.
    Handles both creating new specs and updating existing ones.
    Allows changing asset category which will reload specifications.
    """
    import json
    
    if not frappe.db.exists("HKM Assets Reco", name):
        frappe.throw("Asset reco not found")
    
    doc = frappe.get_doc("HKM Assets Reco", name)
    
    # Only allow editing draft documents
    if doc.docstatus != 0:
        frappe.throw("Cannot edit submitted or cancelled document")
    
    # Update basic fields
    if asset_category:
        doc.asset_category = asset_category
    if purchased_date:
        doc.purchased_date = purchased_date
    if purchased_amount:
        doc.purchased_amount = purchased_amount
    if location:
        doc.location = location
    if remarks:
        doc.remarks = remarks
    if secondary_custodian:
        doc.secondary_custodian = secondary_custodian
    if availability_status:
        doc.availability_status = availability_status
    if asset_id:
        doc.asset_id = asset_id
    if asset_name:
        doc.asset_name = asset_name
    
    # Handle specifications
    if specifications:
        if isinstance(specifications, str):
            specifications = json.loads(specifications)
        
        # Clear existing specifications
        doc.set("specification", [])
        
        # Add new specifications
        for spec in specifications:
            spec_name = spec.get("specification")
            if spec_name:
                spec_doc = frappe.get_doc("HKM Asset Specification", spec_name)
                doc.append("specification", {
                    "specification": spec_name,
                    "specification_name": spec_doc.specification_name,
                    "data_type": spec_doc.data_type,
                    "value": spec.get("value"),
                })
    
    doc.save()
    frappe.db.commit()  # v16: REVIEW - check if needed
    
    return {
        "message": "Asset reco saved successfully",
        "name": doc.name
    }



@frappe.whitelist()
def search():
    roles = frappe.get_roles(frappe.session.user)

    # System Manager has access to everything
    if "System Manager" in roles:
        # Skip all role checks and filters for System Manager
        pass
    elif "Asset Reco" not in roles:
        frappe.throw("You are not authorized to perform this action")

    request_data = frappe._dict(json.loads(frappe.request.data))
    page = max(1, int(request_data.get("page", 1)))  # Ensure page is at least 1
    page_size = max(1, int(request_data.get("page_size", 10)))  # Ensure page_size is at least 1
    limit_start = (page - 1) * page_size

    conditions = []
    params = {}

    # Default condition: purchased_amount must be NOT NULL and > 0
    conditions.append("purchased_amount IS NOT NULL AND purchased_amount > 0")

    # Only apply department filtering if user is not System Manager
    if "System Manager" not in roles:
        execution_departments = frappe.db.sql_list("""
            SELECT name 
            FROM `tabExecution Department` 
            WHERE department_hod = %s
            UNION ALL 
            SELECT parent
            FROM `tabExecution Department Concern Person` 
            WHERE user = %s
        """, (frappe.session.user, frappe.session.user))
        
        if execution_departments:
            conditions.append("custodian_department IN %(execution_departments)s")
            params["execution_departments"] = execution_departments


    sort_field = request_data.get("sort_field", "creation")
    sort_order = request_data.get("sort_order", "desc").upper()
    if sort_order not in ["ASC", "DESC"]:
        sort_order = "DESC"

    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    query = f"""    
        SELECT * FROM `tabHKM Assets Reco`
        WHERE {where_clause}
        ORDER BY {sort_field} {sort_order}
        LIMIT %(limit_start)s, %(page_size)s
    """
    params["limit_start"] = limit_start
    params["page_size"] = page_size
    
    result = frappe.db.sql(query, params, as_dict=True)
    # log_sql_query(query, params)
    return result