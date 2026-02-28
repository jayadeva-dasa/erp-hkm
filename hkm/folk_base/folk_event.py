import frappe
from frappe.model.document import Document

@frappe.whitelist(allow_guest=True)
def get_participant_data(qr_code,secret_code):
    if secret_code != "bonfr23":
        return {"error": "Unauthorized access"}
    participant = frappe.get_doc("FOLK Event Participant", {"name": qr_code})
    if not participant:
        return {"error": "Participant not found"}
    return {
        "name": participant.student_name,
        "institute": participant.institute,
        "email": participant.email,
        "mobile": participant.mobile_no,
        "id":participant.name,
        "status":participant.accepted
    }

@frappe.whitelist(allow_guest=True)
def mark_attendance(qr_code,secret_code):
    if secret_code != "bonfr23":
        return {"error": "Unauthorized access"}
    participant = frappe.get_doc("FOLK Event Participant", {"name": qr_code})
    if not participant:
        return {"error": "Participant not found"}
    if participant.accepted == 1:
        return {"error": "Already Used"}
    participant.accepted = 1
    participant.save(
        ignore_permissions=True, # ignore write permissions during insert
    )
    return "Done"