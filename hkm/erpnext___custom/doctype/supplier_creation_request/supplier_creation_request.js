// Copyright (c) 2022, Narahari Dasa and contributors
// For license information, please see license.txt

/**
 * India Compliance Utility Functions Available:
 * 
 * GSTIN Functions:
 * - india_compliance.validate_gstin(gstin, show_msg) - Validates GSTIN format
 * - india_compliance.set_gstin_status(field, doc, force_update) - Sets GSTIN status with description
 * - india_compliance.guess_gst_category(gstin, country) - Guesses GST category from GSTIN
 * - india_compliance.get_gstin_query(party, party_type) - Returns query for GSTIN options
 * - india_compliance.get_gstin_options(party, party_type) - Gets GSTIN options for a party
 * - india_compliance.validate_gst_transporter_id(transporter_id, doc) - Validates transporter ID
 * 
 * GSTIN Info from Portal (Server Method):
 * - frappe.call("india_compliance.gst_india.utils.gstin_info.get_gstin_info", {gstin, doc, throw_error})
 *   Returns: {
 *     business_name: "Company Name",
 *     gst_category: "Registered Regular",
 *     status: "Active",
 *     permanent_address: {
 *       address_line1: "Address Line 1",
 *       address_line2: "Address Line 2",
 *       city: "City Name",
 *       state: "State Name",
 *       pincode: "123456",
 *       country: "India"
 *     },
 *     all_addresses: [array of all addresses with same structure]
 *   }
 * 
 * PAN Functions:
 * - india_compliance.validate_pan(pan) - Validates and formats PAN
 * - india_compliance.set_pan_status(field, force_update) - Sets PAN status with description
 * 
 * State & Location:
 * - india_compliance.set_state_options(frm) - Sets state options for India
 * 
 * HSN Code:
 * - india_compliance.set_hsn_code_query(field) - Sets query filter for HSN codes
 * 
 * Date/Period Functions:
 * - india_compliance.get_month_year_from_period(period) - Returns [month, year] from period
 * - india_compliance.get_period(month_or_quarter, year) - Returns period in MMYYYY format
 * - india_compliance.last_month_name() - Returns last month name
 * - india_compliance.last_month_start() - Returns last month start date
 * - india_compliance.last_month_end() - Returns last month end date
 * 
 * API & Settings:
 * - india_compliance.is_api_enabled(settings) - Check if API is enabled
 * - india_compliance.is_e_invoice_enabled() - Check if e-invoice is enabled
 * - india_compliance.can_enable_api(settings) - Check if API can be enabled
 * 
 * Utility Functions:
 * - india_compliance.get_account_options(company) - Get GST account options
 * - india_compliance.get_party_type(doctype) - Returns Customer or Supplier
 * - india_compliance.validate_invoice_number(invoice_number) - Validates invoice number format
 * - india_compliance.trigger_file_download(file_content, file_name) - Downloads a file
 * 
 * Constants:
 * - india_compliance.MONTH - Array of month names
 * - india_compliance.QUARTER - Array of quarter names
 * - window.gst_settings - Global GST settings object
 */

frappe.ui.form.on("Supplier Creation Request", {
  onload: function (frm) {
    
  },
  refresh: function (frm) {
    if (frm.doc.status == "Pending") {
      frm.add_custom_button(__("Create Supplier"), function () {
        frappe.call({
          method:
            "hkm.erpnext___custom.doctype.supplier_creation_request.supplier_creation_request.quickly_create_supplier",
          args: { request: frm.doc.name },
          callback: function (r) {
            if (r.message) {
              frappe.msgprint(r.message);
            }
            frm.reload_doc();
          },
        });
      });
      frm.add_custom_button(__("Reject"), function () {
        frm.set_value("status", "Rejected");
        frm.save();
      });
    }
    
    // Set PAN status on refresh (only if PAN is 10 characters)
    if (frm.doc.pan && frm.doc.pan.length === 10) {
      const pan_field = frm.get_field('pan');
      if (pan_field) {
        india_compliance.set_pan_status(pan_field);
      }
    }
  },
  gstin: async function (frm) {
    if (frm.doc.gstin) {
      // Validate GSTIN format
      const validated_gstin = india_compliance.validate_gstin(frm.doc.gstin, true);
      
      if (validated_gstin) {
        frm.set_value('gstin', validated_gstin);
        
        // Set GSTIN status with description
        const gstin_field = frm.get_field('gstin');
        india_compliance.set_gstin_status(gstin_field, frm.doc, false);

        // Fetch GSTIN info from GST portal (includes address details)
        if (india_compliance.is_api_enabled() && !gst_settings.sandbox_mode) {
          frappe.show_alert({
            message: __('Fetching details from GST Portal...'),
            indicator: 'blue'
          });

          try {
            const { message: gstin_info } = await frappe.call({
              method: "india_compliance.gst_india.utils.gstin_info.get_gstin_info",
              args: { 
                gstin: validated_gstin,
                doc: {
                  doctype: frm.doc.doctype,
                  name: frm.doc.name
                },
                throw_error: false
              }
            });

            if (gstin_info) {

              if (gstin_info.business_name) {
                frm.set_value('supplier_name', gstin_info.business_name);
              }

              // Set GST category
              if (gstin_info.gst_category) {
                frm.set_value('gst_category', gstin_info.gst_category);
              }

              // Extract and set PAN from GSTIN (characters 3-12)
              // GSTIN format: 22AAAAA0000A1Z5 where AAAAA0000A is the PAN
              const pan = validated_gstin.substring(2, 12);
              if (pan && pan.length === 10) {
                frm.set_value('pan', pan);
                // Set PAN status after setting PAN value
                setTimeout(() => {
                  const pan_field = frm.get_field('pan');
                  if (pan_field) {
                    india_compliance.set_pan_status(pan_field);
                  }
                }, 100);
              }

              // Set address details from permanent address
              if (gstin_info.permanent_address) {
                const addr = gstin_info.permanent_address;
                
                if (addr.address_line1) {
                  frm.set_value('address_line_1', addr.address_line1);
                }
                if (addr.address_line2) {
                  frm.set_value('address_line_2', addr.address_line2);
                }
                if (addr.city) {
                  frm.set_value('city', addr.city);
                }
                if (addr.state) {
                  frm.set_value('state', addr.state);
                }
                if (addr.pincode) {
                  frm.set_value('pincode', addr.pincode);
                }
                if (addr.country) {
                  frm.set_value('country', addr.country);
                }
              }

              frappe.show_alert({
                message: __('Details fetched successfully from GST Portal'),
                indicator: 'green'
              });
            }
          } catch (error) {
            frappe.show_alert({
              message: __('Could not fetch details from GST Portal'),
              indicator: 'orange'
            });
          }
        } else {
          // If API is not enabled, just guess the GST category
          const gst_category = india_compliance.guess_gst_category(
            validated_gstin, 
            frm.doc.country
          );
          if (gst_category) {
            frm.set_value('gst_category', gst_category);
          }
        }
      }
    }
  },
  pan: function (frm) {
    let { pan } = frm.doc;
    // Don't validate if PAN is empty or less than 10 characters (user is still typing)
    if (!pan || pan.length < 10) return;

    // Validate PAN format
    const validated_pan = india_compliance.validate_pan(pan);
    
    if (validated_pan && validated_pan !== pan) {
      frm.set_value('pan', validated_pan);
    }
    
    // Set PAN status with description (only if PAN is 10 characters)
    const pan_field = frm.get_field('pan');
    if (pan_field && pan.length === 10) {
      india_compliance.set_pan_status(pan_field);
    }
  },
});
