import frappe


def student_query(user):
	if not user:
		user = frappe.session.user
	# students = frappe.get_all ("FOLK Student",fields=["name"])
	# if 'FOLK Plus Guide' in frappe.get_roles('nrhdasa@gmail.com'):
	#guides_allowed = frappe.db.get_list('FOLK Guide', filters={'erp_user':user},pluck='name') #fields=['subject', 'date'],
	user_roles = frappe.get_roles(user)
	if 'FOLK Admin' in user_roles:
		return "( 1 )"
	elif 'FOLK Guide' in user_roles:
		guides_allowed = frappe.db.get_list('FOLK Guide',filters={'erp_user':user},pluck='name')
		filter_strings = []
		if len(guides_allowed) == 0:
			return "( 0 )"
		for guide in guides_allowed:
			filter_strings.append("`tabFOLK Student`.folk_guide = '{}'".format(guide))
		return "("+ (" and ".join(filter_strings)) + ")"
	else:
		return "( 0 )"
