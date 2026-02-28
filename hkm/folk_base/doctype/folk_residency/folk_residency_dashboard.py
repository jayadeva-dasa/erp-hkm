from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'heatmap': False,
		'fieldname': 'residency',
		'transactions': [
			{
				'label': _('Students'),
				'items': ['FOLK Student','FOLK Residency Rent','FOLK Residency Rent Return']
			}
		]
	}
