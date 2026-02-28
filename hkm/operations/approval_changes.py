import frappe

# additional_dept_map = {
# 	"Devotee Pilgrimage":"Ashram",
# 	"VEHICLE":"Vehicle",
# 	"Flower decoration":"Pujari",
# 	"Food":"Ashram",
# 	"FOLK Yatra":"FOLK",
# 	"Kota - Books":"BBT",
# 	"Shree Annapurna Rasoi - JPR":"Shree Annapurna Rasoi",
# 	"LLP":"DCC",
# 	"Folk Hostel":"FOLK"
# }

# JAIPUR_COMPANIES = ["Hare Krishna Movement Jaipur","Sri Radha Krishna Mandir Foundation","Touchstone Foundation Jaipur"]


def get_department_map():
    dept_map = {}
    exc_dpts = frappe.get_all("Execution Department", pluck="name")
    for d in list(
        set(
            frappe.get_all(
                "Purchase Invoice",
                filters={
                    # "company":["in", JAIPUR_COMPANIES],
                    "execution_department": ["is", "not set"],
                    "department": ["is", "set"],
                },
                pluck="department",
            )
        )
    ):
        print(d)
        clean_d = d.rsplit("-", 1)[0].strip()
        found_exc_dept = None
        if clean_d in exc_dpts:
            found_exc_dept = clean_d

        if not found_exc_dept:
            for exc_dpt in exc_dpts:
                if clean_d in exc_dpt:
                    found_exc_dept = exc_dpt
                    break
        # if not found_exc_dept:
        # 	if clean_d in additional_dept_map:
        # 		found_exc_dept = additional_dept_map[clean_d]
        # else:
        # 	frappe.throw("Department {} not found in Execution Department".format(d))
        dept_map[d] = found_exc_dept
    return dept_map


def set_departments():
    dept_map = get_department_map()
    purchase_invoices = frappe.get_all(
        "Purchase Invoice",
        filters={
            # "company":["in", JAIPUR_COMPANIES],
            "execution_department": ["is", "not set"],
            "department": ["is", "set"],
        },
        fields=["name", "department"],
    )
    length = len(purchase_invoices)
    for i, pi in enumerate(purchase_invoices):
        print(f"Processing {i+1}/{length} : {pi.name}")
        try:
            frappe.db.set_value(
                "Purchase Invoice",
                pi.name,
                "execution_department",
                dept_map[pi.department],
                update_modified=False,
            )
        except Exception as e:
            print(e)
    frappe.db.commit()  # v16: OK - operations script
