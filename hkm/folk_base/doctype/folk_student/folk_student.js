// Copyright (c) 2021, NRHD and contributors
// For license information, please see license.txt

frappe.ui.form.on('FOLK Student', {
	refresh: function(frm) {
			if(!frappe.user_roles.includes('FOLK Admin'))
				frm.fields_dict['folk_guide'].get_query = function(doc) {
							return {
								filters: {
									"erp_user": frappe.session.user
								}
							}
						}
	},
	validate:function(frm){
		//frm.set_value('title',frm.doc.full_name);
	},
	call:function(frm) {
	        var phoneNumber = frm.doc.student_mobile_number;
	        window.open('tel:'+phoneNumber, '_self');
	},
	call1:function(frm) { 
	        var phoneNumber = frm.doc.student_mobile_number;
	        window.open('tel:'+phoneNumber, '_self');
	}
});