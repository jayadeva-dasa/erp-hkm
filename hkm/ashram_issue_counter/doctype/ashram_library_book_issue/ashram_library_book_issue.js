// Copyright (c) 2022, Narahari Dasa and contributors
// For license information, please see license.txt

frappe.ui.form.on('Ashram Library Book Issue', {
	// refresh: function(frm) {

	// }
	validate:function(frm){
		var books = frm.doc.books.map(a => a.book).filter(a=>a);
        var unique_books = books.filter(function(item, pos){
		  return books.indexOf(item)== pos; 
		});
        if(unique_books.length != books.length){
        	frappe.msgprint('Please remove duplicate rows.');
        	frappe.validated = false;
        }
	}
});
