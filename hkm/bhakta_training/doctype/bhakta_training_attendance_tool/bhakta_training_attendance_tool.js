// Copyright (c) 2022, Narahari Dasa and contributors
// For license information, please see license.txt

frappe.provide("bhakta");


frappe.ui.form.on('Bhakta Training Attendance Tool', {
	setup: (frm) => {
		frm.bhaktas_area = $('<div>')
			.appendTo(frm.fields_dict.bhaktas_html.wrapper);
	},
	onload:function(frm) {
		frm.set_query("session", function() {
			return {
				"filters": {
					"semester": frm.doc.semester
				}
			};
		});
	},
	refresh: function(frm) {
		if (frappe.route_options) {
			// frm.set_value("based_on", frappe.route_options.based_on);
			// frm.set_value("student_group", frappe.route_options.student_group);
			// frm.set_value("course_schedule", frappe.route_options.course_schedule);
			frappe.route_options = null;
		}
		frm.disable_save();
	},
	session:function(frm){
		frm.bhaktas_area.find('.bhakta-attendance-checks').html(`<div style='padding: 2rem 0'>Fetching...</div>`);
		var method = "hkm.bhakta_training.doctype.bhakta_training_attendance_tool.bhakta_training_attendance_tool.get_bhaktas_records"
		frappe.call({
				method: method,
				args: {
					session: frm.doc.session,
				},
				callback: function(r) {
					frm.events.get_bhaktas(frm, r.message);
					console.log(r.message);
				}
			})
	},
	get_bhaktas: function(frm, bhaktas) {
		bhaktas = bhaktas || [];
		frm.bhaktas_editor = new bhakta.BhaktasEditor(frm, frm.bhaktas_area, bhaktas);
	}
});

bhakta.BhaktasEditor = class BhaktasEditor {
	constructor(frm, wrapper, bhaktas) {
		this.wrapper = wrapper;
		this.frm = frm;
		if(bhaktas.length > 0) {
			this.make(frm, bhaktas);
		} else {
			this.show_empty_state();
		}
	}
	make(frm, bhaktas) {
		var me = this;

		$(this.wrapper).empty();
		var bhaktas_toolbar = $('<p>\
			<button class="btn btn-default btn-add btn-xs" style="margin-right: 5px;"></button>\
			<button class="btn btn-xs btn-default btn-remove" style="margin-right: 5px;"></button>\
			<button class="btn btn-default btn-primary btn-mark-att btn-xs"></button></p>').appendTo($(this.wrapper));

		bhaktas_toolbar.find(".btn-add")
			.html(__('Check all'))
			.on("click", function() {
				$(me.wrapper).find('input[type="checkbox"]').each(function(i, check) {
					if (!$(check).prop("disabled")) {
						check.checked = true;
					}
				});
			});

		bhaktas_toolbar.find(".btn-remove")
			.html(__('Uncheck all'))
			.on("click", function() {
				$(me.wrapper).find('input[type="checkbox"]').each(function(i, check) {
					if (!$(check).prop("disabled")) {
						check.checked = false;
					}
				});
			});

		bhaktas_toolbar.find(".btn-mark-att")
			.html(__('Mark Attendance'))
			.on("click", function() {
				$(me.wrapper.find(".btn-mark-att")).attr("disabled", true);
				var bkts = [];
				$(me.wrapper.find('input[type="checkbox"]')).each(function(i, check) {
					var $check = $(check);
					bkts.push({
						name: $check.data().name,
						disabled: $check.prop("disabled"),
						checked: $check.is(":checked")
					});
				});
				var bkts_present = bkts.filter(function(bkt) {
					return !bkt.disabled && bkt.checked;
				});

				var bkts_absent = bkts.filter(function(bkt) {
					return !bkt.disabled && !bkt.checked;
				});

				frappe.confirm(__("Do you want to update attendance? <br> Present: {0} <br> Absent: {1}",
					[bkts_present.length, bkts_absent.length]),
					function() {	//ifyes
						if(!frappe.request.ajax_count) {
							frappe.call({
								method: "hkm.bhakta_training.doctype.bhakta_training_attendance_tool.api.mark_attendance",
								freeze: true,
								freeze_message: __("Marking attendance"),
								args: {
									"bkts_present": bkts_present,
									"bkts_absent": bkts_absent,
									"session": frm.doc.session
								},
								callback: function(r) {
									$(me.wrapper.find(".btn-mark-att")).attr("disabled", false);
									//frm.trigger("student_group");
								}
							});
						}
					},
					function() {	//ifno
						$(me.wrapper.find(".btn-mark-att")).attr("disabled", false);
					}
				);
			});

		// make html grid of students
		let bhaktas_html = '';
		for (let bhakta of bhaktas) {
			bhaktas_html += `<div class="col-sm-3">
					<div class="checkbox">
						<label>
							<input
								type="checkbox"
								data-name="${bhakta.name}"
								class="bhaktas-check"
								${bhakta.status==='Present' ? 'checked' : ''}>
							${bhakta.name}
						</label>
					</div>
				</div>`;
		}

		$(`<div class='bhakta-attendance-checks'>${bhaktas_html}</div>`).appendTo(me.wrapper);
	}

	show_empty_state() {
		$(this.wrapper).html(
			`<div class="text-center text-muted" style="line-height: 100px;">
				${__("No Bhaktas in")} ${this.frm.doc.session}
			</div>`
		);
	}
};
