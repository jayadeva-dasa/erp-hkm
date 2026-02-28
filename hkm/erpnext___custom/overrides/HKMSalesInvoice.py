from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice


class HKMSalesInvoice(SalesInvoice):
	"""
	HKM Sales Invoice override - adds methods needed for print formats
	"""
	
	@frappe.whitelist()
	def get_gst_breakup(self):
		"""
		Get GST breakup for print format (same as HKMPOSInvoice)
		Returns: (rows, total_tax, cashier)
		"""
		rows = []
		total_tax = 0
		
		for item in self.items:
			qty = item.qty
			rate = item.rate
			GSTp = 0
			
			tax_templates = frappe.db.sql(
				"""
				select item.gst_hsn_code, tax_template.name as template, tax_template.cumulative_tax as rate
				from `tabItem` item
				join `tabItem Tax` item_tax
					on item_tax.parent = item.name
				join `tabItem Tax Template` tax_template
					on tax_template.name = item_tax.item_tax_template
				where tax_template.company = %s and item.name = %s
				""",
				(self.company, item.item_code),
				as_dict=1,
			)
			
			if len(tax_templates) > 0:
				tax_template = tax_templates[0]
				GSTp = tax_template["rate"]
				row_index = self.search_rows(rows, tax_template["gst_hsn_code"], GSTp)
				
				if row_index is None:
					temp_data = {
						"HSN": tax_template["gst_hsn_code"],
						"GSTp": GSTp,
						"Taxable": qty * rate,
						"CGSTI": qty * rate * GSTp / 200,
						"SGSTI": qty * rate * GSTp / 200,
					}
					rows.append(temp_data)
				else:
					rows[row_index]["Taxable"] += qty * rate
					rows[row_index]["CGSTI"] = (
						rows[row_index]["CGSTI"] + qty * rate * GSTp / 200
					)
					rows[row_index]["SGSTI"] = (
						rows[row_index]["SGSTI"] + qty * rate * GSTp / 200
					)
		
		for row in rows:
			row["Taxable"] = round(row["Taxable"], 2)
			row["CGSTI"] = round(row["CGSTI"], 2)
			row["SGSTI"] = round(row["SGSTI"], 2)
			total_tax += row["CGSTI"] + row["SGSTI"]
		
		total_tax = round(total_tax, 2)
		cashier = frappe.db.get_value("User", self.owner, "full_name")
		
		return rows, total_tax, cashier
	
	@frappe.whitelist()
	def get_company_address(self):
		"""
		Get formatted company address for print format
		"""
		adds = frappe.db.sql(
			"""
			select address.*
			from `tabAddress` address
			join `tabDynamic Link` link on link.parent = address.name
			where link.link_name = %s and link.link_doctype = 'Company'
			""",
			(self.company,),
			as_dict=1,
		)
		
		if not adds:
			return ""
		
		address = adds[0]
		formatted_address = (
			"%(address_line1)s, %(address_line2)s, %(city)s, %(state)s - %(pincode)s"
			% address
		)
		
		return formatted_address
	
	def search_rows(self, rows, HSN, GSTp):
		"""
		Helper method to search for existing row in GST breakup
		"""
		for idx, r in enumerate(rows):
			if r["HSN"] == HSN and r["GSTp"] == GSTp:
				return idx
		return None
