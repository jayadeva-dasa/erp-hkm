import frappe,json
import requests
from random import randint, randrange

@frappe.whitelist()
def get_student_list(filters):
	filters = json.loads(filters)
	filter_string = ""
	if "types" in filters:
		strings = []
		for f in filters["types"]:
			strings.append(f+"=1")
		if len(strings)>0:
			filter_string+= " AND "+(" OR ".join(strings))
	
	if ("city" in filters) and filters["city"].strip() != "":
		city = filters["city"]
		filter_string+= " AND ( city LIKE '%{0}%' OR c_city LIKE '%{1}%')".format(city,city)

	if "plus_levels" in filters:
		strings = []
		for l in filters["plus_levels"]:
			strings.append(" plus_level  = {0}".format(l))
		if len(strings)>0:
			filter_string+= " AND "+(" OR ".join(strings))

	filter_string+= " AND (std.full_name LIKE '%{0}%' OR std.name LIKE '%{1}%')".format(filters["search"],filters["search"])

	guide = frappe.session.user
	filter_string

	if "group_name" in filters:
		filter_string+= " AND (calling_group='{}')".format(filters['group_name'])

	data = frappe.db.sql("""
		SELECT std.*,
		(SELECT COUNT(*) FROM `tabFOLK Student Interaction` WHERE `folk_student` = std.name) as inter_count
		FROM
			`tabFOLK Student` as std
		JOIN
			`tabFOLK Guide` as guide ON guide.name = std.folk_guide
		WHERE
			guide.erp_user = '{0}' AND
			enabled = 1 {1}
		ORDER BY
			std.full_name
		LIMIT {2},30
		""".format(guide,filter_string,filters['max_page']*30),as_dict=1)

	
	return data
	#file_url = frappe.db.get_value('File', {'attached_to_name': sname}, ['file_url'])
	#return file_url

@frappe.whitelist()
def get_profile_image_link(sname):
	student = frappe.get_doc("FOLK Student",sname)
	file_url = frappe.db.get_value('File', {'attached_to_name': sname}, ['file_url'])
	return file_url

@frappe.whitelist()
def get_full_name():
	sname = frappe.session.user
	full_name = frappe.db.get_value('User',sname,'full_name')
	return full_name

@frappe.whitelist()
def get_dashboard_data():
	data = (frappe.db.count('FOLK Student', {'folk_resident': 1}),frappe.db.count('FOLK Student', {'folk_plus': 1}),frappe.db.count('FOLK Guide'),frappe.db.count('FOLK Residency'),frappe.db.count('FOLK Student Interaction',{'owner':frappe.session.user}))

	return data

@frappe.whitelist()
def send_message():
	results = send_notification("nrhdasa@gmail.com","Hare Krishna","How are you?")
	return results

def send_notification(user,title,content,data=None):
	url = "https://fcm.googleapis.com/fcm/send"
	auth_key = "AAAAgxuverI:APA91bF1Lz2JC8s6DfPEbdsh9QynwzZU0w6U5JvAtPjCn4xzvHvlqLxzZq5mlsWm9NwoffaK5KYDZt-iZaww38DWaSxpSHIfQ9zRWtdVl_V8S3n9SZnMvcvAySo1-PDgSAar816W19Av"
	headers = {
		"Content-Type":"application/json",
		"Authorization":"key={}".format(auth_key),
	}
	tokens = frappe.db.get_list('FOLK App FCM Token', pluck='token',filters={'user': user},)
	results =[]
	for token in tokens:
		data = {
				  "to": token,
				  "collapse_key": "type_a",
				  "notification": {
					"title": title,
					"body": content
				  },
				  "data":data
				}
		result = requests.post(url, data=json.dumps(data), headers= headers)
		results.append(result.text)
	return results

@frappe.whitelist(allow_guest=True)
def setOTP():
	data = json.loads(frappe.request.data)

	docs = frappe.db.get_all('FOLK Student',filters={'student_mobile_number': ['=', data['mobile']],},fields=['name','full_name'])
	if len(docs) != 1:
		frappe.response["error"] = True
		frappe.response["message"] = "This mobile number is not registered. Please contact FOLK Guide."
	else:
		otp = randrange(100000, 1000000)
		frappe.response["error"] = False
		URL = "http://alertbox.in/pushsms.php"
		PARAMS = {
			'username':'7357010770',
			'api_password':'45c48twjbdqjzbnrr',
			'sender':'HKMJPR',
			'to':data['mobile'],
			'priority':11,
			'e_id':'1701163057877862982',
			't_id':'1707163300407693133',
			'message':'Hare Krishna Dear {}, Your Ashraya Code is {} Please tell it when asked for at entry gate.'.format(docs[0]['full_name'],otp)
		}
		student_doc = frappe.get_doc('FOLK Student',docs[0]['name'])
		student_doc.otp = otp
		student_doc.save(ignore_permissions=True)
		r = requests.get(url = URL, params = PARAMS)
		return


