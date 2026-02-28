import frappe

def execute():
    print("Migrating Purchase Order Approval Revamp")
    migrate_approving_authorities_table()
    remove_custom_fields()
    update_status_of_trashed()

def update_status_of_trashed():
	trashed_purchases = frappe.get_all("Purchase Order",filters={"workflow_state":"Trashed"},pluck="name")
	for po in trashed_purchases:
		frappe.db.set_value("Purchase Order", po, "docstatus", 2,update_modified= False)
	frappe.db.commit()  # v16: OK - patch script


def migrate_approving_authorities_table():
	purchase_orders = frappe.frappe.db.get_all('Purchase Order', filters={"docstatus":1,"locked":0,"workflow_state":"Final Level Approved"},fields=["name","recommended_by","first_approving_authority","final_approving_authority"])
	length = len(purchase_orders)
	for i,po in enumerate(purchase_orders):
		print(f"Processing {i+1}/{length} : {po.name}")
		approving_authorities = []
		if po.recommended_by:
			approving_authorities.append(po.recommended_by)
		if po.first_approving_authority:
			approving_authorities.append(po.first_approving_authority)
		if po.final_approving_authority:
			approving_authorities.append(po.final_approving_authority)
		approving_authorities = list(set(approving_authorities))
		
		approval_count = len(approving_authorities)
		approval_count_str = f"{approval_count}/{approval_count} Approved"
		versions = frappe.get_all("Version", filters={"ref_doctype":"Purchase Order","docname":po.name,"data":["LIKE",'%"workflow_state","Prepared","Checked"%']},pluck="modified_by")
		approval_initiator = "Administrator"
		if versions:
			approval_initiator = versions[0]
		
		for authority in approving_authorities:
			frappe.get_doc({
				'doctype': 'Approval Matrix Authority',
				'authority': authority,
				'status':'Approved',
				'parent': po.name,
				'parenttype': 'Purchase Order',
				'parentfield': 'approving_authorities'
			}).insert(ignore_links= True)
		
		frappe.db.set_value('Purchase Order', po.name, {
			'locked': 1,
			'approval_initiator': approval_initiator,
			'approval_status': approval_count_str
		})
		frappe.db.commit()  # v16: OK - patch script

		
def	remove_custom_fields():
	frappe.delete_doc('Custom Field','Purchase Order-alm')
	frappe.delete_doc('Custom Field','Purchase Order-alm_column_break')
	frappe.delete_doc('Custom Field','Purchase Order-recommended_by')
	frappe.delete_doc('Custom Field','Purchase Order-first_approving_authority')
	frappe.delete_doc('Custom Field','Purchase Order-final_approving_authority')
	frappe.delete_doc('Custom Field','Purchase Order-department')
	frappe.delete_doc('Custom Field','Purchase Receipt-department')
	frappe.delete_doc('Custom Field','Purchase Invoice-department')
	frappe.delete_doc('Custom Field','Material Request-department')
	frappe.db.commit()  # v16: OK - patch script