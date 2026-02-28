// Copyright (c) 2021, NRHD and contributors
// For license information, please see license.txt

frappe.ui.form.on('FOLK Residency Rent', {
	// refresh: function(frm) {

	// }
	refresh: function(frm) {
		frm.fields_dict['folk_student'].get_query = function(doc) {
			return {
				filters: {
					"folk_resident": true
				}
			}
		}
	},
	onload : function(frm){
		var years =[]
		var cur_year = parseInt(moment().format('YYYY'));
		var i,j;
		for(j=0,i=-1;i<5;i++,j++){
			years[j] = cur_year+i;
		}
		frm.set_df_property('year', 'options', years);
		frm.set_df_property('year', 'default', cur_year);
		frm.refresh_field('year');
		var cur_mon = moment().format('MMMM');
		frm.set_df_property('month', 'default', cur_mon);
		frm.refresh_field('month');
	}
});
