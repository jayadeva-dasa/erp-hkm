from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'heatmap': False,
		'fieldname': 'guide',
		'transactions': [
			{
				'label': _('Candidates'),
				'items': ['Ashraya Candidate']
			}
		]
	}
