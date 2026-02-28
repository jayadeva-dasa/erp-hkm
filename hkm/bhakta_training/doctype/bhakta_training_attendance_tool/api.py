import frappe,json
from frappe import _

@frappe.whitelist()
def mark_attendance(bkts_present, bkts_absent, session):

	if session is None:
		frappe.throw("Session is Required.")

	present = json.loads(bkts_present)
	absent = json.loads(bkts_absent)

	for d in present:
		make_attendance_records(d['name'], "Present", session)

	for d in absent:
		make_attendance_records(d['name'], "Absent", session)

	frappe.db.commit()  # v16: REVIEW - check if needed
	frappe.msgprint(_("Attendance has been marked successfully."))

def make_attendance_records(bhakta, status, session):
	attendance_record = frappe.db.exists('Bhakta Training Attendance', {
			'bhakta': bhakta,
			'session': session,
			'docstatus': ('!=', 2)
		})
	if not attendance_record:
		attendance = frappe.new_doc("Bhakta Training Attendance")
		attendance.bhakta = bhakta
		attendance.session = session
		attendance.status = status
		attendance.save()
		attendance.submit()
	else:
		frappe.db.set_value("Bhakta Training Attendance",attendance_record, 'status', status)
