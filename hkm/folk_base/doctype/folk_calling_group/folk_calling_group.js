// Copyright (c) 2021, NRHD and contributors
// For license information, please see license.txt

frappe.ui.form.on('FOLK Calling Group', {
	refresh: function(frm) {
      frm.add_custom_button(__('Clear All Members'), function(){
      	frappe.warn('Are you sure you want to remove the assignment of this calling group?',
		    'It can\'t be undone',
		    () => {
		        frappe.call({
					    method: 'folk.folk.doctype.folk_calling_group.folk_calling_group.clear_all_members',
					    args: {
					        group: frm.doc.name
					    },
					    // disable the button until the request is completed
					    // btn: $('.primary-action'),
					    // freeze the screen until the request is completed
					    freeze: true,
					    callback: (r) => {
					        frappe.msgprint("Done");
					        frm.refresh();
					    },
					    error: (r) => {
					        frappe.msgprint(r);
					    }
					});
		    },
		    'Continue',
		    true // Sets dialog as minimizable
		);
      	
    }); //__("Utilities"))
   } 
});
