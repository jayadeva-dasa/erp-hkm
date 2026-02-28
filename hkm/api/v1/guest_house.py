# Copyright (c) 2025, HKM and contributors
# For license information, please see license.txt
import re
import urllib.parse

import json
from hkm.utils import is_null_or_blank
import frappe
from frappe import _
from frappe.utils import getdate, now_datetime, add_days, flt, nowdate
from datetime import datetime, time
from typing import Dict, List, Optional, Tuple
from mimetypes import guess_type
from frappe.utils.image import optimize_image
from frappe import qb
from frappe.query_builder import Criterion
from frappe.query_builder.functions import Sum
from india_compliance.gst_india.doctype.pan.pan import (
    get_pan_status as get_pan_status_india_compliance,
)


# Standard check-in and check-out times (matching booking validation logic)
CHECK_IN_TIME = time(12, 0, 0)  # 12:00 PM
CHECK_OUT_TIME = time(10, 0, 0)  # 10:00 AM


def _format_date_for_note(date_obj) -> str:
    """
    Format date in "20 Sep 25" format for availability notes.

    Args:
            date_obj: Date object or string

    Returns:
            Formatted date string like "20 Sep 25"
    """
    if isinstance(date_obj, str):
        date_obj = getdate(date_obj)

    # Format: day month_abbr year_short
    month_abbr = date_obj.strftime("%b")
    day = date_obj.day
    year_short = date_obj.strftime("%y")

    return f"{day} {month_abbr} {year_short}"


def _fetch_rooms_and_bookings(
    check_date: str,
) -> Tuple[List[Dict], Dict[str, List[Dict]], Dict[str, List[Dict]]]:
    """
    Fetch all rooms and bookings data using optimized raw SQL.

    Rooms are booked through the GH Room Booking Details child table (room_details field),
    not directly on the GH Room Booking document. Each booking can have multiple rooms.

    Returns:
            Tuple of (rooms_list, current_bookings_map, all_bookings_map)
    """
    # Optimized single query to get rooms with their bookings
    # Rooms are linked to bookings through the GH Room Booking Details child table
    # This matches the doctype validation logic in validate_room_availability()
    query = """
		SELECT 
			r.name as room_id,
			r.room_number as room_details,
			r.floor,
			rb.name as booking_id,
			rb.from_date,
			rb.to_date,
			rb.customer as guest_name,
			rb.actual_check_in,
			rb.actual_check_out,
			rb.amount,
			rb.total_person,
			rb.guest_type,
			rb.devotee,
            rb.docstatus,
			CASE 
				WHEN rb.from_date <= %(check_date)s AND rb.to_date >= %(check_date)s 
				THEN 1 
				ELSE 0 
			END as is_current_booking
		FROM `tabGH Room` r
		LEFT JOIN `tabGH Room Booking Details` rbd 
			ON rbd.room = r.name 
			AND rbd.parentfield = 'room_details'
		LEFT JOIN `tabGH Room Booking` rb 
			ON rb.name = rbd.parent 
			AND rb.docstatus != 2
		WHERE r.enabled = 1
		ORDER BY r.floor, r.room_number, rb.from_date
	"""

    results = frappe.db.sql(query, {"check_date": check_date}, as_dict=True)

    # Process results into separate data structures
    rooms_map = {}
    all_bookings_map = {}
    current_bookings_map = {}

    for row in results:
        room_id = row.room_id

        # Build rooms list
        if room_id not in rooms_map:
            rooms_map[room_id] = {
                "name": room_id,
                "room_details": row.room_details,
                "floor": row.floor or "0",
            }

        # Build bookings maps if booking exists
        if row.booking_id:
            booking_data = {
                "booking_id": row.booking_id,
                "from_date": row.from_date,
                "to_date": row.to_date,
                "guest_name": row.guest_name,
                "actual_check_in": row.actual_check_in,
                "actual_check_out": row.actual_check_out,
                "amount": row.amount,
                "total_person": row.total_person,
                "guest_type": row.guest_type,
                "devotee": row.devotee,
                "docstatus": row.docstatus,
                "room_id": room_id,
            }

            # Add to all bookings map
            if room_id not in all_bookings_map:
                all_bookings_map[room_id] = []
            all_bookings_map[room_id].append(booking_data)

            # Add to current bookings map if it overlaps with check_date
            if row.is_current_booking:
                if room_id not in current_bookings_map:
                    current_bookings_map[room_id] = []
                current_bookings_map[room_id].append(booking_data)

    rooms_list = list(rooms_map.values())
    return rooms_list, current_bookings_map, all_bookings_map


def _calculate_next_available_date(
    available_from_date, all_bookings_for_room: List[Dict]
) -> Optional[str]:
    """
    Calculate the next available date by finding the next booking after available_from_date.

    Returns:
            available_to_date or None if available indefinitely
    """
    if not available_from_date:
        return None

    # Find next booking that starts AFTER available_from_date
    for booking in all_bookings_for_room:
        booking_from = getdate(booking["from_date"])
        if booking_from > available_from_date:
            # Room is available until the day before next booking starts
            return add_days(booking_from, -1)

    return None  # Available indefinitely


def _determine_room_status(
    room_id: str, check_date, current_bookings: List[Dict], all_bookings: List[Dict]
) -> Dict:
    """
    Determine room status, availability, and booking information for a specific date.

    Returns:
            Dict with status, is_available, is_ready_to_book, booking_info,
            availability_note, available_from_date, available_to_date, and summary_update
    """
    current_datetime = now_datetime()
    result = {
        "status": "available",
        "is_available": True,
        "is_ready_to_book": True,
        "booking_info": None,
        "availability_note": "Available and ready to book",
        "available_from_date": check_date,
        "available_to_date": None,
        "summary_update": {"available_rooms": 1},
    }

    # If no current booking, check for past booking ending today
    if not current_bookings:
        for booking in all_bookings:
            if getdate(booking["to_date"]) == check_date:
                booking_check_out = datetime.combine(check_date, CHECK_OUT_TIME)
                if current_datetime >= booking_check_out:
                    result["availability_note"] = (
                        "Checked out today, available and ready to book"
                    )
                    result["available_to_date"] = _calculate_next_available_date(
                        check_date, all_bookings
                    )
                    return result

        # No booking, calculate next booking
        result["available_to_date"] = _calculate_next_available_date(
            check_date, all_bookings
        )
        return result

    # Get the active booking (earliest one overlapping with check_date)
    active_booking = sorted(current_bookings, key=lambda x: getdate(x["from_date"]))[0]

    check_in_date = getdate(active_booking["from_date"])
    check_out_date = getdate(active_booking["to_date"])
    booking_check_in = datetime.combine(check_in_date, CHECK_IN_TIME)
    booking_check_out = datetime.combine(check_out_date, CHECK_OUT_TIME)

    # Build booking info
    result["booking_info"] = {
        "docstatus": active_booking["docstatus"],
        "booking_id": active_booking["booking_id"],
        "guest_name": active_booking["guest_name"],
        "check_in_date": str(active_booking["from_date"]),
        "check_out_date": str(active_booking["to_date"]),
        "check_in_time": f"{active_booking['from_date']} {CHECK_IN_TIME.strftime('%H:%M:%S')}",
        "check_out_time": f"{active_booking['to_date']} {CHECK_OUT_TIME.strftime('%H:%M:%S')}",
        "actual_check_in": (
            str(active_booking["actual_check_in"])
            if active_booking["actual_check_in"]
            else None
        ),
        "actual_check_out": (
            str(active_booking["actual_check_out"])
            if active_booking["actual_check_out"]
            else None
        ),
        "amount": float(active_booking["amount"]) if active_booking["amount"] else 0.0,
        "total_person": active_booking["total_person"] or 0,
        "guest_type": active_booking["guest_type"],
        "devotee": active_booking["devotee"],
    }

    # Determine status based on check-in/check-out timing
    if check_in_date == check_date:
        # Checking in today
        if current_datetime < booking_check_in:
            result.update(
                {
                    "status": "checking_in_today",
                    "is_available": True,
                    "is_ready_to_book": False,
                    "availability_note": "Check-in scheduled for today at 12:00 PM",
                    "available_from_date": check_date,
                    "available_to_date": check_date,
                    "summary_update": {"checking_in_today": 1},
                }
            )
        else:
            # Already checked in
            formatted_date = _format_date_for_note(check_out_date)
            result.update(
                {
                    "status": "booked",
                    "is_available": False,
                    "is_ready_to_book": False,
                    "availability_note": f"Checked in today, check-out on {formatted_date} at 10:00 AM",
                    "available_from_date": check_out_date,
                    "available_to_date": _calculate_next_available_date(
                        check_out_date, all_bookings
                    ),
                    "summary_update": {"booked_rooms": 1},
                }
            )

    elif check_out_date == check_date:
        # Checking out today
        if current_datetime < booking_check_out:
            result.update(
                {
                    "status": "checking_out_today",
                    "is_available": False,
                    "is_ready_to_book": True,
                    "availability_note": "Check-out scheduled for today at 10:00 AM, will be available after that",
                    "available_from_date": check_date,
                    "available_to_date": _calculate_next_available_date(
                        check_date, all_bookings
                    ),
                    "summary_update": {"checking_out_today": 1},
                }
            )
        else:
            # Already checked out
            result.update(
                {
                    "status": "available",
                    "is_available": True,
                    "is_ready_to_book": True,
                    "availability_note": "Checked out today, available and ready to book",
                    "available_from_date": check_date,
                    "available_to_date": _calculate_next_available_date(
                        check_date, all_bookings
                    ),
                    "summary_update": {"available_rooms": 1},
                }
            )

    else:
        # Fully booked (not checking in/out today)
        formatted_date = _format_date_for_note(check_out_date)
        result.update(
            {
                "status": "booked",
                "is_available": False,
                "is_ready_to_book": False,
                "availability_note": f"Booked until {formatted_date} at 10:00 AM",
                "available_from_date": check_out_date,
                "available_to_date": _calculate_next_available_date(
                    check_out_date, all_bookings
                ),
                "summary_update": {"booked_rooms": 1},
            }
        )

    return result


def _build_room_data(room: Dict, room_status: Dict) -> Dict:
    """Build the room data dictionary for API response."""
    booking_info = room_status["booking_info"]

    return {
        "room_id": room["name"],
        "room_details": room["room_details"] or room["name"],
        "floor": room["floor"],
        "status": room_status["status"],
        "is_available": room_status["is_available"],
        "is_ready_to_book": room_status["is_ready_to_book"],
        "booking": booking_info,
        "availability_note": room_status["availability_note"],
        "available_from_date": (
            str(room_status["available_from_date"])
            if room_status["available_from_date"]
            else None
        ),
        "available_to_date": (
            str(room_status["available_to_date"])
            if room_status["available_to_date"]
            else None
        ),
    }


def _group_rooms_by_floor(rooms_data: List[Dict]) -> List[Dict]:
    """Group rooms by floor and sort them."""
    floors_dict = {}

    for room_data in rooms_data:
        floor = room_data["floor"]
        if floor not in floors_dict:
            floors_dict[floor] = {"floor": floor, "rooms": []}
        floors_dict[floor]["rooms"].append(room_data)

    # Sort floors and return as list
    return [
        floors_dict[floor]
        for floor in sorted(
            floors_dict.keys(), key=lambda x: int(x) if x.isdigit() else 0
        )
    ]


@frappe.whitelist()
def get_rooms_floor_wise(date=None):
    """
    Get all rooms grouped by floor for a particular date with booking status.

    Args:
            date (str, optional): Date in YYYY-MM-DD format. Defaults to today.

    Returns:
            dict: {
                    "status": "success",
                    "date": "2025-01-27",
                    "floors": [
                            {
                                    "floor": "0",
                                    "rooms": [
                                            {
                                                    "room_id": "0-101",
                                                            "room_details": "101",
                                                    "floor": "0",
                                                    "status": "booked" | "available" | "checking_out_today" | "checking_in_today",
                                                    "is_available": true/false,
                                                    "is_ready_to_book": true/false,
                                                    "booking": {...} or null,
                                                    "availability_note": "...",
                                                    "available_from_date": "2025-01-27",
                                                    "available_to_date": "2025-02-15" or null
                                            }
                                    ]
                            }
                    ],
                    "summary": {
                            "total_rooms": 50,
                            "available_rooms": 30,
                            "booked_rooms": 20,
                            "checking_out_today": 5,
                            "checking_in_today": 3
                    }
            }
    """
    try:
        # Parse and validate date
        check_date = getdate(date) if date else getdate()

        # Fetch all data using optimized SQL
        rooms, current_bookings_map, all_bookings_map = _fetch_rooms_and_bookings(
            check_date
        )

        # Initialize summary
        summary = {
            "total_rooms": len(rooms),
            "available_rooms": 0,
            "booked_rooms": 0,
            "checking_out_today": 0,
            "checking_in_today": 0,
        }

        # Process each room
        rooms_data = []
        for room in rooms:
            room_id = room["name"]
            current_bookings = current_bookings_map.get(room_id, [])
            all_bookings = sorted(
                all_bookings_map.get(room_id, []), key=lambda x: getdate(x["from_date"])
            )

            # Determine room status
            room_status = _determine_room_status(
                room_id, check_date, current_bookings, all_bookings
            )

            # Update summary
            for key, value in room_status["summary_update"].items():
                summary[key] += value

            # Build room data
            room_data = _build_room_data(room, room_status)
            rooms_data.append(room_data)

        # Group by floor
        floors_list = _group_rooms_by_floor(rooms_data)

        dict_data = {
            "status": "success",
            "date": str(check_date),
            "floors": floors_list,
            "summary": summary,
        }

        print(f"dict_data: {dict_data}")

        return dict_data

    except Exception as e:
        frappe.log_error(
            message=f"Error in get_rooms_floor_wise: {str(e)}",
            title="Guest House API Error",
        )
        return {
            "status": "error",
            "message": str(e),
            "date": str(date) if date else None,
            "floors": [],
            "summary": {
                "total_rooms": 0,
                "available_rooms": 0,
                "booked_rooms": 0,
                "checking_out_today": 0,
                "checking_in_today": 0,
            },
        }


@frappe.whitelist()
def get_devotees_search(search_term=None, required_all=False):
    """
    Get all devotees by search term
    """
    try:
        if required_all:
            return frappe.get_all(
                "DED Devotee",
                fields=["name", "full_name"],
                filters={"enabled": 1},
            )
        devotees = frappe.get_all(
            "DED Devotee",
            fields=["name", "full_name"],
            filters={"enabled": 1},
            or_filters={
                "name": ["like", f"%{search_term}%"],
                "full_name": ["like", f"%{search_term}%"],
            },
            limit=10,
        )
        return devotees
    except Exception as e:
        frappe.log_error(
            message=f"Error in get_devotees_search: {str(e)}",
            title="Guest House API Error",
        )
        return []


@frappe.whitelist()
def get_customers_search(search_term=None, required_all=False):
    """
    Get all customers by search term with one address per customer
    """
    try:
        if required_all:
            customers = frappe.db.sql(
                """
                SELECT 
                    c.name,
                    COALESCE(
                        (
                            SELECT TRIM(CONCAT_WS('\n',
                                NULLIF(a.address_line1, ''),
                                NULLIF(a.address_line2, ''),
                                NULLIF(a.city, ''),
                                NULLIF(a.state, ''),
                                NULLIF(a.pincode, '')
                            ))
                            FROM `tabAddress` a
                            INNER JOIN `tabDynamic Link` dl 
                                ON dl.parent = a.name
                                AND dl.parenttype = 'Address'
                                AND dl.link_doctype = 'Customer'
                                AND dl.link_name = c.name
                            ORDER BY a.is_primary_address DESC
                            LIMIT 1
                        ),
                        ''
                    ) as address
                FROM `tabCustomer` c
                WHERE c.customer_group = 'Guest House'
                LIMIT 10
                """,
                as_dict=True,
            )
            return customers

        if not search_term or search_term.strip() == "":
            return []

        customers = frappe.db.sql(
            """
            SELECT 
                c.name,
                COALESCE(
                    (
                        SELECT TRIM(CONCAT_WS('\n',
                            NULLIF(a.address_line1, ''),
                            NULLIF(a.address_line2, ''),
                            NULLIF(a.city, ''),
                            NULLIF(a.state, ''),
                            NULLIF(a.pincode, '')
                        ))
                        FROM `tabAddress` a
                        INNER JOIN `tabDynamic Link` dl 
                            ON dl.parent = a.name
                            AND dl.parenttype = 'Address'
                            AND dl.link_doctype = 'Customer'
                            AND dl.link_name = c.name
                        ORDER BY a.is_primary_address DESC
                        LIMIT 1
                    ),
                    ''
                ) as address
            FROM `tabCustomer` c
            WHERE c.customer_group = 'Guest House'
                AND c.name LIKE %(search_term)s
            LIMIT 10
            """,
            {"search_term": f"%{search_term}%"},
            as_dict=True,
        )

        return customers
    except Exception as e:
        frappe.log_error(
            message=f"Error in get_customers_search: {str(e)}",
            title="Guest House API Error",
        )
        return []


@frappe.whitelist()
def get_services_list():
    """
    Get all additional services with their configured amounts and guest types from GH Settings.

    Returns:
        list: List of services with service name, amount, and guest_type
    """
    try:
        return frappe.db.sql(
            """
            SELECT 
                gas.service,
                COALESCE(rbas.amount, 0) as amount,
                COALESCE(rbas.guest_type, '') as guest_type
            FROM `tabGH Additional Service` gas
            LEFT JOIN `tabGH Room Booking Additional Service` rbas
                ON rbas.service = gas.name 
                AND rbas.parenttype = 'GH Settings'
                AND rbas.parentfield = 'room_services'
            ORDER BY gas.service
            """,
            as_dict=True,
        )
    except Exception as e:
        frappe.log_error(
            message=f"Error in get_services_list: {str(e)}",
            title="Guest House API Error",
        )
        return []


@frappe.whitelist()
def get_room_types():
    """
    Get all room types
    """
    try:
        room_types = frappe.get_all(
            "GH Room Amount Settings", fields=["room_type", "guest_type", "amount"]
        )
        return room_types
    except Exception as e:
        frappe.log_error(
            message=f"Error in get_room_types: {str(e)}", title="Guest House API Error"
        )
        return []


def _check_room_availability_for_range(room_id: str, from_date, to_date) -> bool:
    """
    Check if a room is available for the given date range.

    A room is available if there are no bookings that overlap with the requested period.
    Overlap logic: existing_check_out > new_check_in AND existing_check_in < new_check_out

    Args:
        room_id: Room ID to check
        from_date: Requested check-in date
        to_date: Requested check-out date

    Returns:
        True if room is available, False otherwise
    """
    from_date_obj = getdate(from_date)
    to_date_obj = getdate(to_date)

    # Standard check-in and check-out times
    requested_check_in = datetime.combine(from_date_obj, CHECK_IN_TIME)
    requested_check_out = datetime.combine(to_date_obj, CHECK_OUT_TIME)

    # Query existing bookings for this room that might overlap
    # Using same date-based overlap logic as _fetch_rooms_and_bookings:
    # For single date: from_date <= check_date AND to_date >= check_date
    # For date range: booking.from_date <= range.to_date AND booking.to_date >= range.from_date
    existing_bookings = frappe.db.sql(
        """
        SELECT DISTINCT
            rb.name,
            rb.from_date,
            rb.to_date
        FROM `tabGH Room Booking` rb
        INNER JOIN `tabGH Room Booking Details` rbd
            ON rbd.parent = rb.name
            AND rbd.parentfield = 'room_details'
        WHERE rbd.room = %(room_id)s
            AND rb.docstatus != 2

            AND (
                -- Date ranges overlap if: booking.from_date <= range.to_date AND booking.to_date >= range.from_date
                rb.from_date <= %(to_date)s
                AND rb.to_date >= %(from_date)s
            )
    """,
        {"room_id": room_id, "from_date": from_date, "to_date": to_date},
        as_dict=True,
    )

    # Check if any booking actually overlaps
    for booking in existing_bookings:
        existing_check_in = datetime.combine(getdate(booking.from_date), CHECK_IN_TIME)
        existing_check_out = datetime.combine(getdate(booking.to_date), CHECK_OUT_TIME)

        # Two bookings overlap if: existing_check_out > new_check_in AND existing_check_in < new_check_out
        if (
            existing_check_out > requested_check_in
            and existing_check_in < requested_check_out
        ):
            return False  # Room is not available

    return True  # Room is available


@frappe.whitelist()
def get_available_rooms(from_date, to_date):
    """
    Get all available rooms for a given date range.

    Args:
        from_date (str): Check-in date in YYYY-MM-DD format
        to_date (str): Check-out date in YYYY-MM-DD format

    Returns:
        dict: {
            "status": "success",
            "from_date": "2025-01-27",
            "to_date": "2025-01-30",
            "rooms": [
                {
                    "room_id": "0-101",
                    "room_details": "101",
                    "floor": "0"
                }
            ],
            "total_available": 10
        }
    """
    try:
        # Parse and validate dates
        from_date_obj = getdate(from_date)
        to_date_obj = getdate(to_date)

        if from_date_obj > to_date_obj:
            return {
                "status": "error",
                "message": "Check-in date cannot be after check-out date",
                "from_date": str(from_date),
                "to_date": str(to_date),
                "rooms": [],
                "total_available": 0,
            }

        if from_date_obj == to_date_obj:
            return {
                "status": "error",
                "message": "Check-in date and check-out date cannot be the same. Minimum stay is 1 night",
                "from_date": str(from_date),
                "to_date": str(to_date),
                "rooms": [],
                "total_available": 0,
            }

        # Fetch all rooms
        all_rooms = frappe.get_all(
            "GH Room",
            filters={"enabled": 1},
            fields=["name", "room_number", "floor", "room_type"],
            order_by="floor, room_number",
        )

        # Check availability for each room
        available_rooms = []
        for room in all_rooms:
            if _check_room_availability_for_range(room.name, from_date, to_date):
                available_rooms.append(
                    {
                        "room_id": room.name,
                        "room_details": room.room_number,
                        "floor": room.floor,
                        "room_type": room.room_type,
                    }
                )

        return {
            "status": "success",
            "from_date": str(from_date_obj),
            "to_date": str(to_date_obj),
            "rooms": available_rooms,
            "total_available": len(available_rooms),
        }

    except Exception as e:
        frappe.log_error(
            message=f"Error in get_available_rooms: {str(e)}",
            title="Guest House API Error",
        )
        return {
            "status": "error",
            "message": str(e),
            "from_date": str(from_date) if from_date else None,
            "to_date": str(to_date) if to_date else None,
            "rooms": [],
            "total_available": 0,
        }


@frappe.whitelist()
def create_customer():
    data = json.loads(frappe.request.data)
    address = data.pop("address")
    contact = data.pop("phone")
    customer = frappe.get_doc(
        {
            "doctype": "Customer",
            **data,
        }
    )

    if is_null_or_blank(customer.custom_aadhar_no):
        frappe.throw("Aadhar Number is required")
    customer.insert(ignore_permissions=True)

    address_doc = frappe.get_doc(
        {
            "doctype": "Address",
            "address_line1": address.get("address_line1"),
            "address_line2": address.get("address_line2"),
            "city": address.get("city"),
            "country": address.get("country"),
            "pincode": address.get("pincode"),
            "state": address.get("state"),
        }
    )
    address_doc.append(
        "links",
        {
            "link_doctype": "Customer",
            "link_name": customer.name,
        },
    )
    address_doc.insert(ignore_permissions=True)

    contact_doc = frappe.get_doc(
        {
            "doctype": "Contact",
            "first_name": customer.customer_name,
        }
    )
    contact_doc.append(
        "phone_nos",
        {
            "phone": contact,
            "is_primary_phone": True,
        },
    )

    contact_doc.append(
        "links",
        {
            "link_doctype": "Customer",
            "link_name": customer.name,
        },
    )
    contact_doc.insert(ignore_permissions=True)

    return json.dumps(customer.name)


@frappe.whitelist()
def create_booking():
    data = json.loads(frappe.request.data)

    room_details = data.pop("room_details")
    additional_services = data.pop("additional_services")
    doc = frappe.get_doc(
        {
            "doctype": "GH Room Booking",
            **data,
        }
    )
    for room_data in room_details:
        doc.append(
            "room_details",
            {
                "room": room_data.get("room"),
                "amount": room_data.get("amount"),
            },
        )
    
    if additional_services:
        for additional_service in additional_services:
            if additional_service.get("service"):
                doc.append(
                    "additional_services",
                    {
                        "service": additional_service.get("service"),
                        "amount": additional_service.get("amount"),
                        "quantity": additional_service.get("quantity"),
                    },
                )
    doc.insert()
    return json.dumps(doc.name)


@frappe.whitelist()
def search_bookings():

    request_data = frappe._dict(json.loads(frappe.request.data))
    page = int(request_data.get("page", 0))
    page_size = int(request_data.get("page_size", 10))
    limit_start = page * page_size

    where_conditions = []
    params = {}

    where_conditions.append("1=1")

    search_field = request_data.get("search_field")
    search_text = request_data.get("search_text")
    if search_field == "customer" and search_text and search_text.strip() != "":
        where_conditions.append("customer LIKE %(customer)s")
        params["customer"] = f"%{search_text.strip()}%"

    if request_data.get("from_date"):
        where_conditions.append("from_date >= %(from_date)s")
        params["from_date"] = request_data.get("from_date")

    if request_data.get("to_date"):
        where_conditions.append("to_date <= %(to_date)s")
        params["to_date"] = request_data.get("to_date")

    if request_data.get("devotee") and not is_null_or_blank(
        request_data.get("devotee")
    ):
        clean_devotees = [
            d.upper() if isinstance(d, str) and d.strip() else d
            for d in request_data.get("devotee")
            if d and (not isinstance(d, str) or d.strip())
        ]
        if len(clean_devotees) > 0:
            devotee_placeholders = ", ".join(
                [f"%(devotee_{i})s" for i in range(len(clean_devotees))]
            )
            where_conditions.append(f"devotee IN ({devotee_placeholders})")
            for i, devotee in enumerate(clean_devotees):
                params[f"devotee_{i}"] = devotee

    sort_field = request_data.get("sort_field", "creation")
    sort_order = request_data.get("sort_order", "desc").upper()
    if sort_order not in ["ASC", "DESC"]:
        sort_order = "DESC"

    query = f"""    
        SELECT * FROM `tabGH Room Booking`
        WHERE {" AND ".join(where_conditions)}
          ORDER BY {sort_field} {sort_order}
        LIMIT %(limit_start)s, %(page_size)s
    """
    params["limit_start"] = limit_start
    params["page_size"] = page_size
    result = frappe.db.sql(query, params, as_dict=True)
    return result


# data: {'page': 0, 'page_size': 50, 'search_field': 'full_name', 'search_text': '', 'from_date': None, 'to_date': None, 'devotee': ['HRND']}

# data: {'page': 0, 'page_size': 50, 'search_field': 'full_name', 'search_text': '', 'from_date': None, 'to_date': None, 'devotee': None}


def get_invoice_outstanding_and_paid(sales_invoice_name, company, cost_head, customer_group, report_date):
    """
    Get outstanding and paid amounts for a Sales Invoice using Payment Ledger Entry logic
    similar to accounts receivable report.
    
    Logic from accounts_receivable report:
    - Invoiced: amount > 0 where voucher_type = "Sales Invoice" and voucher_no = invoice
    - Paid: 
      * amount > 0 where voucher_type in ["Payment Entry", "Journal Entry"] 
        and against_voucher_no = invoice and voucher_no != against_voucher_no
      * amount < 0 where voucher_type = "Sales Invoice" 
        and voucher_no = against_voucher_no = invoice (self-reference)
      * amount < 0 where voucher_type in ["Payment Entry", "Journal Entry"] 
        and against_voucher_no = invoice
    - Credit Note: amount < 0 where voucher_type = "Sales Invoice" 
      and voucher_no = invoice and voucher_no != against_voucher_no
    
    Args:
        sales_invoice_name: Name of the Sales Invoice
        company: Company name
        cost_head: Cost head (cost_center) filter
        customer_group: Customer group filter
        report_date: Report date (posting_date filter) - can be string or date object
    
    Returns:
        dict with outstanding_amount and paid_amount
    """
    ple = qb.DocType("Payment Ledger Entry")
    customer = qb.DocType("Customer")
    
    # Convert report_date to date object if it's a string
    if isinstance(report_date, str):
        report_date = getdate(report_date)
    
    # Build base filters similar to accounts receivable report
    base_filters = []
    base_filters.append(ple.delinked == 0)
    base_filters.append(ple.company == company)
    base_filters.append(ple.party_type == "Customer")
    base_filters.append(ple.posting_date <= report_date)
    
    base_filters.append(ple.cost_head == cost_head)


    
    if customer_group:
        # Join with Customer to filter by customer_group
        customers_in_group = (
            qb.from_(customer)
            .select(customer.name)
            .where(customer.customer_group == customer_group)
        )
        base_filters.append(ple.party.isin(customers_in_group))
    
    # Get invoiced amount (positive amounts where voucher is the invoice)
    invoiced_query = (
        qb.from_(ple)
        .select(Sum(ple.amount).as_("amount"))
        .where(
            (ple.voucher_type == "Sales Invoice")
            & (ple.voucher_no == sales_invoice_name)
            & (ple.amount > 0)
        )
        .where(Criterion.all(base_filters))
    )
    
    invoiced_result = invoiced_query.run()
    invoiced = flt(invoiced_result[0][0]) if invoiced_result and invoiced_result[0][0] else 0.0
    
    # Get paid amount - following accounts receivable report logic:
    # In the report, paid is stored as negative, so we sum negative values
    # Payment Entry/Journal Entry with positive amount against invoice
    paid_from_pe_je_positive = (
        qb.from_(ple)
        .select(Sum(ple.amount).as_("amount"))
        .where(
            (ple.voucher_type.isin(["Payment Entry", "Journal Entry"]))
            & (ple.against_voucher_type == "Sales Invoice")
            & (ple.against_voucher_no == sales_invoice_name)
            & (ple.voucher_no != sales_invoice_name)
            & (ple.amount > 0)
        )
        .where(Criterion.all(base_filters))
    )
    
    paid_pe_je_positive_result = paid_from_pe_je_positive.run()
    # In report: row.paid -= amount (where amount > 0), so this reduces paid (is a payment)
    paid_pe_je_positive = flt(paid_pe_je_positive_result[0][0]) if paid_pe_je_positive_result and paid_pe_je_positive_result[0][0] else 0.0
    
    # Self-referencing invoice (negative amount, self-reference)
    paid_from_self_ref = (
        qb.from_(ple)
        .select(Sum(ple.amount).as_("amount"))
        .where(
            (ple.voucher_type == "Sales Invoice")
            & (ple.voucher_no == sales_invoice_name)
            & (ple.against_voucher_type == "Sales Invoice")
            & (ple.against_voucher_no == sales_invoice_name)
            & (ple.amount < 0)
        )
        .where(Criterion.all(base_filters))
    )
    
    paid_self_ref_result = paid_from_self_ref.run()
    # In report: row.paid -= amount (where amount < 0), so this increases paid
    paid_self_ref = abs(flt(paid_self_ref_result[0][0])) if paid_self_ref_result and paid_self_ref_result[0][0] else 0.0
    
    # Payment Entry/Journal Entry with negative amount against invoice
    paid_from_pe_je_negative = (
        qb.from_(ple)
        .select(Sum(ple.amount).as_("amount"))
        .where(
            (ple.voucher_type.isin(["Payment Entry", "Journal Entry"]))
            & (ple.against_voucher_type == "Sales Invoice")
            & (ple.against_voucher_no == sales_invoice_name)
            & (ple.amount < 0)
        )
        .where(Criterion.all(base_filters))
    )
    
    paid_pe_je_negative_result = paid_from_pe_je_negative.run()
    # In report: row.paid -= amount (where amount < 0), so this increases paid
    paid_pe_je_negative = abs(flt(paid_pe_je_negative_result[0][0])) if paid_pe_je_negative_result and paid_pe_je_negative_result[0][0] else 0.0
    
    # Total paid amount: positive amounts reduce paid (are payments), negative amounts increase paid
    # So paid = abs(negative amounts) - positive amounts
    paid = flt(paid_self_ref + paid_pe_je_negative - paid_pe_je_positive, 2)
    
    # Get credit note amount (negative amounts where voucher is the invoice and it's NOT self-reference)
    credit_note_query = (
        qb.from_(ple)
        .select(Sum(ple.amount).as_("amount"))
        .where(
            (ple.voucher_type == "Sales Invoice")
            & (ple.voucher_no == sales_invoice_name)
            & (ple.amount < 0)
            & (
                (ple.against_voucher_type != "Sales Invoice")
                | (ple.against_voucher_no != sales_invoice_name)
            )
        )
        .where(Criterion.all(base_filters))
    )
    
    credit_note_result = credit_note_query.run()
    credit_note = abs(flt(credit_note_result[0][0])) if credit_note_result and credit_note_result[0][0] else 0.0
    
    # Calculate outstanding: invoiced - paid - credit_note
    outstanding = flt(invoiced - paid - credit_note, 2)
    
    return {
        "outstanding_amount": outstanding,
        "paid_amount": paid,
        "invoiced_amount": invoiced,
        "credit_note_amount": credit_note,
    }


@frappe.whitelist()
def get_booking_detailed_info(booking_id):
    booking = frappe.get_doc("GH Room Booking", booking_id)
    image_urls = frappe.get_all(
        "File",
        filters={
            "attached_to_name": booking.name,
            "attached_to_doctype": "GH Room Booking",
            "file_type": ["in", ["Image", "PNG", "JPG", "JPEG", "GIF", "SVG"]],
            "is_private": 0,
        },
        pluck="file_url",
    )
    booking_dict = booking.as_dict()

    if image_urls:
        processed_urls = []
        for url in image_urls:
            decoded_url = urllib.parse.unquote(url)
            cleaned_url = decoded_url.replace("\\", "/").replace("%5C", "/")
            processed_urls.append(f"https://{frappe.local.site}{cleaned_url}")

        if "image_urls" not in booking_dict:
            booking_dict["image_urls"] = []
        booking_dict["image_urls"].extend(processed_urls)
    
    # Get outstanding and paid amounts from Sales Invoice
    try:
        settings = frappe.get_cached_doc("GH Settings")
        company = settings.company or "Hare Krishna Movement Jaipur"
        cost_head = settings.cost_head or "Guest House"
        customer_group = "Guest House"
        report_date = getdate(nowdate())
        
        # Get Sales Invoice linked to this booking
        sales_invoice = frappe.db.get_value(
            "Sales Invoice",
            {"gh_room_booking": booking_id, "docstatus": ["!=", 2]},
            "name",
            order_by="creation desc"
        )
        
        
        if sales_invoice:
            booking_dict["sales_invoice"] = sales_invoice
            invoice_amounts = get_invoice_outstanding_and_paid(
                sales_invoice,
                company,
                cost_head,
                customer_group,
                report_date
            )
            booking_dict["outstanding_amount"] = invoice_amounts["outstanding_amount"]
            booking_dict["paid_amount"] = invoice_amounts["paid_amount"]
            booking_dict["invoiced_amount"] = invoice_amounts["invoiced_amount"]
        else:
            booking_dict["outstanding_amount"] = 0.0
            booking_dict["paid_amount"] = 0.0
            booking_dict["invoiced_amount"] = 0.0
    except Exception as e:
        frappe.log_error(
            message=f"Error getting invoice amounts for booking {booking_id}: {str(e)}",
            title="Guest House API Error",
        )
        booking_dict["outstanding_amount"] = 0.0
        booking_dict["paid_amount"] = 0.0
        booking_dict["invoiced_amount"] = 0.0

    return booking_dict


@frappe.whitelist()
def cancel_booking(booking_id):
    booking = frappe.get_doc("GH Room Booking", booking_id)
    if booking.docstatus == 0:
        frappe.db.set_value("GH Room Booking", booking_id, "docstatus", 2)
        # frappe.db.commit()  # v16: REMOVED - auto-commits after operation
    else:
        frappe.throw("Not Allowed to cancel")

    


@frappe.whitelist()
def generate_invoice(booking_id):
    settings = frappe.get_cached_doc("GH Settings")
    booking = frappe.get_doc("GH Room Booking", booking_id)
    invoice_dict = {
        "doctype": "Sales Invoice",
        "set_posting_time": True,
        "posting_date": frappe.utils.today(),
        "posting_time": frappe.utils.nowtime(),
        "company": settings.company,
        "customer": booking.customer,
        "gh_room_booking": booking.name,
        "due_date": frappe.utils.today(),
        "cost_head": settings.cost_head,
        "cost_center": settings.cost_center,
        "default_sales_income_account": settings.income_account,
    }


    item_tax_template =  settings.item_tax_template

    percentage = extract_tax_percentage(item_tax_template)

    total_amount = booking.amount

    taxable_amount = (total_amount / (100 + percentage)) * 100

    # Calculate tax rate for CGST and SGST (each is half of total GST percentage)
    tax_rate = percentage / 2

    #### calcalute taxable amount

    invoice = frappe.get_doc(invoice_dict)
    invoice.append("items", {
        "item_code": settings.item_code,
        "qty": 1,
        "rate": taxable_amount,
        "cost_center": settings.cost_center,
        "cost_head": settings.cost_head,
    })


    invoice.append("taxes", {
       "charge_type" : "On Net Total",
       "account_head" : settings.cgst_account,
       "rate": tax_rate,
       "description": settings.cgst_account or "CGST",
       "cost_center": settings.cost_center,
       "cost_head": settings.cost_head,
    })
    invoice.append("taxes", {
       "charge_type" : "On Net Total",
       "account_head" : settings.sgst_account,
       "rate": tax_rate,
       "description": settings.sgst_account or "SGST",
       "cost_center": settings.cost_center,
       "cost_head": settings.cost_head,
    })

    invoice.insert()
    invoice.submit()
    booking.sales_invoice = invoice.name
    booking.save()
    booking.submit()
    frappe.db.commit()  # v16: REVIEW - check if needed
    return invoice.name


def extract_tax_percentage(tax_template):
	"""
	Extract tax percentage from item tax template string.
	Example: "GST - 5% - TSFJ" returns 5.0
	"""
	if not tax_template:
		return 0
	
	# Search for pattern like "5%" or "12%" etc.
	match = re.search(r'(\d+(?:\.\d+)?)\s*%', tax_template)
	
	if match:
		return float(match.group(1))
	
	return 0


@frappe.whitelist()
def upload_booking_images(booking_id):
    """
    Upload images to GH Room Booking document.

    Args:
        booking_id: The name of the GH Room Booking document

    Returns:
        dict: Status and message
    """
    try:
        # Verify booking exists
        if not frappe.db.exists("GH Room Booking", booking_id):
            return {"status": "error", "message": f"Booking {booking_id} not found"}

        files = frappe.request.files.getlist("image")

        if not files:
            return {"status": "error", "message": "No files provided"}

        uploaded_files = []

        for index, file in enumerate(files):
            content = file.stream.read()
            original_filename = file.filename or f"image_{index}.jpg"
            content_type = guess_type(original_filename)[0] or "image/jpeg"

            # Optimize image if it's an image
            if content_type.startswith("image/"):
                content = optimize_image(content=content, content_type=content_type)

            # Generate filename
            filename = f"booking_{booking_id}_{index}_{original_filename}"

            # Set uploaded file for Frappe
            frappe.local.uploaded_file = content
            frappe.local.uploaded_filename = filename

            # Create File document
            file_doc = frappe.get_doc(
                {
                    "doctype": "File",
                    "file_type": "Image",
                    "attached_to_doctype": "GH Room Booking",
                    "attached_to_name": booking_id,
                    "folder": "Home/Attachments",
                    "file_name": filename,
                    "is_private": 0,
                    "content": content,
                }
            ).save(ignore_permissions=1)

            uploaded_files.append(file_doc.file_url)

        frappe.db.commit()  # v16: REVIEW - check if needed

        return {
            "status": "success",
            "message": f"Successfully uploaded {len(uploaded_files)} image(s)",
            "files": uploaded_files,
        }

    except Exception as e:
        frappe.log_error(
            message=f"Error in upload_booking_images: {str(e)}",
            title="Guest House API Error",
        )
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def verify_pan(pan):

    return get_pan_status_india_compliance(pan)




from erpnext.accounts.report.customer_ledger_summary.customer_ledger_summary import execute as customer_ledger_summary_execute


@frappe.whitelist()
def get_customer_ledger_statement(customer = []):

    settings = frappe.get_cached_doc("GH Settings")
    data = json.loads(frappe.request.data)
    from_date = data.get("from_date")
    to_date = data.get("to_date")
    company = settings.company

    filters = {
        "company": company,
        "from_date": from_date,
        "to_date": to_date,
        "customer_group": settings.customer_group,
        "customer": customer,
    }

    columns, data = customer_ledger_summary_execute(filters)
    return data


@frappe.whitelist()
def rename_room_type():
    data = json.loads(frappe.request.data)

    frappe.db.set_value("GH Room Type", data.get("old_name"), "room_title", data.get("new_name"))

    frappe.rename_doc("GH Room Type", data.get("old_name"), data.get("new_name"))

    # frappe.db.commit()  # v16: REMOVED - auto-commits after operation


@frappe.whitelist()
def rename_guest_category():
    data = json.loads(frappe.request.data)

    frappe.db.set_value("GH Guest Category", data.get("old_name"), "guest_category", data.get("new_name"))

    frappe.rename_doc("GH Guest Category", data.get("old_name"), data.get("new_name"))

    # frappe.db.commit()  # v16: REMOVED - auto-commits after operation



@frappe.whitelist()
def guest_house_settings():
    settings = frappe.get_doc("GH Settings" , "GH Settings")
    result = settings.as_dict()
    return result



import base64
from frappe.utils import now_datetime

@frappe.whitelist()
def download_invoice_pdf(id):
    """
    Generate PDF for Sales Invoice and return as base64 encoded string for mobile app.
    Uses frappe.get_print() with as_pdf=True to properly handle letterhead.
    """
    if not frappe.db.exists("Sales Invoice", id):
        frappe.throw("Sales Invoice not found")

    doc = frappe.get_doc("Sales Invoice", id)
    doc.check_permission("print")

    # Use frappe.get_print() with as_pdf=True directly - this properly handles letterhead
    pdf = frappe.get_print(
        doctype="Sales Invoice",
        name=id,
        print_format="HKM - Sales GST Tax Invoice",
        no_letterhead=0,
        letterhead="General - HKMJ",
        as_pdf=True,
        pdf_options={
            "page-size": "A3",
            "orientation": "Portrait",
        }
    )
    
    # Encode PDF to base64
    pdf_base64 = base64.b64encode(pdf).decode("utf-8")
    data_url = f"data:application/pdf;base64,{pdf_base64}"
    
    return {
        "status": "success",
        "pdf_base64": data_url,
        "filename": f"{id}-{now_datetime().strftime('%Y%m%d%H%M%S')}.pdf"
    }
  
