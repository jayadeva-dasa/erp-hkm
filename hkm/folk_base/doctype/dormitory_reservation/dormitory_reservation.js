// Copyright (c) 2022, Narahari Dasa and contributors
// For license information, please see license.txt

frappe.ui.form.on('Dormitory Reservation', {
	setup: function (frm) {
		if (frm.doc.docstatus == 0) {
			if (!frm.doc.reservation_date) {
				frm.set_value('reservation_date', frappe.datetime.nowdate());
			}
			if (!frm.doc.checkin) {
				frm.set_value('checkin', frappe.datetime.now_datetime());
			}
		}
	},
	onload: function (frm) {
		frm.set_query("dormitory_bed", function (doc) {
			let filters = {
				'dormitory': frm.doc.dormitory,
				'checkin': frm.doc.checkin,
				'checkout': frm.doc.expected_checkout,
				'bed_type': frm.doc.bed_type,
			};
			return {
				query: "hkm.folk_base.doctype.dormitory_reservation.dormitory_reservation.dormitory_bed_query",
				filters: filters,
			}
		});
	},
	refresh: function (frm, cdt, cdn) {
		if (frm.doc.docstatus == 1) {
			frm.add_custom_button(__('Checkout'), frm.trigger("set_actual_checkout")).addClass("btn-primary");
		}
	},
	days: function (frm) {
		frm.trigger("set_expected_checkout");
	},
	checkin: function (frm) {
		frm.trigger("set_days");
		frm.trigger("set_expected_checkout");
	},
	expected_checkout: function (frm) {
		frm.trigger("set_days");
	},
	set_days: function (frm) {
		let days = frappe.datetime.get_day_diff(frm.doc.expected_checkout, moment(frm.doc.checkin).format(frappe.defaultDateFormat));
		frm.doc.days = (days > 0 ? days : 0);
		frm.refresh_field("days");
	},
	set_expected_checkout: function (frm) {
		let days = cint(frm.doc.days) || 0;
		let expected_checkout = "";
		if (frm.doc.checkin && days) {
			expected_checkout = frappe.datetime.add_days(frm.doc.checkin, days);
		}
		frm.doc.expected_checkout = expected_checkout;
		frm.refresh_field("expected_checkout");
		//frm.set_value("expected_checkout", frappe.datetime.add_days(frm.doc.checkin, days))
	},
	set_actual_checkout: function (frm) {
		var dialog = new frappe.ui.Dialog({
			title: __("Set Submission Date"),
			fields: [
				{
					"fieldtype": "Date", "label": __("Checkout Date"), "fieldname": "checkout_date",
					"reqd": 1, "default": Date.now()
				},
				{ "fieldtype": "Button", "label": __("Update"), "fieldname": "update" },
			]
		});
		dialog.fields_dict.update.$input.click(function () {
			args = dialog.get_values();
			if (!args) return;
			return frm.call({
				doc: frm.doc,
				method: "hkm.folk_base.doctype.dormitory_reservation.dormitory_reservation.update_checkout_date",
				args: { "docname": frm.doc.name, "checkout_date": args.checkout_date },
				callback: function (r) {
					if (r.exc) {
						msgprint(__("There were errors."));
					} else {
						dialog.hide();
						cur_frm.refresh();
					}
				},
				btn: this
			})
		});
		dialog.show();
	},
});
