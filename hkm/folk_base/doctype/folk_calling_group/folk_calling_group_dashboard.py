from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'heatmap': False,
		'fieldname': 'calling_group',
		'transactions': [
			{
				'label': _('Students Assigned'),
				'items': ['FOLK Student']
			}
		]
	}
