# Copyright (c) 2021, NRHD and contributors
# For license information, please see license.txt

import frappe
# from folk.ashraya.doctype.ashraya_candidate.ashraya_candidate import update_latest_level
from frappe.model.document import Document

class AshrayaCeremonyParticipant(Document):
	def on_change(self):
		update_latest_level(self.participant)
	def after_delete(self):
		update_latest_level(self.participant)
		
def update_latest_level(candidate_id):
		latest_ashraya = frappe.db.sql("""
							SELECT acp.level
							FROM `tabAshraya Candidate` as ac
							JOIN
							(
								SELECT `tabAshraya Ceremony Participant`.participant ,`tabAshraya Ceremony`.date, `tabAshraya Ceremony Participant`.level, `tabAshraya Level`.level_index
								FROM `tabAshraya Ceremony Participant`
								JOIN `tabAshraya Level`
								ON `tabAshraya Ceremony Participant`.level = `tabAshraya Level`.name
								JOIN `tabAshraya Ceremony`
								ON `tabAshraya Ceremony Participant`.ashraya_ceremony = `tabAshraya Ceremony`.name
							) as acp
							ON acp.participant = ac.name
							WHERE ac.name = '{}'
							ORDER BY level_index DESC
							LIMIT 1
							""".format(candidate_id))
		if len(latest_ashraya) > 0 and len(latest_ashraya[0]) > 0:
			frappe.db.sql("""
				UPDATE `tabAshraya Candidate`
				SET latest_level_of_ashraya = '{}'
				WHERE `tabAshraya Candidate`.name = '{}'
				""".format(latest_ashraya[0][0],candidate_id))
			frappe.db.commit()  # v16: REVIEW - check if needed