from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'heatmap': False,
		'fieldname': 'folk_student',
		'transactions': [
			{
				'label': _('Interaction'),
				'items': ['FOLK Student Interaction']
			},
			{
				'label': _('Residency Rent'),
				'items': ['FOLK Residency Rent','FOLK Residency Rent Return']
			},
			{
				'label': _('Donation'),
				'items': ['FOLK Donation']
			},
		]
	}

