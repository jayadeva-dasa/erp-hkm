// Copyright (c) 2021, NRHD and contributors
// For license information, please see license.txt

frappe.ui.form.on('Ashram Store Item Issue', {
	issued_to:function(frm) {
	    frappe.call({
         'method': 'hkm.ashram_issue_counter.previous_issue.query',
         'args': {
           'store_user': frm.doc.issued_to
         },
         'callback': function(res){
            console.log(res);
            var template = frm.events.update_issue_table(res.message);
            frm.set_df_property('last_issue_details', 'options', template);
            frm.refresh_field('last_issue_details');
         }
       })
	},
	update_issue_table(data){
	    var template = "<h5>Items issued in last 2 months</h5><table class=\"table table-bordered table-sm\"><tbody><tr><th>#</th><th>Item</th><th>Quantity</th></tr>";
	    for(var row in data){
	        template += '<tr><td>'+(parseInt(row)+1)+'</td><td>'+data[row][0]+'</td><td>'+data[row][1]+'</td></tr>';
	    }
	    template += "</tbody></table>";
	    return template
	}
})