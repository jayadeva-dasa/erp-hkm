// Copyright (c) 2023, Narahari Dasa and contributors
// For license information, please see license.txt

frappe.ui.form.on('Item Price Update', {
	onload:function(frm){
		if( frm.doc.items == undefined ){
			frm.doc.items = [];
			frm.refresh_field("items");
		}
		
	},

	refresh: function(frm) {
		if(frm.doc.item_group){
			frm.set_query('item', 'items', () => {
				return {
					filters: {
						item_group: frm.doc.item_group
					}
				}
			});
		}
		frm.set_query('tax_template', 'items', () => {
			return {
				filters: {
					company: frm.doc.company
				}
				
			}
		})
	}
});

class PriceUpdate extends erpnext.stock.StockController {
	scan_barcode() {
		const barcode_scanner = new erpnext.utils.BarcodeScanner({frm:this.frm});
		barcode_scanner.process_scan();
	}
}

extend_cscript(cur_frm.cscript, new PriceUpdate({frm: cur_frm}));


frappe.ui.form.on('Item Price Update Detail', { // The child table is defined in a DoctType called "Dynamic Link"
    item_code(frm, cdt, cdn) { // "links" is the name of the table field in ToDo, "_add" is the event
        
        let row = frappe.get_doc(cdt, cdn);
        if(row.item_code){
        	frappe.db.get_doc('Item', row.item_code).then(doc =>{
				row.tax_template = "";
				row.tax_rate = 0;
				row.price_rate = 0;
				row.selling_rate=0;
				// Get Tax Template & Rate | Get Price Rate
				
					frappe.call({
						method:'hkm.erpnext___custom.doctype.item_price_update.item_price_update.get_current_applied_tax_template',
						args: {
							'item_code': doc.name,
							'company': frm.doc.company
						},
						callback : function(r) {
							if (!r.exc) {
								if (r.message != null){
									row.tax_template = r.message['template'];
									row.tax_rate = r.message['rate'];
								}
								frappe.db.get_doc('Item Price', null, { item_code: doc.name, price_list:frm.doc.price_list })
												.then(price_doc => {
													if(price_doc){
														row.price_rate = price_doc.price_list_rate;
														row.selling_rate = row.price_rate + (row.price_rate* row.tax_rate/100)
														frm.refresh_field("items");
													}
												}).catch(err => {
													frm.refresh_field("items");
													console.log(err.statusText);
												} );
								
							}
						}
					});
				
				
	        });
        }
    },
	tax_template(frm, cdt, cdn){
		let row = frappe.get_doc(cdt, cdn);
		if(row.tax_template == ""){
			row.price_rate = row.selling_rate;
			row.tax_rate =0;
			frm.refresh_field("items");
		}
		else{
			frappe.db.get_doc("Item Tax Template",row.tax_template).then(tax_template_doc=>{
				row.tax_rate = tax_template_doc.cumulative_tax;
				row.price_rate = (100*row.selling_rate)/(100+row.tax_rate);
				frm.refresh_field("items");
			});
		}
	},
	selling_rate(frm, cdt, cdn){
		let row = frappe.get_doc(cdt, cdn);
		row.price_rate = (100*row.selling_rate)/(100+row.tax_rate);
		frm.refresh_field("items");
	}
    
});