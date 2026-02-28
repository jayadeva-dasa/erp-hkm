from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'heatmap': True,
		'fieldname': 'supplier_creation_request',
		'transactions': [
			{
				'label': _('Supplier'),
				'items': ['Supplier']
			}
		]
	}

