# Copyright (c) 2022, Narahari Dasa and contributors
# For license information, please see license.txt

import frappe
from erpnext.accounts.utils import get_balance_on
vec = []
depth = 1
max_depth = 0
def execute(filters=None):
	columns, data = [], []

	# # accounts = frappe.db.get_all("Account", fields=['name','is_group','parent_account'],filters = {'company': filters.get("company")})

	accounts = frappe.db.sql("""
					select name,is_group,parent_account
					from `tabAccount`
					where company = '{}'
				""".format(filters.get("company")),as_dict=1)

	final_data = []
	def generate_accounts(root):
		if root is None:
			return
		
		global vec
		global depth
		global max_depth
		vec.append(root)
		depth = depth+1

		c_accounts = [ a['name'] for a in accounts if a['parent_account'] == root]
		if len(c_accounts) == 0:
			fill_data(vec)
			vec.pop()
			depth = depth-1
			if depth > max_depth:
				max_depth = depth+1
			return
		else:
			for index, account in enumerate(c_accounts):
				generate_accounts(account)
		vec.pop()
		depth = depth-1
	root_accounts = []
	for account in accounts:
		if account['parent_account'] is None:
			root_accounts.append(account['name'])
	
	def fill_data(vec):
		row = []
		for ele in vec:
			row.append(ele)
		balance = get_balance_on(account=vec[-1], date=frappe.utils.nowdate(),company=filters.get("company"))
		balance_format = "{} Cr".format(balance) if balance<0  else "{} Dr".format(balance)
		row.append(balance_format)
		final_data.append(row)


	for r_account in root_accounts:
		generate_accounts(r_account)
	# # return final_data
	i=0
	while i<=max_depth:
		columns.append(
			{
            "fieldname": "D{}".format(i),
            "label":"D{}".format(i),
            "fieldtype": "Link",
			"options": "Account",
			"width": 100
            }
		)			
		i = i+1
	for d in final_data:
		extra = [""] * (max_depth-len(d)+1)
		d.extend(extra)
	return columns, final_data


