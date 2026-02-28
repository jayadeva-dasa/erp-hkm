import frappe
import datetime
import operator

@frappe.whitelist()
def get_current_status():
		vehicles = frappe.db.get_list('Fleet Vehicle')
		veh_status = []
		for vehicle in vehicles:
			veh_status.append(last_status(vehicle.name))
		return veh_status

@frappe.whitelist()
def last_status(vehicle):
	status = {
				"vehicle" : vehicle,
				"movement" : "IN",
				"driver" : None,
				"driver_code" :None,
				"devotee" : None,
				"last_movement":None,
				"last_odometer":None
					}
	movements = frappe.db.sql("""
					SELECT *
					FROM `tabFleet Vehicle Movement`
					WHERE docstatus = 1
					AND vehicle = '{}'
					ORDER BY date_time
					DESC LIMIT 1
					""".format(vehicle),as_dict = 1)
	if len(movements) !=0:
		last_movement = movements[0]
		status = {
				"vehicle" : vehicle,
				"movement" : last_movement['movement'],
				"driver" : last_movement['driver_name'],
				"driver_code" : last_movement['driver'],
				"devotee" : last_movement['devotee'],
				"date_time":last_movement['date_time'].strftime("%d-%m-%y %I:%M %p"),
				"last_odometer":last_movement['odometer'],
					}
	return status