// Copyright (c) 2021, NRHD and contributors
// For license information, please see license.txt

frappe.ui.form.on('FOLK Trip Train Ticket', {
	onload: function(frm,cdt,cdn) {
		frm.set_query("allocated_to", "passengers", function(frm,cdt,cdn) {
		    // return {
		    //     query: "folk.trip.controller.lead_query"
		    //     // filters: frm.doc.enquiry_type === "Maintenance" ?
		    //     //     {"is_service_item": "Yes"} : {"is_sales_item": "Yes"}
		    // };
		    return {
            "filters": {
                // "account_type": "Bank",
	            }
	        };
		});
	}

});
