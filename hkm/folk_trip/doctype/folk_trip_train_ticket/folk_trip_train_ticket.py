# Copyright (c) 2021, NRHD and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class FOLKTripTrainTicket(Document):
	def validate(self):

		self.validate_seat_duplicacy()
		self.validate_pnr()
		self.validate_yatri_duplicacy()
		self.clear_yatri_names()

	def clear_yatri_names(self):
		for psg in self.passengers:
			if psg.allocated_to is None:
				psg.allocated_name = ""
		return
	def validate_yatri_duplicacy(self):
		for psg in self.passengers:
			data = frappe.db.sql("""
								SELECT
									tt.name
								FROM `tabFOLK Trip Train Ticket` tt
								JOIN `tabFOLK Trip Train Passenger` tp ON tp.parent = tt.name
								WHERE tt.train = '{}'
								AND tp.allocated_to = '{}'
								AND tt.name <> '{}'
								""".format(self.train,psg.allocated_to,self.pnr_number),as_dict = 0)
			if len(data)> 0:
				frappe.throw("Passenger: <b>{}</b> is already allocated a Seat in Train".format(psg.allocated_to))
		list_yatri = [psg.allocated_to for psg in self.passengers if psg.allocated_to is not None]
		unique_yatri = list(set(list_yatri))

		if len(unique_yatri) != len(list_yatri):
			frappe.throw("Yatris are duplicated. Please Check.")

		return

	def validate_pnr(self):
		if len(self.pnr_number) != 10:
			frappe.throw("PNR number should be of 10 digits only.")
		return
	def validate_seat_duplicacy(self):
		for psg in self.passengers:
			data = frappe.db.sql("""
									SELECT
										tt.name
									FROM `tabFOLK Trip Train Ticket` tt
									JOIN `tabFOLK Trip Train Passenger` tp
									ON tp.parent = tt.name
									WHERE tt.train = '{}'
									AND tp.coach_number = '{}'
									AND tp.seat_number  = '{}'
									AND tt.pnr_number <> '{}'
								""".format(self.train, psg.coach_number, psg.seat_number, self.pnr_number),as_dict=0)
			if len(data)>0:
				frappe.throw("This Seat Number <b>{}/{}</b> is already booked in another PNR : <b>{}</b>".format(psg.coach_number, psg.seat_number, data[0][0]))
		seat_comb = []
		for psg in self.passengers:
			seat_comb.append(psg.coach_number+"/"+str(psg.seat_number))
		list_seat_comb = set(seat_comb)
		unique_seat_comb = (list(list_seat_comb))
		if len(unique_seat_comb) != len(seat_comb):
			frappe.throw("Seats are duplicated. Please Check.")

		return
