frappe.ui.form.on('Item', {
    onload(frm) {
        frm.events.fetch_item_code(frm);
        frm.set_query("item_group", function () {
            return {
                filters: {
                    is_group: 0,
                }
            }
        });
    },
    // current_rates_update(frm,cur_dialog){
    //         var rate = cur_dialog.fields_dict.rate.value || 0;
    //         frappe.call({
    //             method:'hkm.erpnext___custom.item.get_tax_included_price',
    //             args: {
    //                 'item_code': frm.doc.name,
    //                 'price_list': cur_dialog.fields_dict.pricing_type.value,
    //                 'rate':rate
    //             },
    //             callback:function(r){
    //                 if(!r.exc){
    //                     cur_dialog.set_value("selling_price",r.message['with_tax']);
    //                     cur_dialog.set_value("price_rate",r.message['without_tax']);
    //                 }
    //             }
    //         });
    // },
    // update_rate_selling_price(frm,cur_dialog){
    //     if(cur_dialog.fields_dict.company.value == "" || cur_dialog.fields_dict.pricing_type.value == ""){
    //         frappe.throw("Please select Company & Pricing List");
    //     }else{
    //         var selling_price = parseInt(cur_dialog.fields_dict.selling_price.value);
    //         var rate = parseInt(cur_dialog.fields_dict.rate.value);
    //         var price_rate = (100*selling_price)/(100+rate);
    //         cur_dialog.set_value("price_rate",price_rate);
    //     }
    // },
    // refresh(frm) {

    // 	frm.add_custom_button('Update Price', () => {
    // 	    var current_price = 0;
    // 	    var current_selling_price = 0;
    //         let d = new frappe.ui.Dialog({
    //             title: 'Enter details',
    //             fields: [
    //                 {
    //                     label: 'Company',
    //                     fieldname: 'company',
    //                     fieldtype: 'Link',
    //                     reqd:1,
    //                     options : 'Company',
    //                     default : frappe.defaults.get_user_default("company")
    //                 },
    //                 {
    //                     label: 'Pricing Type',
    //                     fieldname: 'pricing_type',
    //                     fieldtype: 'Link',
    //                     options : 'Price List',
    //                     filters:{'selling':1},
    //                     reqd : 1,
    //                     // default : frappe.defaults.get_user_default("price_list"),
    //                     onchange:function(){
    //                         var val = cur_dialog.fields_dict.pricing_type.value
    //                         if (val != ""){
    //                             var company = cur_dialog.fields_dict.company.value;
    //                             frappe.call({
    //                                 method:'hkm.erpnext___custom.item.get_current_applied_tax_template',
    //                                 args: {
    //                                     'item_code': frm.doc.name,
    //                                     'company': company
    //                                 },
    //                                 callback : function(r) {
    //                                     if (!r.exc) {
    //                                         var tax_temp = "";
    //                                         var rate = 0;
    //                                         if (r.message != null){
    //                                             tax_temp = r.message['template'];
    //                                             rate = r.message['rate'];
    //                                         }
    //                                         cur_dialog.set_value("tax_template",tax_temp);
    //                                         cur_dialog.set_value("rate",rate);
    //                                         frm.events.current_rates_update(frm,cur_dialog);
    //                                     }
    //                                 }
    //                             });
    //                         }
    //                     }
    //                 },
    //                 {
    //                     label: 'Tax Template',
    //                     fieldname: 'tax_template',
    //                     fieldtype: 'Link',
    //                     options:'Item Tax Template',
    //                     onchange:function(){
    //                         var val = cur_dialog.fields_dict.tax_template.value
    //                         if(val != ""){
    //                             console.log(val);
    //                             frappe.db.get_doc("Item Tax Template", val).then(function(res){
    //                                 cur_dialog.set_value("rate",res['cumulative_tax']);
    //                                 frm.events.update_rate_selling_price(frm,cur_dialog);
    //                             });
    //                         }
    //                     },
    //                     get_query: function() {
    //                         console.log(cur_dialog);
    //                         return {filters: {company: cur_dialog.fields_dict.company.value}};
    //                     },
    //                 },
    //                 {
    //                     label: 'Rate',
    //                     fieldname: 'rate',
    //                     fieldtype: 'Int',
    //                     read_only:1
    //                 },
    //                 {
    //                     label: 'Selling Price',
    //                     fieldname: 'selling_price',
    //                     fieldtype: 'Currency',
    //                     onchange:function(){
    //                         frm.events.update_rate_selling_price(frm,cur_dialog);
    //                     },
    //                 },
    //                 {
    //                     label: 'Without Tax Rate',
    //                     fieldname: 'price_rate',
    //                     fieldtype: 'Currency',
    //                     read_only : 1
    //                 },
    //                 // {
    //                 //     label: 'Also update Valuation',
    //                 //     description:'Valuation rate will be 65% of Selling Price',
    //                 //     fieldname: 'valuation_update',
    //                 //     fieldtype: 'Check'
    //                 // }

    //             ],
    //             primary_action_label: 'Submit',
    //             primary_action(values) {
    //                 values.item_code = frm.doc.name;
    //                 frappe.call({
    //                     type: "POST",
    //                     method: 'hkm.erpnext___custom.item_price_update.query',
    //                     args: {
    //                         values: values
    //                     },
    //                     freeze: true,
    //                     callback: (r) => {
    //                         console.log(r.message);
    //                     },
    //                     error: (r) => {
    //                         // on error
    //                     }
    //                 })
    //                 console.log(values);
    //                 d.hide();
    //             }
    //         });
    //         d.show();


    //     })
    // },
    item_group(frm) {
        frm.events.fetch_item_code(frm);
    },
    fetch_item_code(frm) {
        if (frm.doc.item_group != undefined) {
            frappe.call({
                method: 'hkm.erpnext___custom.extend.item.fetch_item_code',
                args: {
                    item_group: frm.doc.item_group
                },
                callback: (r) => {
                    if (!r.exc) {
                        frm.doc.item_code = r.message;
                        refresh_field('item_code');
                    }
                },
            });
        }
    }
})