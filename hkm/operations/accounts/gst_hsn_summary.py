import frappe
from frappe import _
import re


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"fieldname": "gst_hsn_code",
			"label": _("HSN Code"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "uom",
			"label": _("UOM"),
			"fieldtype": "Link",
			"options": "UOM",
			"width": 80
		},
		{
			"fieldname": "quantity",
			"label": _("Quantity"),
			"fieldtype": "Float",
			"width": 100
		},
		{
			"fieldname": "taxable_amount",
			"label": _("Taxable Amount"),
			"fieldtype": "Currency",
			"width": 130
		},
		{
			"fieldname": "item_tax_template",
			"label": _("Item Tax Template"),
			"fieldtype": "Link",
			"options": "Item Tax Template",
			"width": 200
		},
		{
			"fieldname": "cgst",
			"label": _("CGST"),
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"fieldname": "sgst",
			"label": _("SGST"),
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"fieldname": "igst",
			"label": _("IGST"),
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"fieldname": "total_amount",
			"label": _("Total Amount"),
			"fieldtype": "Currency",
			"width": 130
		}
	]


def get_data(filters):
	conditions = get_conditions(filters)
	
	# Query to fetch sales invoice items
	query = """
		SELECT 
			sii.gst_hsn_code,
			sii.uom,
			SUM(sii.qty) as quantity,
			SUM(sii.rate * sii.qty) as taxable_amount,
			sii.item_tax_template,
			si.taxes_and_charges
		FROM 
			`tabSales Invoice Item` sii
		INNER JOIN 
			`tabSales Invoice` si ON sii.parent = si.name
		WHERE 
			si.docstatus = 1
			AND si.customer != 'Online Ecom (Swiggy/Zomato)'
			AND si.company = 'Touchstone Foundation Jaipur'
			AND si.posting_date BETWEEN '2024-04-01' AND '2025-03-31'
			{conditions}
		GROUP BY 
			sii.gst_hsn_code, 
			sii.uom, 
			sii.item_tax_template,
			si.taxes_and_charges
		ORDER BY 
			sii.gst_hsn_code
	""".format(conditions=conditions)
	
	result = frappe.db.sql(query, as_dict=1)
	
	# Process the data to calculate CGST, SGST, IGST
	data = []
	for row in result:
		taxable_amount = row.get("taxable_amount", 0)
		
		# Extract tax percentage from item_tax_template
		tax_rate = extract_tax_percentage(row.get("item_tax_template", ""))
		
		# Calculate tax amounts based on in-state or out-of-state
		cgst = 0
		sgst = 0
		igst = 0
		
		if tax_rate > 0:
			total_tax = taxable_amount * (tax_rate / 100)
			
			# Check if it's in-state or out-of-state GST
			if row.get("taxes_and_charges") == "Output In State GST":
				# Split equally between CGST and SGST
				cgst = total_tax / 2
				sgst = total_tax / 2
			else:
				# Out of state - all goes to IGST
				igst = total_tax
		
		# Calculate total amount
		total_amount = taxable_amount + cgst + sgst + igst
		
		data.append({
			"gst_hsn_code": row.get("gst_hsn_code"),
			"uom": row.get("uom"),
			"quantity": row.get("quantity"),
			"taxable_amount": taxable_amount,
			"item_tax_template": row.get("item_tax_template"),
			"cgst": cgst,
			"sgst": sgst,
			"igst": igst,
			"total_amount": total_amount
		})
	
	return data


def get_conditions(filters):
	conditions = ""
	
	if filters:
		if filters.get("from_date"):
			conditions += " AND si.posting_date >= %(from_date)s"
		if filters.get("to_date"):
			conditions += " AND si.posting_date <= %(to_date)s"
		if filters.get("company"):
			conditions += " AND si.company = %(company)s"
		if filters.get("customer"):
			conditions += " AND si.customer = %(customer)s"
	
	return conditions


def extract_tax_percentage(tax_template):
	"""
	Extract tax percentage from item tax template string.
	Example: "GST - 5% - TSFJ" returns 5.0
	"""
	if not tax_template:
		return 0
	
	# Search for pattern like "5%" or "12%" etc.
	match = re.search(r'(\d+(?:\.\d+)?)\s*%', tax_template)
	
	if match:
		return float(match.group(1))
	
	return 0

