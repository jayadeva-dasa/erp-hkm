from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'heatmap': False,
		'fieldname': 'folk_guide',
		'transactions': [
			{
				'label': _('Students'),
				'items': ['FOLK Student']
			},
			{
				'label': _('Residency'),
				'items': ['FOLK Residency']
			},
		]
	}
