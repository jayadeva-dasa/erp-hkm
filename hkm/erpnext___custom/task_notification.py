import frappe
from datetime import date
from frappe.utils.background_jobs import enqueue
from frappe.workflow.doctype.workflow_action.workflow_action import get_doc_workflow_state

def query(self,method):
	if self.workflow_state == 'Completed':
		coordinators = {
		"IT": "vicky.sharma@hkm-group.org",
		"Maintenance": "mukesh.chhaparwal@hkm-group.org"
		}
		message = """
				<h3>Hare Krishna,</h3>
				<p>Your assigned task to {} is completed. Please check it on ERP and confirm if you are satisfied with work done.</p>
				<h3><span style="color: #000080;">Task Details:</span></h3>
				Task Created on : {}
				Task Description : {}
				""".format(self.to_department,self.creation,self.description)
		subject = "✅ Completeted ✅" + ((self.subject[:50] + '...') if len(self.subject) > 75 else self.subject)
		email_args = {
			"recipients": [self.owner],
			"message": message,
			"subject": subject,
			"reference_doctype": self.doctype,
			"reference_name": self.name,
			"reply_to": coordinators[self.to_department],
			"delayed":False,
			"sender":coordinators[self.to_department]
			}
		enqueue(method=frappe.sendmail, queue='short', timeout=300, is_async=True, **email_args)