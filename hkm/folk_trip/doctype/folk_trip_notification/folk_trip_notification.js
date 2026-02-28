// Copyright (c) 2022, Narahari Dasa and contributors
// For license information, please see license.txt

frappe.ui.form.on('FOLK Trip Notification', {
	refresh: function(frm) {
		frm.add_custom_button(__("Send SMS"), function(){
			frappe.call({
		        method: 'folk_trip.doctype.folk_trip_notification.notification.send_train_seat_sms',
		        args: {
		            'train': frm.doc.train
		        },
		        callback: function(r) {
		            console.log(r);
		            // if (!r.exc) {
		            //     // code snippet
		            // }
		        }
		    });
		});
	},
	trip: function (frm) {
        frm.set_query('train', () => {
            return {
                filters: {
                    trip: frm.doc.trip
                }
            };
        });

    }
});
