// import {get_EZPL_string} from "./barcode-printing.js";


frappe.ui.form.on('Purchase Receipt', {

    refresh(frm) {
            frm.add_custom_button(__("Print Labels"), function(){
                frappe.ui.form.qz_connect()
        .then(function () {
            var config = qz.configs.create("Godex G500");            // Exact printer name from OS
            var print_data =[];
            var shift =310;

            var stock_qty ={}
            for(var index in frm.doc.items){
                stock_qty[frm.doc.items[index]['item_code']] = frm.doc.items[index]['qty'];
            }

            let d = new frappe.ui.Dialog({
                            title: 'Select Price List',
                            fields: [
                                {
                                    label: 'Price List',
                                    fieldname: 'price_list',
                                    fieldtype: 'Link',
                                    options:'Price List'
                                }
                            ],
                            primary_action_label: 'Print',
                            primary_action(values) {
                                frappe.call({
                                    method: 'hkm.erpnext___custom.godex_print.filter_sellable_items',
                                    args: {
                                        items: frm.doc.items.filter(a => a['do_not_print_in_barcodes']==false).map(a => a['item_code']),
                                        company:frm.doc.company,
                                        price_list:values.price_list
                                    },
                                    freeze: true,
                                    callback: (r) => {
                                        console.log(r.message);
                                        console.log(stock_qty)
                                        var items_detailed = r.message;
                                        var total_items =[];
                                        for(var index in items_detailed){
                                            var qty = stock_qty[items_detailed[index]['code']];
                                            if(items_detailed[index]['name']!=null){
                                                for(var i=0;i<qty;i++){
                                                    total_items.push({
                                                        "name" : items_detailed[index]['name'],
                                                        "code" : items_detailed[index]['code'],
                                                        "rate" : items_detailed[index]['rate'],
                                                    });
                                                }
                                            }
                                        }
                                        console.log(total_items);
                                        for(var j=0;j<total_items.length;j=j+2){
                                            var group_string="";
                                                for(var g=0;g<2;g++){
                                                    if((j+g)<total_items.length){
                                                        group_string += `\nBA3,`+(4+g*shift)+`,8,1,2,63,0,0,`+total_items[j+g]['code']+
                                                                                `\nAB,`+(4+g*shift)+`,70,1,1,0,0E,`+total_items[j+g]['code']+
                                                                                `\nAA,`+(4+g*shift)+`,104,1,1,0,0E,`+total_items[j+g]['name']+
                                                                                `\nAC,`+(4+g*shift)+`,131,1,1,0,0E,Rs.`+total_items[j+g]['rate']
                                                    }
                                                }
                                                print_data.push(frm.events.get_EZPL_string(frm,group_string));
                                            }
                                        return qz.print(config, print_data)
                                    },
                                    error: (r) => {
                                        // on error
                                    }
                                })
                                d.hide();
                            }
                        });
            
            d.show();

        })
        .then(frappe.ui.form.qz_success)
        .catch(err => {
            frappe.ui.form.qz_fail(err);
        });
        //perform desired action such as routing to new form or fetching etc.
    }, __("Utilities"));
    },
    get_EZPL_string:function(frm,data){
        // Please refer to documentation for seetings : https://www.godexprinters.co.uk/downloads/manuals/desktop/EZPL_EN_J_20180226.pdf
        var settings = `
                        ^Q23,3
                        ^W76
                        ^H10
                        ^P1
                        ^S2
                        ^AD
                        ^C1
                        ^R8
                        ~Q+8
                        ^O0
                        ^D0
                        ^E18
                        ~R255
                        ^L
                        `
        var end = `\nE`
        var str =settings+data+ end
        var arr_data =  str.split("\n");
        var final_data = "";
        for(var index in arr_data){
            final_data +=  arr_data[index].trim() + "\x0D";}
        return final_data;
    }
})
