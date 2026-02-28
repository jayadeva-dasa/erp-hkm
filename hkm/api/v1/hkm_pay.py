from hkm.hkm_pay.notify_user import send_statement_email
import frappe
from hkm.hkm_pay.doctype.hkmp_entry.payment import process_hkmp_payment
import json


@frappe.whitelist()
def get_statement_email():
    user = frappe.session.user

    data = json.loads(frappe.request.data)
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    send_statement_email(user, start_date, end_date)


@frappe.whitelist()
def get_companies(user=None):
    if user is None:
        user = frappe.session.user
    parent = frappe.db.get_value("HKMP User", {"user": user}, "name")
    if not parent:
        return []
    doc = frappe.get_all(
        "HKM Active Company",
        filters={"parenttype": "HKMP User", "parent": parent},
        fields=["company"],
    )
    return doc


@frappe.whitelist()
def get_all_companies():
    """Get all companies in the system"""
    try:
        companies = frappe.get_all(
            "HKM Active Company",
            filters={"parenttype": "HKM General Settings"},
            fields=["company as name"],
        )
        return {"status": "success", "data": companies}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error fetching companies")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_available_balance():
    return (
        frappe.get_value("HKMP User", {"user": frappe.session.user}, "available_amt")
        or 0
    )


@frappe.whitelist()
def create_payment():
    data = json.loads(frappe.request.data)
    
    try:
        status , response_message = process_hkmp_payment(data, frappe.session.user)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error processing payment")
        frappe.throw(str(e))
    return {"status": status.lower() , "message"  :response_message}


@frappe.whitelist()
def get_status_payment():
    status = (
        frappe.get_all(
            "HKMP Entry",
            {"user": frappe.session.user, "docstatus": 1},
            pluck="status",
            limit=1,
            order_by="creation desc",
        )[0]
        or None
    )
    if not status:
        return {"status": "Failed"}
    return {"status": status}


@frappe.whitelist()
def search_quick_payments():
    request_data = frappe._dict(json.loads(frappe.request.data))
    page = int(request_data.get("page", 0))
    page_size = int(request_data.get("page_size", 10))
    limit_start = page * page_size


    where_conditions = ["hkmp_user = %(hkmp_user)s"]
    params = {}

    params["hkmp_user"] = frappe.session.user


    search_text = request_data.get("search_text", "").strip()
    if search_text:
        search_conditions = []
        params["search_text"] = f"%{search_text}%"

        # Text search fields
        text_fields = [
            "beneficiary",
            "paid_amount",
        ]

    where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

    query = f"""
        SELECT 
            name,
            beneficiary,
            beneficiary_vpa,
            paid_amount,
            payment_date
        FROM `tabHKMP Payee Directory`
        WHERE {where_clause}
        ORDER BY payment_date DESC
        LIMIT %(limit_start)s, %(page_size)s
    """
    params["limit_start"] = limit_start
    params["page_size"] = page_size

    entries = frappe.db.sql(query, params, as_dict=True)
    return entries
    

@frappe.whitelist()
def search_transactions():
    request_data = frappe._dict(json.loads(frappe.request.data))
    page = int(request_data.get("page", 0))
    page_size = int(request_data.get("page_size", 10))
    limit_start = page * page_size

    # Build WHERE conditions and parameters
    where_conditions = []
    params = {}

    # Base filters
    where_conditions.append("user = %(user)s")
    params["user"] = frappe.session.user

    where_conditions.append("docstatus = 1")

    # Add status filter (supports multiple status values)
    status_filter = request_data.get("status")
    if status_filter and isinstance(status_filter, list):
        clean_statuses = [
            s for s in status_filter if s and (not isinstance(s, str) or s.strip())
        ]
        if len(clean_statuses) > 0:
            status_placeholders = ", ".join(
                [f"%(status_{i})s" for i in range(len(clean_statuses))]
            )
            where_conditions.append(f"status IN ({status_placeholders})")
            for i, status in enumerate(clean_statuses):
                params[f"status_{i}"] = status

    # Add transaction type filter (supports multiple types)
    transaction_type = request_data.get("transaction_type")
    if transaction_type and isinstance(transaction_type, list):
        clean_types = [
            t.upper() if isinstance(t, str) and t.strip() else t
            for t in transaction_type
            if t and (not isinstance(t, str) or t.strip())
        ]
        if len(clean_types) > 0:
            type_placeholders = ", ".join(
                [f"%(type_{i})s" for i in range(len(clean_types))]
            )
            where_conditions.append(f"transfer_type IN ({type_placeholders})")
            for i, ttype in enumerate(clean_types):
                params[f"type_{i}"] = ttype
    elif not is_null_or_blank(transaction_type):
        where_conditions.append("transfer_type = %(transfer_type)s")
        params["transfer_type"] = (
            transaction_type.upper()
            if isinstance(transaction_type, str)
            else transaction_type
        )

    # Add company filter (supports multiple companies)
    company_filter = request_data.get("company")
    if company_filter and isinstance(company_filter, list):
        clean_companies = [
            c.strip() if isinstance(c, str) and c.strip() else c
            for c in company_filter
            if c and (not isinstance(c, str) or c.strip())
        ]
        if len(clean_companies) > 0:
            company_placeholders = ", ".join(
                [f"%(company_{i})s" for i in range(len(clean_companies))]
            )
            where_conditions.append(f"company IN ({company_placeholders})")
            for i, company in enumerate(clean_companies):
                params[f"company_{i}"] = company
    elif not is_null_or_blank(company_filter):
        where_conditions.append("company = %(company)s")
        params["company"] = (
            company_filter.strip()
            if isinstance(company_filter, str)
            else company_filter
        )

    # Add bill_received filter
    bill_received = request_data.get("bill_received")
    if bill_received is not None and bill_received != "":
        if isinstance(bill_received, str):
            params["bill_received"] = 1 if bill_received.lower() in ["true", "1"] else 0
        else:
            params["bill_received"] = int(bill_received)
        where_conditions.append("bill_received = %(bill_received)s")

    # Add is_return filter
    is_return = request_data.get("is_return")
    if is_return is not None and is_return != "":
        if isinstance(is_return, str):
            params["is_return"] = 1 if is_return.lower() in ["true", "1"] else 0
        else:
            params["is_return"] = int(is_return)
        where_conditions.append("is_return = %(is_return)s")

    # Add date range filters
    from_date = request_data.get("from_date")
    to_date = request_data.get("to_date")
    if not is_null_or_blank(from_date):
        where_conditions.append("creation >= %(from_date)s")
        params["from_date"] = from_date
    if not is_null_or_blank(to_date):
        where_conditions.append("creation <= %(to_date)s")
        params["to_date"] = to_date

    # Add amount range filters
    from_amount = request_data.get("transaction_from_amount")
    to_amount = request_data.get("transaction_to_amount")
    if from_amount is not None and from_amount != "":
        where_conditions.append("amount >= %(from_amount)s")
        params["from_amount"] = float(from_amount)
    if to_amount is not None and to_amount != "":
        where_conditions.append("amount <= %(to_amount)s")
        params["to_amount"] = float(to_amount)

    # Add search text filter (OR conditions)
    search_text = request_data.get("search_text", "").strip()
    if search_text:
        search_conditions = []
        params["search_text"] = f"%{search_text}%"

        # Text search fields
        text_fields = [
            "beneficiary_name",
            "transfer_type",
            "status",
            "remarks",
            "customer_ref_no",
            "utr",
            "ifsc_code",
            "upi_id",
        ]

        for field in text_fields:
            search_conditions.append(f"{field} LIKE %(search_text)s")

        # Numeric search fields (only if search text is numeric)
        if search_text.isdigit():
            params["search_amount"] = float(search_text)
            params["search_mobile"] = search_text
            search_conditions.append("amount = %(search_amount)s")
            search_conditions.append("mobile_number = %(search_mobile)s")

        # Add search conditions as OR group
        if search_conditions:
            where_conditions.append(f"({' OR '.join(search_conditions)})")

    # Validate and build ORDER BY
    sort_field = request_data.get("sort_field", "creation")
    sort_order = request_data.get("sort_order", "desc").upper()
    if sort_order not in ["ASC", "DESC"]:
        sort_order = "DESC"

    # Whitelist allowed sort fields to prevent SQL injection
    allowed_sort_fields = [
        "creation",
        "modified",
        "amount",
        "status",
        "transfer_type",
        "beneficiary_name",
        "customer_ref_no",
        "utr",
    ]
    if sort_field not in allowed_sort_fields:
        sort_field = "creation"

    # Build final query
    where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

    query = f"""
        SELECT *
        FROM `tabHKMP Entry`
        WHERE {where_clause}
        ORDER BY {sort_field} {sort_order}
        LIMIT %(limit_start)s, %(page_size)s
    """

    params["limit_start"] = limit_start
    params["page_size"] = page_size

    # Execute query
    try:
        entries = frappe.db.sql(query, params, as_dict=True)
        return entries
    except Exception as e:
        frappe.log_error(
            title="Search Transactions Error",
            message=f"Query: {query}\nParams: {frappe.as_json(params)}\nError: {str(e)}",
        )
        raise


def is_null_or_blank(value):
    """
    Check if a string is either None, empty, or consists only of whitespace characters.

    Args:
        value (str): The string to check.

    Returns:
        bool: True if the string is None, empty, or blank; otherwise, False.
    """
    return value is None or (isinstance(value, str) and value.strip() == "")




@frappe.whitelist(allow_guest=True)
def approve_pending_expense_approval(data):
    pass



@frappe.whitelist(allow_guest=True)
def reject_pending_expense_approval(data):
    pass

