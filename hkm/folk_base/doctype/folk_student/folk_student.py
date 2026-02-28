# -*- coding: utf-8 -*-
# Copyright (c) 2021, NRHD and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.website.website_generator import WebsiteGenerator

class FOLKStudent(WebsiteGenerator):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from hkm.folk_base.doctype.folk_student_book.folk_student_book import FOLKStudentBook

		aadhar_id: DF.Data | None
		address_line_1: DF.Data | None
		address_line_2: DF.Data | None
		alternative_mobile_number: DF.Data | None
		ashraya: DF.Literal["", "Sraddhawan", "Sevak", "Sadhak", "Upasak", "Charanashraya"]
		batch: DF.Data | None
		blood_group: DF.Literal["", "A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]
		book_reading: DF.Table[FOLKStudentBook]
		c_address_line_1: DF.Data | None
		c_address_line_2: DF.Data | None
		c_city: DF.Data | None
		c_pincode: DF.Data | None
		c_state: DF.Data | None
		calling_group: DF.Link | None
		chanting_rounds: DF.Int
		city: DF.Data | None
		company_name: DF.Data | None
		date_of_birth: DF.Date | None
		date_of_leaving: DF.Date | None
		degree_pursuing: DF.Link | None
		degree_pursuing_since: DF.Literal["2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025", "2026", "2027", "2028", "2029", "2030"]
		designation: DF.Data | None
		enabled: DF.Check
		father_mobile_no: DF.Data | None
		father_name: DF.Data | None
		folk_guide: DF.Link | None
		folk_plus: DF.Check
		folk_resident: DF.Check
		from_institute: DF.Data | None
		from_institute_degree: DF.Data | None
		full_name: DF.Data | None
		gender: DF.Literal["Male", "Female"]
		image: DF.AttachImage | None
		initiated: DF.Check
		initiated_name: DF.Data | None
		institute_name: DF.Data | None
		leaving_certificate_number: DF.Data | None
		marriage_anniversary: DF.Date | None
		married: DF.Check
		mother_name: DF.Data | None
		occupation: DF.Literal["", "Student", "Working", "Business"]
		otp: DF.Int
		pincode: DF.Data | None
		plus_level: DF.Literal["", "1", "2", "3", "4", "5"]
		plus_remarks: DF.LongText | None
		reason_for_leaving: DF.Text | None
		reference: DF.Literal["FOLK Guide", "FOLK Student", "Online", "Temple", "Book Distribution", "Other"]
		reference_remarks: DF.Data | None
		residency: DF.Link | None
		security_key: DF.Data | None
		short_name: DF.Data | None
		since: DF.Date | None
		state: DF.Data | None
		student_email_id: DF.Data | None
		student_mobile_number: DF.Data
		title: DF.Data | None
		user: DF.Link | None
		vehicle_license_id: DF.Data | None
		voter_id: DF.Data | None
		wifes_name: DF.Data | None
	# end: auto-generated types
	
	def validate(self):
		if not self.folk_resident:
			self.residency = None
			self.since = None
