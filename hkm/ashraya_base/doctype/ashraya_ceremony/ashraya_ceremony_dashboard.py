from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'heatmap': False,
		'fieldname': 'ashraya_ceremony',
		'transactions': [
			{
				'label': _('Participants'),
				'items': ['Ashraya Ceremony Participant']
			}
		]
	}
