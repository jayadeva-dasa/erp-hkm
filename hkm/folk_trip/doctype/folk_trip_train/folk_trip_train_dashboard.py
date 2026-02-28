from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'heatmap': False,
		'fieldname': 'train',
		'transactions': [
			{
				'label': _('Tickets'),
				'items': ['FOLK Trip Train Ticket']
			}
		]
	}
