// Copyright (c) 2025, Narahari Dasa and contributors
// For license information, please see license.txt

frappe.ui.form.on("HKM Assets Reco", {
	refresh(frm) {
		var asset_category = frm.asset_category;

		frm.set_query("specification", "specification", function (frm, cdt, cdn) {
			const row = locals[cdt][cdn];
			return {
				filters: {
					"asset_category": asset_category
				}
			};
		});



		frm.add_custom_button("QR Barcode Print", function () {
			var barcodeValue = frm.doc.name;
			if (!barcodeValue) {
				frappe.msgprint({ title: __('Error'), message: __('Document name is required to print barcode.'), indicator: 'red' });
				return;
			}

			frappe.ui.form.qz_connect()
				.then(function () {
					return qz.printers.find();
				})
				.then(function (printers) {
					var printer_options = printers.join('\n');
					frappe.prompt([
						{
							fieldname: 'printer_name',
							label: __('Printer Name'),
							fieldtype: 'Select',
							options: printer_options,
							reqd: 1,
							default: printers[0] || 'Godex G500'
						},
						{
							fieldname: 'quantity',
							label: __('Quantity'),
							fieldtype: 'Int',
							reqd: 1,
							default: 1,
							description: __('Number of copies of this barcode to print.')
						}
					], function (values) {
						var qty = values.quantity;
						frappe.confirm(
							__('Print {0} copy/copies of barcode <strong>{1}</strong>?', [qty, barcodeValue]),
							function () {
									frappe.ui.form.qz_connect()
									.then(function () {
										var printer = (values.printer_name || 'Godex G500').trim().replace(/\s+/g, ' ');
										var config = qz.configs.create(printer);
										var print_data = [];
										// Same layout as asset_category.js: prefix + numberPart for display
										var displayPrefix = barcodeValue.replace(/[0-9]/g, '') || barcodeValue;
										var numberPart = barcodeValue.replace(/[^0-9]/g, '');
										numberPart = numberPart ? String(numberPart).padStart(4, '0') : '';

										for (var j = 0; j < qty; j += 2) {
											var group_string = '^XA';
											for (var g = 0; g < 2; g++) {
												if (j + g >= qty) break;
												var xOffset = 20 + g * 310;
												var yOffset = 15;
												group_string += `
      ^FO${xOffset},${yOffset}^BQN,2,6^FDQA,${barcodeValue}^FS
      ^FO${xOffset + 150},${yOffset + 35}^A0N,30,30^FD${displayPrefix}^FS
      ^FO${xOffset + 150},${yOffset + 70}^A0N,30,30^FD${numberPart}^FS`;
											}
											group_string += '^XZ';
											print_data.push(group_string);
										}

										return qz.print(config, print_data);
									})
									.then(function () {
										frappe.ui.form.qz_success();
										frappe.msgprint({
											title: __('Success'),
											message: __('Printed {0} barcode(s): {1}', [qty, barcodeValue]),
											indicator: 'green'
										});
									})
									.catch(function (err) {
										frappe.ui.form.qz_fail(err);
									});
							}
						);
					}, __('QR Barcode Print'));
				})
				.catch(function (err) {
					frappe.msgprint({
						title: __('QZ Tray Connection Error'),
						message: __('Unable to connect to QZ Tray or get printer list. Please ensure QZ Tray is running.<br>Error: {0}', [err.message || err]),
						indicator: 'red'
					});
				});
		}, __("Barcode Printer"));
	},
});
