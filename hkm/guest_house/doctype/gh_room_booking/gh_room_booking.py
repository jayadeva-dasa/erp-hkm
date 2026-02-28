# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import get_link_to_form, getdate, get_datetime, now_datetime
from datetime import time, datetime


class GHRoomBooking(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from hkm.guest_house.doctype.gh_room_booking_additional_service.gh_room_booking_additional_service import GHRoomBookingAdditionalService
		from hkm.guest_house.doctype.gh_room_booking_details.gh_room_booking_details import GHRoomBookingDetails

		actual_check_in: DF.Datetime | None
		actual_check_out: DF.Datetime | None
		additional_services: DF.Table[GHRoomBookingAdditionalService]
		address: DF.Data | None
		amended_from: DF.Link | None
		amount: DF.Currency
		booking_status: DF.Literal["Booked", "Invoiced"]
		customer: DF.Link
		devotee: DF.Link
		from_date: DF.Date | None
		guest_type: DF.Link
		room_details: DF.Table[GHRoomBookingDetails]
		sales_invoice: DF.Link | None
		to_date: DF.Date | None
		total_person: DF.Int
	# end: auto-generated types

	def before_insert(self):
		address = frappe.db.sql(
		"""
		SELECT 
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
			) AS address
		FROM `tabCustomer` c
		WHERE c.customer_group = 'Guest House'
		AND c.name = %(customer)s
		""",
		{"customer": self.customer},
		as_dict=True,
	)

		if not address and address[0]["address"] :
			frappe.throw(_("Address is required"))
		else:
			self.address = address[0]["address"]

	def validate_dates(self):
		"""Validate that from_date is not after to_date and not same as to_date
		Same date is not allowed because check-in (12:00 PM) would be after check-out (10:00 AM)
		"""
		if self.from_date and self.to_date:
			from_date_obj = getdate(self.from_date)
			to_date_obj = getdate(self.to_date)
			
			if from_date_obj > to_date_obj:
				frappe.throw(
					_("Check-In Date cannot be after Check-Out Date"),
					title=_("Invalid Date Range")
				)
			
			if from_date_obj == to_date_obj:
				frappe.throw(
					_("Check-In Date and Check-Out Date cannot be the same. Minimum stay is 1 night (check-in at 12:00 PM, check-out at 10:00 AM next day)"),
					title=_("Invalid Date Range")
				)

	def validate_full_name(self):
		"""Validate that full_name is provided"""
		if not self.full_name or not self.full_name.strip():
			frappe.throw(
				_("Full Name is required"),
				title=_("Missing Required Field")
			)

	def validate_address(self):
		"""Validate that address is provided"""
		if not self.address or not self.address.strip():
			frappe.throw(
				_("Address is required"),
				title=_("Missing Required Field")
			)

	def validate_room_availability(self):
		"""Validate room availability using standard booking dates with standard times:
		- Check-in: 12:00 PM (noon) on from_date
		- Check-out: 10:00 AM on to_date
		
		This prevents double booking by checking if any existing booking overlaps
		with the requested booking period.
		"""
		if not self.from_date or not self.to_date:
			return

		if not self.room_details:
			return

		# Get list of room IDs from current booking
		current_rooms = [row.room for row in self.room_details if row.room]
		
		if not current_rooms:
			return

		# Set temporary name for new documents
		if not self.name:
			self.name = "New GH Room Booking"

		# Standard check-in and check-out times
		CHECK_IN_TIME = time(12, 0, 0)  # 12:00 PM
		CHECK_OUT_TIME = time(10, 0, 0)  # 10:00 AM

		# Convert Date fields to Datetime with standard times for current booking
		current_check_in = datetime.combine(getdate(self.from_date), CHECK_IN_TIME)
		current_check_out = datetime.combine(getdate(self.to_date), CHECK_OUT_TIME)

		# Query existing bookings for same rooms that might overlap
		# Using date comparison first (more efficient), then datetime comparison for accuracy
		existing_bookings = frappe.db.sql("""
			SELECT DISTINCT
				rb.name,
				rb.from_date,
				rb.to_date,
				GROUP_CONCAT(DISTINCT rbd.room) as rooms
			FROM `tabGH Room Booking` rb
			INNER JOIN `tabGH Room Booking Details` rbd
				ON rbd.parent = rb.name
				AND rbd.parentfield = 'room_details'
			WHERE rb.name != %(name)s
				AND rb.docstatus < 2
				AND rbd.room IN %(rooms)s
				AND (
					-- Date ranges that might overlap (loose check to reduce candidates)
					-- Existing booking's check-out date >= new booking's check-in date - 1 day
					-- AND existing booking's check-in date <= new booking's check-out date + 1 day
					rb.to_date >= DATE_SUB(%(from_date)s, INTERVAL 1 DAY)
					AND rb.from_date <= DATE_ADD(%(to_date)s, INTERVAL 1 DAY)
				)
			GROUP BY rb.name, rb.from_date, rb.to_date
		""", {
			"name": self.name,
			"rooms": current_rooms,
			"from_date": self.from_date,
			"to_date": self.to_date
		}, as_dict=True)

		# Filter bookings that actually overlap based on check-in/check-out times
		# Two bookings overlap if: (existing_check_out > new_check_in) AND (existing_check_in < new_check_out)
		# This allows same-day transitions: booking ends 10 AM, new booking starts 12 PM same day
		overlapping_bookings = []
		for booking in existing_bookings:
			# Convert existing booking dates to datetime with standard times
			existing_check_in = datetime.combine(getdate(booking.from_date), CHECK_IN_TIME)
			existing_check_out = datetime.combine(getdate(booking.to_date), CHECK_OUT_TIME)
			
			# Check for overlap: existing booking's check-out > new booking's check-in
			# AND existing booking's check-in < new booking's check-out
			if existing_check_out > current_check_in and existing_check_in < current_check_out:
				overlapping_bookings.append(booking)

		if overlapping_bookings:
			# Collect overlapping room information
			overlapping_rooms = []
			for booking in overlapping_bookings:
				booking_rooms = booking.rooms.split(',') if booking.rooms else []
				overlapping_rooms.extend([room for room in booking_rooms if room in current_rooms])
			
			unique_overlapping_rooms = list(set(overlapping_rooms))
			booking_names = [booking.name for booking in overlapping_bookings]
			
			# Get room numbers for display
			try:
				room_names = frappe.db.get_all(
					"GH Room",
					filters={"name": ["in", unique_overlapping_rooms]},
						pluck="room_details"
				)
				# Filter out None values
				room_names = [name for name in room_names if name]
				room_display = ", ".join(room_names) if room_names else ", ".join(unique_overlapping_rooms)
			except:
				room_display = ", ".join(unique_overlapping_rooms)
			
			# Format booking period for error message
			from_date_str = frappe.format(self.from_date, {"fieldtype": "Date"})
			to_date_str = frappe.format(self.to_date, {"fieldtype": "Date"})
			booking_period = _("{0} (12:00 PM) to {1} (10:00 AM)").format(from_date_str, to_date_str)
			
			booking_links = ", ".join([get_link_to_form("GH Room Booking", name) for name in booking_names[:3]])
			if len(booking_names) > 3:
				booking_links += _(" and {0} more").format(len(booking_names) - 3)
			
			msg = _("Room(s) {0} are already booked for the period {1}. Overlapping booking(s): {2}").format(
				frappe.bold(room_display),
				frappe.bold(booking_period),
				booking_links
			)
			
			frappe.throw(msg, title=_("Room Already Booked"))

	def validate_check_in_out_times(self):
		"""Validate that actual check-in/check-out times are reasonable
		Compares actual times with booking dates (not datetimes)
		"""
		if self.actual_check_in and self.from_date:
			# Get dates for comparison (ignore time component)
			from_date_obj = getdate(self.from_date)
			actual_check_in_date = getdate(self.actual_check_in)
			
			# Allow early check-in but limit to 1 day before scheduled check-in date
			if actual_check_in_date < from_date_obj:
				days_diff = (from_date_obj - actual_check_in_date).days
				if days_diff > 1:
					frappe.throw(
						_("Actual check-in time cannot be more than 1 day before scheduled check-in date ({0})").format(
							frappe.format(self.from_date, {"fieldtype": "Date"})
						),
						title=_("Invalid Check-In Time")
					)
			
			# Check-in should not be after check-out date
			if self.to_date and actual_check_in_date > getdate(self.to_date):
				frappe.throw(
					_("Actual check-in time cannot be after scheduled check-out date ({0})").format(
						frappe.format(self.to_date, {"fieldtype": "Date"})
					),
					title=_("Invalid Check-In Time")
				)

		if self.actual_check_out:
			if not self.actual_check_in:
				frappe.throw(
					_("Cannot check out without checking in first"),
					title=_("Invalid Check-Out")
				)
			
			# Check-out must be after check-in
			if self.actual_check_out < self.actual_check_in:
				frappe.throw(
					_("Check-out time cannot be before check-in time"),
					title=_("Invalid Check-Out Time")
				)

	def update_booking_status(self):
		"""Update booking status based on check-in/check-out times"""
		if self.actual_check_out:
			self.booking_status = "Completed"
		elif self.actual_check_in:
			self.booking_status = "Checked In"
		else:
			# Only set to "Booked" if not already set (preserve other statuses)
			if not self.booking_status:
				self.booking_status = "Booked"

	@frappe.whitelist()
	def record_check_in(self, check_in_time=None):
		"""Record actual check-in time for the guest"""
		if self.actual_check_in:
			frappe.throw(
				_("Check-in has already been recorded for this booking"),
				title=_("Already Checked In")
			)
		
		if not check_in_time:
			check_in_time = now_datetime()
		else:
			check_in_time = get_datetime(check_in_time)
		
		self.actual_check_in = check_in_time
		self.checked_in_by = frappe.session.user
		self.booking_status = "Checked In"
		self.save()
		frappe.msgprint(_("Check-in recorded successfully"), indicator="green")

	@frappe.whitelist()
	def record_check_out(self, check_out_time=None):
		"""Record actual check-out time for the guest"""
		if not self.actual_check_in:
			frappe.throw(
				_("Cannot check out without checking in first"),
				title=_("Check-In Required")
			)
		
		if self.actual_check_out:
			frappe.throw(
				_("Check-out has already been recorded for this booking"),
				title=_("Already Checked Out")
			)
		
		if not check_out_time:
			check_out_time = now_datetime()
		else:
			check_out_time = get_datetime(check_out_time)
		
		self.actual_check_out = check_out_time
		self.checked_out_by = frappe.session.user
		self.booking_status = "Completed"
		self.save()
		frappe.msgprint(_("Check-out recorded successfully"), indicator="green")

	
