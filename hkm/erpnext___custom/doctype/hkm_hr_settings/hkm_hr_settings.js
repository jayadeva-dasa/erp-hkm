// Copyright (c) 2025, Narahari Dasa and contributors
// For license information, please see license.txt

frappe.ui.form.on("HKM HR Settings", {
	refresh(frm) {

	},
    process(frm){
        frm.call({
			freeze: true,
            method:"POST",
			freeze_message: "Processing",
			method: 'hkm.erpnext___custom.doctype.hkm_hr_settings.hr_employee_leave_operation.process',
			callback: function (r) {
				if (!r.exc) {
					frappe.msgprint(__('Successfully Done.'));
				} else {
					console.log(r.data);
					frappe.msgprint(__('Failed.'));
				}
			}
		});
    }
});
