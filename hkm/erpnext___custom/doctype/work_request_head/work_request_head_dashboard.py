from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'heatmap': False,
		'fieldname': 'work_head',
		'transactions': [
			{
				'label': _('Work Request'),
				'items': ['Material Request']
			}
		]
	}
