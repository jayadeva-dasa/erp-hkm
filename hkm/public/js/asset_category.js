frappe.ui.form.on('Asset Category', {
    refresh(frm) {
        // Button 1: Reprint Existing Barcodes
        frm.add_custom_button("Reprint Existing Barcodes", function () {
            // First, get the list of existing assets for this category
            frappe.prompt([
                {
                    fieldname: 'company',
                    label: __('Company'),
                    fieldtype: 'Link',
                    options: 'Company',
                    reqd: 1,
                    default: frappe.defaults.get_user_default('Company'),
                    onchange: function() {
                        var company = this.get_value();
                        var dialog = frappe.ui.form.get_open_dialog();
                        if (company && dialog) {
                            // Get company abbreviation and suggest it
                            frappe.call({
                                method: 'frappe.client.get_value',
                                args: {
                                    doctype: 'Company',
                                    filters: { name: company },
                                    fieldname: 'abbr'
                                },
                                callback: function(r) {
                                    if (r.message && r.message.abbr) {
                                        var suggested_abbr = r.message.abbr.toUpperCase();
                                        // Get category abbreviation
                                        var category_abbr = frm.doc.name.split(' ').map(w => w[0]).join('').toUpperCase();
                                        var full_abbr = suggested_abbr + category_abbr;
                                        
                                        dialog.set_value('abbreviation', full_abbr);
                                    }
                            
                                    // Fetch existing assets count
                                    frappe.call({
                                        method: 'hkm.erpnext___custom.doctype.hkm_assets_reco.hkm_assets_reco.get_existing_assets_count',
                                        args: {
                                            company: company,
                                            asset_category: frm.doc.name
                                        },
                                        callback: function(r2) {
                                            if (r2.message) {
                                                var dialog2 = frappe.ui.form.get_open_dialog();
                                                if (dialog2) {
                                                    dialog2.set_df_property('info_html', 'options', 
                                                        `<div class="alert alert-info">
                                                            <strong>Total Existing Assets: ${r2.message.total_count}</strong><br>
                                                            Range: ${r2.message.first_id} to ${r2.message.last_id}
                                                        </div>`
                                                    );
                                                }
                                            }
                                        }
                                    });
                                }
                            });
                        }
                    }
                },
                {
                    fieldname: 'info_html',
                    label: __(''),
                    fieldtype: 'HTML',
                    options: '<div class="alert alert-warning">Please select a company first</div>'
                },
                {
                    fieldname: 'abbreviation',
                    label: __('Abbreviation Prefix'),
                    fieldtype: 'Data',
                    reqd: 1,
                    description: 'Enter the abbreviation prefix (e.g., HKMFF, HKMV, HKMAC). This must match the prefix of assets you want to reprint.',
                    onchange: function() {
                        var abbr = this.get_value();
                        if (abbr) {
                            var cleaned = abbr.trim().toUpperCase();
                            if (cleaned !== abbr) {
                                this.set_value(cleaned);
                            }
                        }
                    }
                },
                {
                    fieldname: 'from_number',
                    label: __('From Number'),
                    fieldtype: 'Int',
                    reqd: 1,
                    default: 1,
                    description: 'Starting sequence number'
                },
                {
                    fieldname: 'to_number',
                    label: __('To Number'),
                    fieldtype: 'Int',
                    reqd: 1,
                    description: 'Ending sequence number'
                }
            ], function(values) {
                // Validate and clean abbreviation
                var baseLetter = values.abbreviation ? values.abbreviation.trim().toUpperCase() : '';
                
                if (!baseLetter) {
                    frappe.msgprint({
                        title: __('Error'),
                        message: __('Abbreviation prefix is required'),
                        indicator: 'red'
                    });
                    return;
                }
                
                // Validate range
                if (values.to_number < values.from_number) {
                    frappe.msgprint({
                        title: __('Invalid Range'),
                        message: __('To Number must be greater than or equal to From Number'),
                        indicator: 'red'
                    });
                    return;
                }
                
                // Connect to QZ Tray and get printers
                frappe.ui.form.qz_connect()
                    .then(function() {
                        return qz.printers.find();
                    })
                    .then(function(printers) {
                        var printer_options = printers.join('\n');
                        
                        // Prompt for printer selection
                        frappe.prompt([
                            {
                                fieldname: 'printer_name',
                                label: __('Printer Name'),
                                fieldtype: 'Select',
                                options: printer_options,
                                reqd: 1,
                                default: printers[0] || 'Godex G500'
                            }
                        ], function(printer_values) {
                            // Fetch the asset IDs in the range and print
                            frappe.call({
                                method: 'hkm.erpnext___custom.doctype.hkm_assets_reco.hkm_assets_reco.get_assets_in_range',
                                args: {
                                    company: values.company,
                                    asset_category: frm.doc.name,
                                    abbreviation: baseLetter,
                                    from_number: values.from_number,
                                    to_number: values.to_number
                                },
                                callback: function(r) {
                                    if (r.message && r.message.length > 0) {
                                        var asset_ids = r.message;
                                        
                                        // Validate that all asset IDs match the provided abbreviation
                                        var invalid_ids = [];
                                        for (var i = 0; i < asset_ids.length; i++) {
                                            var asset_prefix = asset_ids[i].replace(/[0-9]/g, '');
                                            if (asset_prefix !== baseLetter) {
                                                invalid_ids.push(asset_ids[i]);
                                            }
                                        }
                                        
                                        if (invalid_ids.length > 0) {
                                            frappe.msgprint({
                                                title: __('Mismatch Warning'),
                                                message: __('Some asset IDs do not match the abbreviation prefix {0}. Found: {1}', 
                                                    [baseLetter, invalid_ids.join(', ')]),
                                                indicator: 'orange'
                                            });
                                        }
                                        
                                        // Start printing
                                        frappe.ui.form.qz_connect()
                                            .then(function() {
                                                var printer = printer_values.printer_name || "Godex G500";
                                                printer = printer.trim().replace(/\s+/g, " ");
                                                var config = qz.configs.create(printer);
                                                var print_data = [];
                                                
                                                // Process labels 2 per row
                                                for (var j = 0; j < asset_ids.length; j += 2) {
                                                    var group_string = "^XA";
                                                    
                                                    for (var g = 0; g < 2; g++) {
                                                        if (j + g >= asset_ids.length) {
                                                            break;
                                                        }
                                                        
                                                        var currentId = asset_ids[j + g];
                                                        // Extract prefix and number from asset ID
                                                        var extractedPrefix = currentId.replace(/[0-9]/g, '');
                                                        var numberPart = currentId.replace(/[^0-9]/g, '');
                                                        numberPart = String(numberPart).padStart(4, '0');
                                                        
                                                        // Use the provided abbreviation for display consistency
                                                        var displayPrefix = baseLetter;
                                                        
                                                        var xOffset = 20 + g * 310;
                                                        var yOffset = 15;
                                                        
                                                        group_string += `
      ^FO${xOffset},${yOffset}^BQN,2,6^FDQA,${currentId}^FS
      ^FO${xOffset + 150},${yOffset + 35}^A0N,30,30^FD${displayPrefix}^FS
      ^FO${xOffset + 150},${yOffset + 70}^A0N,30,30^FD${numberPart}^FS`;
                                                    }
                                                    
                                                    group_string += "^XZ";
                                                    print_data.push(group_string);
                                                }
                                                
                                                return qz.print(config, print_data);
                                            })
                                            .then(function() {
                                                frappe.ui.form.qz_success();
                                                frappe.msgprint({
                                                    title: __('Success'),
                                                    message: __('Printed {0} barcodes successfully!', [asset_ids.length]),
                                                    indicator: 'green'
                                                });
                                            })
                                            .catch((err) => {
                                                frappe.ui.form.qz_fail(err);
                                            });
                                    } else {
                                        frappe.msgprint({
                                            title: __('No Assets Found'),
                                            message: __('No assets found in the specified range'),
                                            indicator: 'orange'
                                        });
                                    }
                                }
                            });
                        }, __('Select Printer'));
                    })
                    .catch(function(err) {
                        frappe.msgprint({
                            title: __('QZ Tray Connection Error'),
                            message: __('Unable to connect to QZ Tray. Please ensure QZ Tray is running.<br>Error: {0}', [err.message || err]),
                            indicator: 'red'
                        });
                    });
            }, __('Select Range to Reprint'), __('Print Barcodes'));
            
            // Trigger company onchange to load count
            setTimeout(function() {
                var dialog = frappe.ui.form.get_open_dialog();
                if (dialog) {
                    var company_field = dialog.get_field('company');
                    if (company_field && company_field.get_value()) {
                        company_field.df.onchange.call(company_field);
                    }
                }
            }, 100);
        }, __("Barcode Printer"));
        
        // Button 2: Create New and Print Barcodes
        frm.add_custom_button("QR Barcode Print", async function () {
            // First connect to QZ Tray and get printer list
            frappe.ui.form.qz_connect()
                .then(function() {
                    // Get list of printers from QZ Tray
                    return qz.printers.find();
                })
                .then(function(printers) {
                    // Prepare printer options for Select field
                    var printer_options = printers.join('\n');
                    
                    // Prompt for quantity with populated printer list
                    frappe.prompt([
                        {
                            fieldname: 'company',
                            label: __('Company'),
                            fieldtype: 'Link',
                            options: 'Company',
                            reqd: 1,
                            default: frappe.defaults.get_user_default('Company'),
                            onchange: function() {
                                var company = this.get_value();
                                var dialog = frappe.ui.form.get_open_dialog();
                                if (company && dialog) {
                                    // Get company abbreviation and suggest it
                                    frappe.call({
                                        method: 'frappe.client.get_value',
                                        args: {
                                            doctype: 'Company',
                                            filters: { name: company },
                                            fieldname: 'abbr'
                                        },
                                        callback: function(r) {
                                            if (r.message && r.message.abbr) {
                                                var suggested_abbr = r.message.abbr.toUpperCase();
                                                // Get category abbreviation
                                                var category_abbr = frm.doc.name.split(' ').map(w => w[0]).join('').toUpperCase();
                                                var full_abbr = suggested_abbr + category_abbr;
                                                
                                                dialog.set_value('abbreviation', full_abbr);
                                                dialog.set_df_property('info_html', 'options', 
                                                    `<div class="alert alert-info">
                                                        <strong>Suggested Prefix:</strong> ${full_abbr}<br>
                                                        <small>You can modify this if needed</small>
                                                    </div>`
                                                );
                                            }
                                        }
                                    });
                                }
                            }
                        },
                        {
                            fieldname: 'info_html',
                            label: __(''),
                            fieldtype: 'HTML',
                            options: '<div class="alert alert-warning">Please select a company first</div>'
                        },
                        {
                            fieldname: 'abbreviation',
                            label: __('Abbreviation Prefix'),
                            fieldtype: 'Data',
                            reqd: 1,
                            description: 'Enter the abbreviation prefix (e.g., HKMFF, HKMV, HKMAC). This will be used exactly as entered.',
                            onchange: function() {
                                var abbr = this.get_value();
                                if (abbr) {
                                    var cleaned = abbr.trim().toUpperCase();
                                    if (cleaned !== abbr) {
                                        this.set_value(cleaned);
                                    }
                                }
                            }
                        },
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
                            default: 1
                        }
                    ], function(values) {
                        // Validate and clean abbreviation
                        var baseLetter = values.abbreviation.trim().toUpperCase();
                        
                        if (!baseLetter) {
                            frappe.msgprint({
                                title: __('Error'),
                                message: __('Abbreviation prefix is required'),
                                indicator: 'red'
                            });
                            return;
                        }
                        
                        // Show confirmation with exact abbreviation
                        frappe.confirm(
                            __('You are about to print {0} barcodes with prefix <strong>{1}</strong>.<br><br>The asset IDs will be: {1}0001, {1}0002, etc.<br><br>Continue?', 
                                [values.quantity, baseLetter]),
                            function() {
                                // Call Python method to get the next number sequence
                                frappe.call({
                                    method: 'hkm.erpnext___custom.doctype.hkm_assets_reco.hkm_assets_reco.get_next_sequence_number',
                                    args: {
                                        company: values.company,
                                        asset_category: frm.doc.name,
                                        abbreviation: baseLetter
                                    },
                                    callback: function(r) {
                                        if (r.message) {
                                            var startingNumber = r.message;
                                            var qr_barcode_quantity = values.quantity;
                                            
                                            // Array to store all generated QR IDs
                                            var allQrIds = [];
                                            
                                            // Start QZ Tray printing
                                            frappe.ui.form
                                                .qz_connect()
                                                .then(function () {
                                                    // Use selected printer from dialog
                                                    var printer = values.printer_name || "Godex G500";
                                                    printer = printer.trim().replace(/\s+/g, " ");

                                                    var config = qz.configs.create(printer);
                                                    var print_data = [];
                                                    var qty = qr_barcode_quantity;

                                                    // Process labels 2 per row
                                                    for (var j = 0; j < qty; j += 2) {
                                                        var group_string = "^XA";

                                                        for (var g = 0; g < 2; g++) {
                                                            if (j + g >= qty) {
                                                                break;
                                                            }

                                                            // Calculate current label number (incremental for each label)
                                                            var currentNumber = startingNumber + j + g;
                                                            var numberPart = String(currentNumber).padStart(4, '0'); // e.g., "0001", "0002"
                                                            var currentId = baseLetter + numberPart; // e.g., "HKMV0001", "HKMV0002"
                                                            
                                                            // Store the QR ID
                                                            allQrIds.push(currentId);

                                                            // Calculate position for each label (2 labels per row)
                                                            var xOffset = 20 + g * 310; // 310 is the shift for second label
                                                            var yOffset = 15; // Vertical position

                                                            // Add QR Code and ID text for each label - center aligned
                                                            // ^BQN,2,6 - QR code size 6
                                                            // Text centered to the right of QR code
                                                            group_string += `
      ^FO${xOffset},${yOffset}^BQN,2,6^FDQA,${currentId}^FS
      ^FO${xOffset + 150},${yOffset + 35}^A0N,30,30^FD${baseLetter}^FS
      ^FO${xOffset + 150},${yOffset + 70}^A0N,30,30^FD${numberPart}^FS`;
                                                        }

                                                        group_string += "^XZ";
                                                        print_data.push(group_string);
                                                    }

                                                    return qz.print(config, print_data);
                                                })
                                                .then(function() {
                                                    frappe.ui.form.qz_success();
                                                    
                                                    // After successful printing, create the assets
                                                    frappe.call({
                                                        method: 'hkm.erpnext___custom.doctype.hkm_assets_reco.hkm_assets_reco.create_assets_reco',
                                                        args: {
                                                            company: values.company,
                                                            asset_category: frm.doc.name,
                                                            qr_ids: allQrIds
                                                        },
                                                        callback: function(res) {
                                                            if (res.message && res.message.success) {
                                                                frappe.msgprint({
                                                                    title: __('Success'),
                                                                    message: __('Printed and created {0} assets with prefix {1}!<br>IDs: {2} to {3}', 
                                                                        [res.message.created_count, baseLetter, allQrIds[0], allQrIds[allQrIds.length - 1]]),
                                                                    indicator: 'green'
                                                                });
                                                            } else {
                                                                frappe.msgprint({
                                                                    title: __('Partial Success'),
                                                                    message: __('Barcodes printed but some assets may not have been created. Check error log.'),
                                                                    indicator: 'orange'
                                                                });
                                                            }
                                                        }
                                                    });
                                                })
                                                .catch((err) => {
                                                    frappe.ui.form.qz_fail(err);
                                                });
                                        }
                                    }
                                });
                            }
                        );
                    }, __('QR Barcode Print Details'));
                    
                    // Trigger company onchange to load suggestion
                    setTimeout(function() {
                        var dialog = frappe.ui.form.get_open_dialog();
                        if (dialog) {
                            var company_field = dialog.get_field('company');
                            if (company_field && company_field.get_value()) {
                                company_field.df.onchange.call(company_field);
                            }
                        }
                    }, 100);
                })
                .catch(function(err) {
                    frappe.msgprint({
                        title: __('QZ Tray Connection Error'),
                        message: __('Unable to connect to QZ Tray or get printer list. Please ensure QZ Tray is running.<br>Error: {0}', [err.message || err]),
                        indicator: 'red'
                    });
                });
        }, __("Barcode Printer"));
    }
});