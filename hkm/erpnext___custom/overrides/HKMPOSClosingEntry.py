from erpnext.accounts.doctype.pos_closing_entry.pos_closing_entry import POSClosingEntry
import frappe
from frappe.utils import escape_html, flt, fmt_money


class HKMPOSClosingEntry(POSClosingEntry):
	def on_submit(self):
		super().on_submit()
		frappe.enqueue(generate_sales_invoices_item_html, doc_name=self.name)


@frappe.whitelist()
def generate_sales_invoices_item_html(doc_name):
	if not frappe.db.exists("POS Closing Entry", doc_name):
		frappe.throw("POS Closing Entry not found")

	doc = frappe.get_doc("POS Closing Entry", doc_name)

	if not doc.sales_invoices:
		doc.sales_invoices_item_html = "<p class='text-muted'>No sales invoices in this closing entry.</p>"
		return

	item_dict = {}
	for sales_inv_ref in doc.sales_invoices:
		sales_invoice_name = sales_inv_ref.sales_invoice
		sales_invoice_items = frappe.get_all(
			"Sales Invoice Item",
			filters={"parent": sales_invoice_name, "parenttype": "Sales Invoice"},
			fields=["item_code", "item_name", "qty", "rate", "amount"],
		)
		for row in sales_invoice_items:
			# Use item_code, fallback to item_name when item_code is empty (e.g. non-stock/description rows)
			item_key = row.get("item_code") or row.get("item_name")
			if not item_key:
				continue
			if item_key not in item_dict:
				item_dict[item_key] = {
					"item_code": row.get("item_code") or item_key,
					"item_name": row.get("item_name") or item_key,
					"quantity": flt(row.get("qty") or 0),
					"rate": flt(row.get("rate") or 0),
					"amount": flt(row.get("amount") or 0),
				}
			else:
				item_dict[item_key]["quantity"] += flt(row.get("qty") or 0)
				item_dict[item_key]["amount"] += flt(row.get("amount") or 0)

	# Build data list with computed average rate
	data = []
	for item_code, item_data in item_dict.items():
		qty = item_data["quantity"]
		amount = item_data["amount"]
		avg_rate = amount / qty if qty else 0
		data.append({
			"item_code": item_data["item_code"],
			"item_name": item_data["item_name"],
			"quantity": qty,
			"rate": avg_rate,
			"amount": amount,
		})

	# Sort by item_code for consistent display
	data.sort(key=lambda x: (x["item_code"] or ""))

	company_currency = frappe.get_cached_value("Company", doc.company, "default_currency") or "INR"
	sales_invoices_item_html = _build_item_html_table(data, company_currency)
	if  not "pos_sales_invoices_item" in doc.as_dict():
		return
	frappe.db.set_value("POS Closing Entry", doc_name, "pos_sales_invoices_item", sales_invoices_item_html)
	frappe.db.commit()

def _build_item_html_table(data, company_currency="INR"):
	"""Build HTML table from aggregated item data."""
	if not data:
		return "<p class='text-muted'>No items found.</p>"

	# Column widths: # and Qty minimal, Item Code moderate, Item Name larger, Rate/Amount a bit larger
	col_styles = [
		"padding: 6px 8px; width: 2.2em; min-width: 2.2em;",  # #
		"padding: 6px 8px; width: 10em; min-width: 10em;",   # Item Code
		"padding: 6px 8px; width: 18em; min-width: 14em;",   # Item Name (larger to reduce wrapping)
		"padding: 6px 8px; text-align: right; width: 4em; min-width: 4em;",   # Qty
		"padding: 6px 8px; text-align: right; width: 7.5em; min-width: 7.5em;", # Rate
		"padding: 6px 8px; text-align: right; width: 7.5em; min-width: 7.5em;", # Amount
	]
	html_parts = [
		'<div class="pos-closing-item-summary">',
		'<table class="table table-bordered table-condensed" style="margin-bottom: 0; table-layout: fixed;">',
		"<thead>",
		"<tr>",
		f'<th style="{col_styles[0]}">#</th>',
		f'<th style="{col_styles[1]}">Item Code</th>',
		f'<th style="{col_styles[2]}">Item Name</th>',
		f'<th style="{col_styles[3]}">Qty</th>',
		f'<th style="{col_styles[4]}">Rate</th>',
		f'<th style="{col_styles[5]}">Amount</th>',
		"</tr>",
		"</thead>",
		"<tbody>",
	]
	for idx, row in enumerate(data, 1):
		qty_fmt = frappe.format_value(row["quantity"], df=dict(fieldtype="Float"))
		rate_fmt = fmt_money(row["rate"], currency=company_currency)
		amount_fmt = fmt_money(row["amount"], currency=company_currency)
		html_parts.extend([
			"<tr>",
			f'<td style="{col_styles[0]}">{idx}</td>',
			f'<td style="{col_styles[1]}">{escape_html(str(row["item_code"] or ""))}</td>',
			f'<td style="{col_styles[2]}">{escape_html(str(row["item_name"] or ""))}</td>',
			f'<td style="{col_styles[3]}">{qty_fmt}</td>',
			f'<td style="{col_styles[4]}">{rate_fmt}</td>',
			f'<td style="{col_styles[5]}">{amount_fmt}</td>',
			"</tr>",
		])
	html_parts.extend(["</tbody>", "</table>", "</div>"])
	return "".join(html_parts)
