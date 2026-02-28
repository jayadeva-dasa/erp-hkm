


import frappe

@frappe.whitelist()
def leave_balance(employee_id):
    doc = frappe.get_all(
        "HKM Leaves",
        filters = {
            "employee": employee_id
        },
        pluck = "name"
        
    )
    
    # if not doc:
    #     frappe.throw("No Leave Balance Found")    
    if len(doc) > 1:
        frappe.throw("Multiple Leave Balance Found")
    if not doc:
        return
    leave_balance = frappe.get_doc("HKM Leaves", doc[0])
    operations_doc = frappe.get_single("HKM HR Settings")
    return {
        "month" :operations_doc.month,
        "el_opening_balance": leave_balance.el_opening_balance,
        "cl_opening_balance": leave_balance.cl_opening_balance,
        "coff_opening_balance": leave_balance.coff_opening_balance
    }
    