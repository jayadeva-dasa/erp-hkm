# Copyright (c) 2021, NRHD and contributors
# For license information, please see license.txt

import frappe,requests,urllib.parse

@frappe.whitelist()
def send_train_seat_sms(train):
	yatris = frappe.db.sql("""
		select fty.name,fty.full_name,fty.mobile_no
		from `tabFOLK Trip Yatri` fty
		join `tabFOLK Trip Train Passenger` fttp on (fttp.allocated_to = fty.name)
		join `tabFOLK Trip Train Ticket` fttt on (fttt.name = fttp.parent)
		where fttt.train = '{}' 
		""".format(train),as_dict = 1)
	return send_single_sms('7357010770',urllib.parse.quote_plus('Hare Krishna Dear Naresh, For: Naresh Seat Name : S4 Seat No. : 2131'))
	# for yatri in yatris:

	# self.total = len(data)
	return

def send_single_sms(mobile,message):
	url = "http://alertbox.in/pushsms.php?username=7357010770&api_password=45c48twjbdqjzbnrr&sender=HKMJPR&to={}&message={}&priority=11&e_id=1701163057877862982&t_id=1707163997528750827".format(mobile,message)
	response = requests.get(url)
	return response.text
