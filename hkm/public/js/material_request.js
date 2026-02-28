frappe.ui.form.on('Material Request', {
	refresh: function (frm) {
		if (frm.fields_dict["volunteer"]) {
			frm.set_query("volunteer", function () {
				return {
					filters: { enabled: 1 }
				};
			});
		} else {
			console.log("Volunteer field does not exist in this Doctype");
		}

		// Override Purchase Order creation button to carry forward dimensions
		if (frm.doc.docstatus == 1 && frm.doc.status != "Stopped" && frm.doc.material_request_type === "Purchase") {
			let precision = frappe.defaults.get_default("float_precision");
			if (flt(frm.doc.per_ordered, precision) < 100) {
				// Remove existing button and add custom one
				frm.remove_custom_button(__("Purchase Order"), __("Create"));
				frm.add_custom_button(
					__("Purchase Order"),
					() => frm.events.make_purchase_order_custom(frm),
					__("Create")
				);
			}
		}
	},
	make_purchase_order_custom: function (frm) {
		frappe.prompt(
			{
				label: __("For Default Supplier (Optional)"),
				fieldname: "default_supplier",
				fieldtype: "Link",
				options: "Supplier",
				description: __(
					"Select a Supplier from the Default Suppliers of the items below. On selection, a Purchase Order will be made against items belonging to the selected Supplier only."
				),
				get_query: () => {
					return {
						query: "erpnext.stock.doctype.material_request.material_request.get_default_supplier_query",
						filters: { doc: frm.doc.name },
					};
				},
			},
			(values) => {
				frappe.model.open_mapped_doc({
					method: "erpnext.stock.doctype.material_request.material_request.make_purchase_order",
					frm: frm,
					args: { default_supplier: values.default_supplier },
					run_link_triggers: true,
					freeze: true,
					freeze_message: __("Creating Purchase Order..."),
					callback: function(r) {
						if (!r.exc) {
							// Get the newly created Purchase Order doc
							let po_doc = r.docs[0];
							
							// Create a map of material request items with their dimensions
							let mr_items_map = {};
							frm.doc.items.forEach(function(mr_item) {
								mr_items_map[mr_item.name] = {
									cost_center: mr_item.cost_center,
									project: mr_item.project,
									department: mr_item.department,
									expense_account: mr_item.expense_account
								};
							});
							
							// Copy dimensions from Material Request items to Purchase Order items
							if (po_doc.items && po_doc.items.length > 0) {
								po_doc.items.forEach(function(po_item) {
									if (po_item.material_request_item && mr_items_map[po_item.material_request_item]) {
										let mr_dimensions = mr_items_map[po_item.material_request_item];
										
										// Set dimension values
										if (mr_dimensions.cost_center) {
											po_item.cost_center = mr_dimensions.cost_center;
										}
										if (mr_dimensions.project) {
											po_item.project = mr_dimensions.project;
										}
										if (mr_dimensions.department) {
											po_item.department = mr_dimensions.department;
										}
										if (mr_dimensions.expense_account) {
											po_item.expense_account = mr_dimensions.expense_account;
										}
									}
								});
							}
							
							// Navigate to the Purchase Order
							frappe.set_route("Form", po_doc.doctype, po_doc.name);
						}
					}
				});
			},
			__("Enter Supplier"),
			__("Create")
		);
	},
	onload: function (frm) {
		frm.set_query("material_purchase_link", function () {
			return {
				filters: {
					material_request_type: "Purchase",
					for_a_work_order: false,
				}
			}
		});
		if (frm.fields_dict["volunteer"]) {
			frm.set_query("volunteer", function () {
				return {
					filters: { enabled: 1 }
				};
			});
		} else {
			console.log("Volunteer field does not exist in this Doctype");
		}
	},
	transaction_date: function (frm) {
		let transactionDate = new Date(frm.doc.transaction_date);
		transactionDate.setDate(transactionDate.getDate() + 5);
		frappe.model.set_value("Material Request", frm.doc.name, "schedule_date", transactionDate);
	},
	schedule_date: function (frm) {
		for (var i = 0; i < frm.doc.items.length; i++) {
			frappe.model.set_value(
				frm.doc.items[i].doctype,
				frm.doc.items[i].name,
				"schedule_date",
				frm.doc.schedule_date
			);
		}
	},
	company: function (frm) {
		frm.set_query('department', () => {
			return {
				filters: {
					company: frm.doc.company
				}
			};
		});
	},
	for_a_work_order: function (frm) {
		frm.events.filter_service_items(frm);
	},
	filter_service_items: function (frm) {
		frm.set_query("item_code", "items", function (doc, cdt, cdn) {
			return {
				filters: {
					is_stock_item: !doc.for_a_work_order,
					disabled: 0
				}
			};
		});
	},
	on_submit: function (frm) {
		frappe.call({
			method: 'frappe.client.get_list',
			args: {
				'doctype': 'ToDo',
				'filters': { 'reference_name': frm.doc.name, 'status': 'Open' },
				'fields': ['owner']
			},
			callback: function (r) {
				for (var ind in r.message) {
					frm.assign_to.remove(r.message[ind].owner);
				}
			}
		});

	}
});
// frappe.listview_settings['Material Request'] = {
// 	add_fields: ["material_request_type", "status", "per_ordered", "per_received", "transfer_status"],
// 	get_indicator: function(doc) {
// 		if(doc.status=="Stopped") {
// 			return [__("Stopped"), "red", "status,=,Stopped"];
// 		} else if(doc.transfer_status && doc.docstatus != 2) {
// 			if (doc.transfer_status == "Not Started") {
// 				return [__("Not Started"), "orange"];
// 			} else if (doc.transfer_status == "In Transit") {
// 				return [__("In Transit"), "yellow"];
// 			} else if (doc.transfer_status == "Completed") {
// 				return [__("Completed"), "green"];
// 			}
// 		} else if(doc.docstatus==1 && flt(doc.per_ordered, 2) === 0) {
// 			return [__("Pending"), "orange", "per_ordered,=,0"];
// 		} else if(doc.docstatus==1 && flt(doc.per_ordered, 2) < 100 && flt(doc.per_received,2) === 0) {
// 			return [__("Partially ordered"), "yellow", "per_ordered,<,100"];
// 		}  
// 		else if(doc.docstatus==1 && flt(doc.per_ordered, 2) <= 100 && flt(doc.per_received, 2) < 100) {
// 			if (doc.material_request_type == "Purchase" && flt(doc.per_received, 2) < 100 && flt(doc.per_received, 2) > 0) {
// 				return [__("Partially Received"), "yellow", "per_received,<,100"];
// 			} else if (doc.material_request_type == "Purchase" && flt(doc.per_received, 2) == 100) {
// 				return [__("Received"), "green", "per_received,=,100"];
// 			} else if (doc.material_request_type == "Purchase") {
// 				return [__("Ordered"), "green", "per_ordered,=,100"];
// 			} else if (doc.material_request_type == "Material Transfer") {
// 				return [__("Transfered"), "green", "per_ordered,=,100"];
// 			} else if (doc.material_request_type == "Material Issue") {
// 				return [__("Issued"), "green", "per_ordered,=,100"];
// 			} else if (doc.material_request_type == "Customer Provided") {
// 				return [__("Received"), "green", "per_ordered,=,100"];
// 			} else if (doc.material_request_type == "Manufacture") {
// 				return [__("Manufactured"), "green", "per_ordered,=,100"];
// 			}
// 		}

//  }
// };
// frappe.ui.form.on('Material Request Item', {
//     item_code(frm,cdt,cdn){
//         var mr_item = frappe.get_doc(cdt,cdn);
//         if(mr_item.item_code!=null)
//         frappe.db.get_doc('Item', mr_item.item_code)
//             .then(doc => {
//                 console.log(doc.specific_company,frm.doc.company)
//                 if(doc.specific_company!=null && doc.specific_company != frm.doc.company){
//                     msgprint("This item is not of this company");
//                     //frm.refresh_field('unbooked')

//                 }
//             })
//     }
// })


frappe.ui.form.on('Material Request Item', { // The child table is defined in a DoctType called "Dynamic Link"
	item_code(frm, cdt, cdn) { // "links" is the name of the table field in ToDo, "_add" is the event

		let row = frappe.get_doc(cdt, cdn);
		if (row.item_code) {
			frappe.db.get_doc('Item', row.item_code).then(doc => {
				console.log(doc);
				// var child = locals[cdt][cdn];

				if (doc.is_fixed_asset == 1) {
					row.item_type = "Asset";
				}
				else if (doc.is_stock_item == 1) {
					row.item_type = "Stock";
				}
				else {
					row.item_type = "Non-Stock";
				}
				frm.refresh_field("items");
			});
		}
	},

});