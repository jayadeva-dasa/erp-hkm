from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'heatmap': False,
		'fieldname': 'participant',
		'transactions': [
			{
				'label': _('Ashraya Participation'),
				'items': ['Ashraya Ceremony Participant']
			}
		]
	}
