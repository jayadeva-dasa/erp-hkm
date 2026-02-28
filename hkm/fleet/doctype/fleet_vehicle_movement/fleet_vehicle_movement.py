# Copyright (c) 2021, NRHD and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class FleetVehicleMovement(Document):
	def validate(self):
		self.validate_movement()
	def before_cancel(self):
		self.validate_movement_for_cancellation()
	def validate_movement(self):
		movements = frappe.db.get_list('Fleet Vehicle Movement',fields=['vehicle','date_time','movement','odometer'],filters={'vehicle':self.vehicle,'docstatus':1},order_by='date_time')
		if len(movements) !=0:
			last_movement = movements[-1]
			if self.movement == 'OUT' and last_movement['movement'] == 'OUT':
				frappe.throw("Vehicle is already OUT.")
			elif self.movement == 'IN' and last_movement['movement'] == 'IN':
				frappe.throw("Vehicle is already IN.")
			#Odometer Reading Validate
			if self.odometer < last_movement['odometer']:
				frappe.throw("Odometer Reading can't be less than Last Reading: %s"%last_movement['odometer'])
		else:
			vehicle = frappe.get_doc('Fleet Vehicle', self.vehicle)
			if self.odometer < vehicle.last_odometer:
				frappe.throw("Odometer Reading can't be less than Initital Reading of Vehicle: %s"%vehicle.last_odometer)
			if self.movement == 'IN':
				frappe.throw("Vehicle is already IN.")
		return
	def validate_movement_for_cancellation(self):
		movements = frappe.db.get_list('Fleet Vehicle Movement',
			fields=['name','vehicle','date_time','movement','odometer'],
			filters={'vehicle':self.vehicle,'docstatus':1,'date_time':['>',self.date_time]},
			order_by='date_time')
		if len(movements) != 0:
			error_string = ','.join([m['name'] for m in movements])
			frappe.throw("Please cancel the after entries first : %s"%error_string)
		return