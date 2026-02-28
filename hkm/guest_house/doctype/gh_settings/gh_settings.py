# Copyright (c) 2025, Narahari Dasa and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class GHSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from hkm.guest_house.doctype.gh_floor_wise_room_detail.gh_floor_wise_room_detail import GHFloorwiseRoomDetail
		from hkm.guest_house.doctype.gh_room_amount_settings.gh_room_amount_settings import GHRoomAmountSettings
		from hkm.guest_house.doctype.gh_room_booking_additional_service.gh_room_booking_additional_service import GHRoomBookingAdditionalService

		cgst_account: DF.Link
		check_in_time: DF.Time | None
		check_out_time: DF.Time | None
		company: DF.Link
		cost_center: DF.Link
		cost_head: DF.Link
		floor_room_details: DF.Table[GHFloorwiseRoomDetail]
		income_account: DF.Link
		item_code: DF.Link
		item_tax_template: DF.Link | None
		room_charges: DF.Table[GHRoomAmountSettings]
		room_services: DF.Table[GHRoomBookingAdditionalService]
		sgst_account: DF.Link
	# end: auto-generated types

	pass
