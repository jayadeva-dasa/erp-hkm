// Copyright (c) 2023, Narahari Dasa and contributors
// For license information, please see license.txt

frappe.ui.form.on('Suspense Tool', {
	refresh: function(frm) {
		frm.add_custom_button(__("Update Suspense JV"), function(){
			frappe.call({
				freeze:true,
				freeze_message:"Setting",
				method: "hkm.erpnext___custom.doctype.suspense_tool.suspense_tool.update_suspense_clearing_jv",
				callback: function(r) {
					if(!r.exc){
						console.log(r.message);
						frappe.msgprint("Successfully Imported");
					}
				}
			});
		  });
	}
});
