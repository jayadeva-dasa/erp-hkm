frappe.ready(function() {
	// bind events here
	frappe.web_form.validate = () => {
		let data = frappe.web_form.get_values();
		console.log(data);
		// if (data.amount < 1000) {
		// 	frappe.msgprint('Value must be more than 1000');
		// 	return false;
		// }
	};
})

