from .api import send_notification
import frappe
from frappe.utils import today

@frappe.whitelist()
def send_birthday_reminders():

	students = frappe.db.sql("""
			SELECT `name`,`student_email_id`, `student_mobile_number`, `folk_guide`, `full_name`
			FROM `tabFOLK Student`
			WHERE
				DAY(date_of_birth) = DAY(%(today)s)
			AND
				MONTH(date_of_birth) = MONTH(%(today)s)
			AND
				`enabled` = 1
		""",dict(today=today()), as_dict=1)
	for student in students:
		guide = frappe.db.get_value('FOLK Guide',student.folk_guide,'erp_user')
		data ={
			'route' : '/studentProfile',
			'scode' : student.name
		}
		results = send_notification(guide,'Birthday Reminder','Today is the birthday of {}'.format(student.full_name),data)


@frappe.whitelist()
def send_marriage_anniversary_reminders():

	students = frappe.db.sql("""
			SELECT `name`,`student_email_id`, `student_mobile_number`, `folk_guide`, `full_name`
			FROM `tabFOLK Student`
			WHERE
				DAY(marriage_anniversary) = DAY(%(today)s)
			AND
				MONTH(marriage_anniversary) = MONTH(%(today)s)
			AND
				`enabled` = 1
		""",dict(today=today()), as_dict=1)
	for student in students:
		guide = frappe.db.get_value('FOLK Guide',student.folk_guide,'erp_user')
		data ={
			'route' : '/studentProfile',
			'scode' : student.name
		}
		results = send_notification(guide,'Marriage Anniversary Reminder','Today is the anniversary of {}'.format(student.full_name),data)