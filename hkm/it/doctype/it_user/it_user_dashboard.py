from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'heatmap': False,
		'fieldname': 'it_user',
		'transactions': [
			{
				'label': _('Devices'),
				'items': ['IT Device']
			}
		]
	}
