# Copyright (c) 2021, NRHD and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime



class FleetVehicleRefuel(Document):
	def before_save(self):
		self.total_amount = self.quantity*self.fuel_rate
	def validate(self):
		self.validate_filling()
	def before_cancel(self):
		self.validate_filling_for_cancellation()
	def validate_filling(self):
		filling = frappe.db.get_list('Fleet Vehicle Refuel',
			fields=['vehicle','date_time','odometer'],
			filters={'vehicle':self.vehicle,'docstatus':1},
			order_by='date_time')
		if len(filling)!= 0:
			last_filling = filling[-1]
			if self.odometer < last_filling['odometer']:
				frappe.throw("Odometer Reading can't be less than Last Reading: %s"%last_filling['odometer'])
			date_time_obj = datetime.strptime(self.date_time, '%Y-%m-%d %H:%M:%S')
			if date_time_obj < last_filling['date_time']:
				frappe.throw("Date Time can't be less than Last Date Time: %s"%last_filling['date_time'])
		return
	def validate_filling_for_cancellation(self):
		filling = frappe.db.get_list('Fleet Vehicle Refuel',
			fields=['name','vehicle','date_time','odometer'],
			filters={'vehicle':self.vehicle,'docstatus':1,'date_time':['>',self.date_time]},
			order_by='date_time')
		if len(filling) != 0:
			error_string = ','.join([f['name'] for f in filling])
			frappe.throw("Please cancel the after entries first : %s"%error_string)
		return